const { expect } = require("chai");
const { ethers } = require("hardhat");
const { time } = require("@nomicfoundation/hardhat-network-helpers");
const { sol } = require("../kit");

describe("Exercicio 3 · Crowdfunding (meta, prazo, reembolso)", function () {
  const DURACAO = 3600;
  const META = ethers.parseEther("10");
  let cf, dono, a, b;

  beforeEach(async function () {
    [dono, a, b] = await ethers.getSigners();
    const CF = await ethers.getContractFactory(sol("crowdfunding", "Crowdfunding"));
    cf = await CF.deploy(META, DURACAO);
  });

  it("contribuir registra por endereco e soma o total", async function () {
    await cf.connect(a).contribuir({ value: ethers.parseEther("3") });
    await cf.connect(b).contribuir({ value: ethers.parseEther("4") });
    expect(await cf.contribuido(a.address)).to.equal(ethers.parseEther("3"));
    expect(await cf.total()).to.equal(ethers.parseEther("7"));
  });

  it("contribuir depois do prazo reverte", async function () {
    await time.increase(DURACAO + 1);
    await expect(
      cf.connect(a).contribuir({ value: ethers.parseEther("1") })
    ).to.be.revertedWith("campanha encerrada");
  });

  it("meta atingida: o beneficiario saca tudo", async function () {
    await cf.connect(a).contribuir({ value: ethers.parseEther("6") });
    await cf.connect(b).contribuir({ value: ethers.parseEther("5") });
    await time.increase(DURACAO + 1);
    await expect(cf.connect(dono).sacar()).to.changeEtherBalance(dono, ethers.parseEther("11"));
  });

  it("nao-beneficiario nao saca", async function () {
    await cf.connect(a).contribuir({ value: ethers.parseEther("11") });
    await time.increase(DURACAO + 1);
    await expect(cf.connect(a).sacar()).to.be.revertedWith("somente o beneficiario");
  });

  it("sacar antes do prazo reverte mesmo com a meta batida", async function () {
    await cf.connect(a).contribuir({ value: ethers.parseEther("11") });
    await expect(cf.connect(dono).sacar()).to.be.revertedWith("ainda em andamento");
  });

  it("meta nao atingida: o contribuinte pega o seu de volta", async function () {
    await cf.connect(a).contribuir({ value: ethers.parseEther("2") });
    await time.increase(DURACAO + 1);
    await expect(cf.connect(a).reembolsar()).to.changeEtherBalance(a, ethers.parseEther("2"));
    expect(await cf.contribuido(a.address)).to.equal(0);
  });

  it("reembolsar com a meta atingida reverte", async function () {
    await cf.connect(a).contribuir({ value: ethers.parseEther("11") });
    await time.increase(DURACAO + 1);
    await expect(cf.connect(a).reembolsar()).to.be.revertedWith("meta atingida");
  });
});
