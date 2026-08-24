pragma circom 2.1.6;

include "circomlib/circuits/poseidon.circom";
include "circomlib/circuits/bitify.circom";
include "circomlib/circuits/comparators.circom";
include "circomlib/circuits/eddsaposeidon.circom";

// Observations travel as vpos = centi-degrees Celsius + 32768, so every signal
// the circuit range-checks is non-negative.

// Poseidon chain over the policy-ordered values.  The position of a value in
// the chain carries its record identifier, so completeness relative to P is
// enforced by the shape of the circuit rather than by additional constraints:
// a witness with a missing or reordered record produces a different cM.
template Binding(n) {
    signal input v[n];
    signal output cM;
    component h[n];
    signal acc[n + 1];
    acc[0] <== 0;
    for (var i = 0; i < n; i++) {
        h[i] = Poseidon(2);
        h[i].inputs[0] <== acc[i];
        h[i].inputs[1] <== v[i];
        acc[i + 1] <== h[i].out;
    }
    cM <== acc[n];
}
