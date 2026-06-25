const { expect } = require("chai");
const { ethers } = require("hardhat");
const { time } = require("@nomicfoundation/hardhat-network-helpers");
const { sol } = require("../kit");

describe("Exercicio 2 · Votacao (prazo, 1 voto por endereco)", function () {
  const DURACAO = 3600;
  let votacao, admin, a, b, c;

  beforeEach(async function () {
    [admin, a, b, c] = await ethers.getSigners();
    const Votacao = await ethers.getContractFactory(sol("votacao", "Votacao"));
    votacao = await Votacao.deploy(["Alice", "Bob"], DURACAO);
  });

  it("guarda os candidatos do construtor", async function () {
    expect(await votacao.totalCandidatos()).to.equal(2);
    expect(await votacao.candidatos(0)).to.equal("Alice");
  });

  it("um voto incrementa a contagem do candidato", async function () {
    await votacao.connect(a).votar(1);
    expect(await votacao.votos(1)).to.equal(1);
  });

  it("o mesmo endereco nao vota duas vezes", async function () {
    await votacao.connect(a).votar(0);
    await expect(votacao.connect(a).votar(1)).to.be.revertedWith("ja votou");
  });

  it("votar em candidato inexistente reverte", async function () {
    await expect(votacao.connect(a).votar(9)).to.be.revertedWith("candidato invalido");
  });

  it("nao da pra votar depois do prazo", async function () {
    await time.increase(DURACAO + 1);
    await expect(votacao.connect(a).votar(0)).to.be.revertedWith("votacao encerrada");
  });

  it("vencedor so apura depois do prazo", async function () {
    await expect(votacao.vencedor()).to.be.revertedWith("votacao em andamento");
  });

  it("vencedor e o candidato mais votado", async function () {
    await votacao.connect(a).votar(1);
    await votacao.connect(b).votar(1);
    await votacao.connect(c).votar(0);
    await time.increase(DURACAO + 1);
    expect(await votacao.vencedor()).to.equal(1);
  });
});
