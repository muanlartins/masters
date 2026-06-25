const { expect } = require("chai");
const { ethers } = require("hardhat");
const { sol } = require("../kit");

describe("Exercicio 1 · Cofre (payable, saque do dono)", function () {
  let cofre, dono, alice, bob;

  beforeEach(async function () {
    [dono, alice, bob] = await ethers.getSigners();
    const Cofre = await ethers.getContractFactory(sol("cofre", "Cofre"));
    cofre = await Cofre.deploy();
  });

  it("registra o dono como quem fez o deploy", async function () {
    expect(await cofre.dono()).to.equal(dono.address);
  });

  it("deposito aumenta o saldo do cofre e registra por endereco", async function () {
    await cofre.connect(alice).depositar({ value: ethers.parseEther("1") });
    expect(await cofre.saldo()).to.equal(ethers.parseEther("1"));
    expect(await cofre.depositado(alice.address)).to.equal(ethers.parseEther("1"));
  });

  it("deposito de 0 reverte", async function () {
    await expect(
      cofre.connect(alice).depositar({ value: 0 })
    ).to.be.revertedWith("envie algum valor");
  });

  it("nao-dono nao consegue sacar", async function () {
    await cofre.connect(alice).depositar({ value: ethers.parseEther("1") });
    await expect(
      cofre.connect(alice).sacar(alice.address, ethers.parseEther("1"))
    ).to.be.revertedWith("somente o dono");
  });

  it("dono saca e o destinatario recebe o ETH", async function () {
    await cofre.connect(alice).depositar({ value: ethers.parseEther("2") });
    await expect(
      cofre.connect(dono).sacar(bob.address, ethers.parseEther("2"))
    ).to.changeEtherBalance(bob, ethers.parseEther("2"));
    expect(await cofre.saldo()).to.equal(0);
  });

  it("sacar mais que o saldo reverte", async function () {
    await cofre.connect(alice).depositar({ value: ethers.parseEther("1") });
    await expect(
      cofre.connect(dono).sacar(bob.address, ethers.parseEther("2"))
    ).to.be.revertedWith("saldo insuficiente");
  });
});
