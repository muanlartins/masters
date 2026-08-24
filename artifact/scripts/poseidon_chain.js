// Poseidon chain acc_{i+1} = Poseidon(acc_i, v_i), matching Binding(n).
const circomlibjs = require("circomlibjs");
let input = "";
process.stdin.on("data", d => (input += d));
process.stdin.on("end", async () => {
  const poseidon = await circomlibjs.buildPoseidon();
  const F = poseidon.F;
  const vals = JSON.parse(input);
  let acc = F.e(0);
  for (const v of vals) acc = poseidon([acc, F.e(BigInt(v))]);
  process.stdout.write(F.toString(acc));
});
