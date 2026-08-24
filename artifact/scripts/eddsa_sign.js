// Produce EdDSA-Poseidon signatures matching AttributedMeanFusion's checks.
// Input : {"vpos":[...], "m":4, "k":3}
// Output: {"Ax":[..m],"Ay":[..m],"S":[..n],"R8x":[..n],"R8y":[..n]}
const circomlibjs = require("circomlibjs");
let input = "";
process.stdin.on("data", d => (input += d));
process.stdin.on("end", async () => {
  const eddsa = await circomlibjs.buildEddsa();
  const poseidon = await circomlibjs.buildPoseidon();
  const F = poseidon.F;
  const { vpos, m, k } = JSON.parse(input);
  const prv = [], Ax = [], Ay = [];
  for (let d = 0; d < m; d++) {
    const key = Buffer.alloc(32, 0);
    key.writeUInt32BE(d + 1, 28);
    prv.push(key);
    const pub = eddsa.prv2pub(key);
    Ax.push(F.toString(pub[0]));
    Ay.push(F.toString(pub[1]));
  }
  const S = [], R8x = [], R8y = [];
  vpos.forEach((v, i) => {
    const dev = Math.floor(i / k), seq = (i % k) + 1;
    const label = BigInt((dev + 1) * 65536 + seq);
    const msg = poseidon([F.e(label), F.e(BigInt(v))]);
    const sig = eddsa.signPoseidon(prv[dev], msg);
    S.push(sig.S.toString());
    R8x.push(F.toString(sig.R8[0]));
    R8y.push(F.toString(sig.R8[1]));
  });
  process.stdout.write(JSON.stringify({ Ax, Ay, S, R8x, R8y }));
});
