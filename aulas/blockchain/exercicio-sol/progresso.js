#!/usr/bin/env node
// Seu painel de progresso. Rode:  node progresso.js
//
// Mostra, exercicio a exercicio: se voce ligou em config.js ([VOCE]) ou ainda
// usa o gabarito ([gabarito]), e quantos testes daquele exercicio passam.

const { execFileSync } = require("child_process");
const config = require("./config");

const PARTS = [
  ["cofre",        "1 · Cofre (payable, saque do dono)",   "test/cofre.test.js"],
  ["votacao",      "2 · Votacao (prazo, 1 voto)",          "test/votacao.test.js"],
  ["crowdfunding", "3 · Crowdfunding (meta, refund)",      "test/crowdfunding.test.js"],
  ["leilao",       "4 · Leilao ingles (pull payments)",    "test/leilao.test.js"],
  ["moeda",        "5 · Moeda ERC-20",                     "test/moeda.test.js"],
  ["dvp",          "6 · DvP (entrega contra pagamento)",   "test/dvp.test.js"],
];

function run(file) {
  let out;
  try {
    out = execFileSync("npx", ["hardhat", "test", file], { encoding: "utf8" });
  } catch (e) {
    out = (e.stdout || "") + (e.stderr || "");
  }
  const passed = Number((out.match(/(\d+) passing/) || [0, 0])[1]);
  const failed = Number((out.match(/(\d+) failing/) || [0, 0])[1]);
  return [passed, passed + failed];
}

function main() {
  process.stdout.write("\n  exercicio-sol — seu progresso\n");
  process.stdout.write("  " + "─".repeat(52) + "\n");
  let done = 0;
  for (const [key, title, file] of PARTS) {
    const isMine = config[key];
    const [passed, total] = run(file);
    const tag = isMine ? "[VOCE]    " : "[gabarito]";
    const mark = total && passed === total ? "✓" : "✗";
    if (isMine && total && passed === total) done++;
    process.stdout.write(`  ${title.padEnd(38)} ${tag}  ${passed}/${total} ${mark}\n`);
  }
  process.stdout.write("  " + "─".repeat(52) + "\n");
  process.stdout.write(
    `  Exercicios seus concluidos: ${done}/${PARTS.length}` +
    "   (ligue cada um em config.js ao terminar)\n\n"
  );
}

main();
