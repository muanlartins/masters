// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// Leilao ingles: lances crescentes; o superado fica com um saldo a sacar
/// (pull payment); no fim, o beneficiario recebe o maior lance. (REFERENCIA)
contract Leilao {
    address public beneficiario;
    uint public fim; // timestamp de encerramento
    address public maiorComprador;
    uint public maiorLance;
    bool public encerrado;
    mapping(address => uint) public aDevolver; // pull payments

    constructor(uint duracaoSegundos) {
        beneficiario = msg.sender;
        fim = block.timestamp + duracaoSegundos;
    }

    function darLance() external payable {
        require(block.timestamp < fim, "leilao encerrado");
        require(msg.value > maiorLance, "lance baixo");
        if (maiorComprador != address(0)) {
            aDevolver[maiorComprador] += maiorLance; // o anterior saca depois
        }
        maiorComprador = msg.sender;
        maiorLance = msg.value;
    }

    function retirar() external {
        uint valor = aDevolver[msg.sender];
        require(valor > 0, "nada a retirar");
        aDevolver[msg.sender] = 0; // efeito antes da interacao
        (bool ok, ) = payable(msg.sender).call{value: valor}("");
        require(ok, "falha no envio");
    }

    function encerrar() external {
        require(block.timestamp >= fim, "ainda em andamento");
        require(!encerrado, "ja encerrado");
        encerrado = true;
        (bool ok, ) = payable(beneficiario).call{value: maiorLance}("");
        require(ok, "falha no envio");
    }
}
