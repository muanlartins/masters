pragma circom 2.1.6;

include "binding.circom";

// ---------------------------------------------------------------- mean ----
// The judge recovers the arithmetic mean from the certified sum; the affine
// step from centi-Celsius to kelvin needs no constraints.
template MeanFusion(n) {
    signal input v[n];
    signal output cM;
    signal output sumv;
    component b = Binding(n);
    component rc[n];
    var s = 0;
    for (var i = 0; i < n; i++) {
        rc[i] = Num2Bits(16);
        rc[i].in <== v[i];
        b.v[i] <== v[i];
        s += v[i];
    }
    sumv <== s;
    cM <== b.cM;
}

// ----------------------------------------------------------- excursion ----
template ExcursionFusion(n, thrpos) {
    signal input v[n];
    signal output cM;
    signal output count;
    component b = Binding(n);
    component rc[n];
    component gt[n];
    var c = 0;
    for (var i = 0; i < n; i++) {
        rc[i] = Num2Bits(16);
        rc[i].in <== v[i];
        b.v[i] <== v[i];
        gt[i] = GreaterThan(17);
        gt[i].in[0] <== v[i];
        gt[i].in[1] <== thrpos;
        c += gt[i].out;
    }
    count <== c;
    cM <== b.cM;
}

// ----------------------------------------------------------------- MKT ----
// Mean kinetic temperature (USP <1079.2>) in shifted form. With Tc the reading
// in centi-kelvin and SC the fixed-point scale:
//     x_i    = 1e6 / Tc_i
//     u_i    = x_ref - x_i                      (|u| <= 1.7 over 2..30 C)
//     T_MKT  = 1e6 * SC / (XREF - L),   L = SC * ln( mean_i exp(u_i) )
// exp is a degree-D truncated series.  Carrying the common denominator
// D! * SC^D keeps every intermediate integral, so the whole circuit needs one
// division for the logarithm and one for the final reciprocal, not one per
// record.
template MktFusion(n, SC, XREF, D, RBITS, TLOPOS, THIPOS, UMIN, UMAX) {
    signal input v[n];          // vpos
    signal input X[n];          // floor(SC * 1e6 / Tc_i)
    signal input Xrem[n];       // its remainder
    signal input L;             // SC * ln(mean exp), may be negative
    signal input Lrem;
    signal input TcMkt;         // result, centi-kelvin
    signal input Trem;
    signal output cM;
    signal output out;

    var TCOFF = 32768 - 27315;  // vpos -> centi-kelvin
    var SC1E6 = SC * 1000000;

    // D!/j! and SC^(D-j), evaluated at compile time.
    var cf[D + 1];
    cf[D] = 1;
    for (var j = D - 1; j >= 0; j--) { cf[j] = cf[j + 1] * (j + 1); }
    var scp[D + 1];
    scp[D] = 1;
    for (var j = D - 1; j >= 0; j--) { scp[j] = scp[j + 1] * SC; }

    component b = Binding(n);
    component rc[n];
    component vlo[n];
    component vhi[n];
    component xrc[n];
    component xlt[n];
    signal Tc[n];
    signal U[n];
    signal pw[n][D + 1];
    var SNUM = 0;

    for (var i = 0; i < n; i++) {
        rc[i] = Num2Bits(16);
        rc[i].in <== v[i];
        vlo[i] = LessEqThan(17);
        vlo[i].in[0] <== TLOPOS;
        vlo[i].in[1] <== v[i];
        vlo[i].out === 1;
        vhi[i] = LessEqThan(17);
        vhi[i].in[0] <== v[i];
        vhi[i].in[1] <== THIPOS;
        vhi[i].out === 1;
        b.v[i] <== v[i];
        Tc[i] <== v[i] - TCOFF;

        // X[i] = floor(SC*1e6 / Tc[i]), pinned by 0 <= Xrem[i] < Tc[i].
        X[i] * Tc[i] + Xrem[i] === SC1E6;
        xrc[i] = Num2Bits(16);
        xrc[i].in <== Xrem[i];
        xlt[i] = LessThan(17);
        xlt[i].in[0] <== Xrem[i];
        xlt[i].in[1] <== Tc[i];
        xlt[i].out === 1;

        U[i] <== XREF - X[i];
        pw[i][0] <== 1;
        var Ni = cf[0] * scp[0];
        for (var j = 1; j <= D; j++) {
            pw[i][j] <== pw[i][j - 1] * U[i];
            Ni += cf[j] * scp[j] * pw[i][j];
        }
        SNUM += Ni;
    }

    // L is the fixed-point logarithm of the mean, checked through the same
    // series: n * N(L) + Lrem == sum_i N(u_i), with Lrem bounded.
    signal Lshift;
    Lshift <== L - UMIN;
    component lrange = Num2Bits(19);
    lrange.in <== Lshift;
    component lmax = LessEqThan(19);
    lmax.in[0] <== Lshift;
    lmax.in[1] <== UMAX - UMIN;
    lmax.out === 1;
    signal lpw[D + 1];
    signal lnextpw[D + 1];
    lpw[0] <== 1;
    lnextpw[0] <== 1;
    var NL = cf[0] * scp[0];
    var NLnext = cf[0] * scp[0];
    for (var j = 1; j <= D; j++) {
        lpw[j] <== lpw[j - 1] * L;
        lnextpw[j] <== lnextpw[j - 1] * (L + 1);
        NL += cf[j] * scp[j] * lpw[j];
        NLnext += cf[j] * scp[j] * lnextpw[j];
    }
    component lrem = Num2Bits(RBITS);
    lrem.in <== Lrem;
    n * NL + Lrem === SNUM;
    // Pin L to the greatest fixed-point integer whose polynomial value does
    // not exceed the mean. Without this upper remainder bound, many L values
    // and therefore many incorrect outputs satisfy the equality above.
    signal Lstep;
    Lstep <== n * (NLnext - NL);
    component lstepRange = Num2Bits(RBITS);
    lstepRange.in <== Lstep;
    component lunique = LessThan(RBITS);
    lunique.in[0] <== Lrem;
    lunique.in[1] <== Lstep;
    lunique.out === 1;

    // T_MKT = 1e6 * SC / (XREF - L), pinned by 0 <= Trem < XREF - L.
    signal W;
    W <== XREF - L;
    TcMkt * W + Trem === SC1E6;
    component trc = Num2Bits(22);
    trc.in <== Trem;
    component tlt = LessThan(23);
    tlt.in[0] <== Trem;
    tlt.in[1] <== W;
    tlt.out === 1;

    out <== TcMkt;
    cM <== b.cM;
}

