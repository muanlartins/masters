const { expect } = require("chai");
const { ethers } = require("hardhat");
const { sol } = require("../kit");

describe("Exercicio 6 · DvP (entrega contra pagamento, atomico)", function () {
  const QTD = ethers.parseEther("100"); // tokens entregues
  const PRECO = ethers.parseEther("1"); // ETH pago (wei)
  let dvp, token, vendedor, comprador, estranho;

  beforeEach(async function () {
    [vendedor, comprador, estranho] = await ethers.getSigners();
    // o token nasce todo na mao do vendedor (e o ativo a ser entregue)
    const TestToken = await ethers.getContractFactory("TestToken");
    token = await TestToken.connect(vendedor).deploy(ethers.parseEther("1000"));
    const DvP = await ethers.getContractFactory(sol("dvp", "DvP"));
    dvp = await DvP.deploy(token.target, vendedor.address, comprador.address, QTD, PRECO);
  });

  it("liquidacao atomica: comprador recebe o token e vendedor recebe o ETH", async function () {
    await token.connect(vendedor).approve(dvp.target, QTD);
    await expect(
      dvp.connect(comprador).liquidar({ value: PRECO })
    ).to.changeEtherBalance(vendedor, PRECO);
    expect(await token.balanceOf(comprador.address)).to.equal(QTD);
    expect(await dvp.liquidado()).to.equal(true);
  });

  it("sem o approve do vendedor, NADA se move (atomicidade)", async function () {
    // o vendedor NAO aprovou -> a entrega falha -> a tx inteira reverte
    await expect(dvp.connect(comprador).liquidar({ value: PRECO })).to.be.reverted;
    expect(await token.balanceOf(comprador.address)).to.equal(0);
    expect(await dvp.liquidado()).to.equal(false);
    expect(await ethers.provider.getBalance(dvp.target)).to.equal(0); // ETH nao ficou preso
  });

  it("pagamento diferente do preco reverte", async function () {
    await token.connect(vendedor).approve(dvp.target, QTD);
    await expect(
      dvp.connect(comprador).liquidar({ value: ethers.parseEther("0.5") })
    ).to.be.revertedWith("pagamento incorreto");
  });

  it("so o comprador pode liquidar", async function () {
    await token.connect(vendedor).approve(dvp.target, QTD);
    await expect(
      dvp.connect(estranho).liquidar({ value: PRECO })
    ).to.be.revertedWith("somente o comprador");
  });

  it("nao da pra liquidar duas vezes", async function () {
    await token.connect(vendedor).approve(dvp.target, QTD);
    await dvp.connect(comprador).liquidar({ value: PRECO });
    await expect(
      dvp.connect(comprador).liquidar({ value: PRECO })
    ).to.be.revertedWith("ja liquidado");
  });

  it("cancelar (por qualquer parte) trava a liquidacao", async function () {
    await dvp.connect(vendedor).cancelar();
    await token.connect(vendedor).approve(dvp.target, QTD);
    await expect(
      dvp.connect(comprador).liquidar({ value: PRECO })
    ).to.be.revertedWith("cancelado");
  });
});
