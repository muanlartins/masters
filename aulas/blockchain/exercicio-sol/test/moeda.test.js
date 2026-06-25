const { expect } = require("chai");
const { ethers } = require("hardhat");
const { sol } = require("../kit");

describe("Exercicio 5 · Moeda ERC-20", function () {
  const SUPPLY = ethers.parseEther("1000");
  let moeda, dono, a, b;

  beforeEach(async function () {
    [dono, a, b] = await ethers.getSigners();
    const Moeda = await ethers.getContractFactory(sol("moeda", "Moeda"));
    moeda = await Moeda.deploy(SUPPLY);
  });

  it("o deploy cria todo o supply na conta do criador", async function () {
    expect(await moeda.totalSupply()).to.equal(SUPPLY);
    expect(await moeda.balanceOf(dono.address)).to.equal(SUPPLY);
  });

  it("transfer move o saldo e emite Transfer", async function () {
    const v = ethers.parseEther("100");
    await expect(moeda.connect(dono).transfer(a.address, v))
      .to.emit(moeda, "Transfer")
      .withArgs(dono.address, a.address, v);
    expect(await moeda.balanceOf(a.address)).to.equal(v);
    expect(await moeda.balanceOf(dono.address)).to.equal(SUPPLY - v);
  });

  it("transfer sem saldo reverte", async function () {
    await expect(
      moeda.connect(a).transfer(b.address, ethers.parseEther("1"))
    ).to.be.revertedWith("saldo insuficiente");
  });

  it("approve seta a allowance e emite Approval", async function () {
    const v = ethers.parseEther("50");
    await expect(moeda.connect(dono).approve(a.address, v))
      .to.emit(moeda, "Approval")
      .withArgs(dono.address, a.address, v);
    expect(await moeda.allowance(dono.address, a.address)).to.equal(v);
  });

  it("transferFrom respeita e debita a allowance", async function () {
    await moeda.connect(dono).approve(a.address, ethers.parseEther("100"));
    await moeda.connect(a).transferFrom(dono.address, b.address, ethers.parseEther("60"));
    expect(await moeda.balanceOf(b.address)).to.equal(ethers.parseEther("60"));
    expect(await moeda.allowance(dono.address, a.address)).to.equal(ethers.parseEther("40"));
  });

  it("transferFrom sem allowance reverte", async function () {
    await expect(
      moeda.connect(a).transferFrom(dono.address, b.address, ethers.parseEther("1"))
    ).to.be.revertedWith("allowance insuficiente");
  });
});