// ------------------------------------------------ attribution in-circuit ----
// Verifying each device signature *inside* the proof is what makes a V4
// evidence object constant-size: nothing per record has to reach the judge.
// The roster is committed so the judge can check it against the policy.
template AttributedMeanFusion(n, m, k) {
    signal input v[n];
    signal input Ax[m];
    signal input Ay[m];
    signal input S[n];
    signal input R8x[n];
    signal input R8y[n];
    signal output cM;
    signal output sumv;
    signal output roster;

    component b = Binding(n);
    component rc[n];
    component msg[n];
    component sig[n];
    var s = 0;
    for (var i = 0; i < n; i++) {
        rc[i] = Num2Bits(16);
        rc[i].in <== v[i];
        b.v[i] <== v[i];
        s += v[i];
        // The signed message names the record identifier, which position fixes.
        msg[i] = Poseidon(2);
        msg[i].inputs[0] <== (i \ k + 1) * 65536 + (i % k + 1);
        msg[i].inputs[1] <== v[i];
        sig[i] = EdDSAPoseidonVerifier();
        sig[i].enabled <== 1;
        sig[i].Ax <== Ax[i \ k];
        sig[i].Ay <== Ay[i \ k];
        sig[i].S <== S[i];
        sig[i].R8x <== R8x[i];
        sig[i].R8y <== R8y[i];
        sig[i].M <== msg[i].out;
    }
    component rost = Poseidon(2 * m);
    for (var d = 0; d < m; d++) {
        rost.inputs[d] <== Ax[d];
        rost.inputs[m + d] <== Ay[d];
    }
    roster <== rost.out;
    sumv <== s;
    cM <== b.cM;
}
