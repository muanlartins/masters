// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// Vaquinha tudo-ou-nada: bateu a meta ate o prazo, o beneficiario saca; senao,
/// cada um pega o seu de volta. Reembolso usa checks-effects-interactions. (REFERENCIA)
contract Crowdfunding {
    address public beneficiario;
    uint public meta;  // em wei
    uint public fim;   // timestamp de encerramento
    uint public total;
    bool public sacado;
    mapping(address => uint) public contribuido;

    constructor(uint metaWei, uint duracaoSegundos) {
        beneficiario = msg.sender;
        meta = metaWei;
        fim = block.timestamp + duracaoSegundos;
    }

    function contribuir() external payable {
        require(block.timestamp < fim, "campanha encerrada");
        require(msg.value > 0, "envie algum valor");
        contribuido[msg.sender] += msg.value;
        total += msg.value;
    }

    function sacar() external {
        require(block.timestamp >= fim, "ainda em andamento");
        require(total >= meta, "meta nao atingida");
        require(msg.sender == beneficiario, "somente o beneficiario");
        require(!sacado, "ja sacado");
        sacado = true;
        (bool ok, ) = payable(beneficiario).call{value: address(this).balance}("");
        require(ok, "falha no envio");
    }

    function reembolsar() external {
        require(block.timestamp >= fim, "ainda em andamento");
        require(total < meta, "meta atingida");
        uint valor = contribuido[msg.sender];
        require(valor > 0, "nada a reembolsar");
        contribuido[msg.sender] = 0; // efeito antes da interacao
        (bool ok, ) = payable(msg.sender).call{value: valor}("");
        require(ok, "falha no envio");
    }
}
