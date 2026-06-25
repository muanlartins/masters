const { expect } = require("chai");
const { ethers } = require("hardhat");
const { time } = require("@nomicfoundation/hardhat-network-helpers");
const { sol } = require("../kit");

describe("Exercicio 4 · Leilao ingles (lances, pull payments)", function () {
  const DURACAO = 3600;
  let leilao, dono, a, b, c;

  beforeEach(async function () {
    [dono, a, b, c] = await ethers.getSigners();
    const Leilao = await ethers.getContractFactory(sol("leilao", "Leilao"));
    leilao = await Leilao.deploy(DURACAO);
  });

  it("o primeiro lance vira o maior", async function () {
    await leilao.connect(a).darLance({ value: ethers.parseEther("1") });
    expect(await leilao.maiorComprador()).to.equal(a.address);
    expect(await leilao.maiorLance()).to.equal(ethers.parseEther("1"));
  });

  it("lance menor ou igual ao maior reverte", async function () {
    await leilao.connect(a).darLance({ value: ethers.parseEther("2") });
    await expect(
      leilao.connect(b).darLance({ value: ethers.parseEther("2") })
    ).to.be.revertedWith("lance baixo");
  });

  it("lance maior atualiza e credita o anterior", async function () {
    await leilao.connect(a).darLance({ value: ethers.parseEther("1") });
    await leilao.connect(b).darLance({ value: ethers.parseEther("2") });
    expect(await leilao.maiorComprador()).to.equal(b.address);
    expect(await leilao.aDevolver(a.address)).to.equal(ethers.parseEther("1"));
  });

  it("retirar devolve o lance superado e zera o credito", async function () {
    await leilao.connect(a).darLance({ value: ethers.parseEther("1") });
    await leilao.connect(b).darLance({ value: ethers.parseEther("2") });
    await expect(leilao.connect(a).retirar()).to.changeEtherBalance(a, ethers.parseEther("1"));
    expect(await leilao.aDevolver(a.address)).to.equal(0);
  });

  it("nao da pra dar lance depois do fim", async function () {
    await time.increase(DURACAO + 1);
    await expect(
      leilao.connect(a).darLance({ value: ethers.parseEther("1") })
    ).to.be.revertedWith("leilao encerrado");
  });

  it("encerrar antes do fim reverte", async function () {
    await expect(leilao.connect(c).encerrar()).to.be.revertedWith("ainda em andamento");
  });

  it("encerrar paga o maior lance ao beneficiario", async function () {
    await leilao.connect(a).darLance({ value: ethers.parseEther("1") });
    await leilao.connect(b).darLance({ value: ethers.parseEther("3") });
    await time.increase(DURACAO + 1);
    // 'c' encerra (qualquer um pode), entao o beneficiario nao paga gas aqui
    await expect(leilao.connect(c).encerrar()).to.changeEtherBalance(dono, ethers.parseEther("3"));
  });
});
