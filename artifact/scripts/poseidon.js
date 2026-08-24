// Batch Poseidon over BN254, matching circomlib's implementation exactly.
const circomlibjs = require("circomlibjs");
let input = "";
process.stdin.on("data", d => (input += d));
process.stdin.on("end", async () => {
  const poseidon = await circomlibjs.buildPoseidon();
  const F = poseidon.F;
  const batches = JSON.parse(input);
  const out = batches.map(b => F.toString(poseidon(b.map(x => BigInt(x)))));
  process.stdout.write(JSON.stringify(out));
});
