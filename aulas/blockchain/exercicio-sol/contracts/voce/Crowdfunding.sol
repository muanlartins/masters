// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// Exercicio 3 — Crowdfunding  (estado + tempo + dinheiro, com duas saidas)
//
// Uma vaquinha tudo-ou-nada. O deploy fixa uma meta (em wei) e um prazo.
// Enquanto aberto, qualquer um contribui. Depois do prazo:
//   - se o total >= meta  -> o beneficiario (quem fez o deploy) saca tudo;
//   - se nao bateu a meta  -> cada contribuinte pega o SEU de volta (reembolso).
//
// O reembolso e o ponto-chave: zere o registro do contribuinte ANTES de enviar
// o ETH (checks-effects-interactions) — a mesma ordem que evitou a reentrancia
// da aula. Construtor e estado ja vem prontos. Ligue "crowdfunding": true em
// config.js quando passar.

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
        // TODO: so antes do prazo ("campanha encerrada") e com msg.value > 0
        //       ("envie algum valor"); some msg.value em contribuido[msg.sender]
        //       e em total.
        revert("TODO: implemente contribuir");
    }

    function sacar() external {
        // TODO: so depois do prazo ("ainda em andamento"); so se total >= meta
        //       ("meta nao atingida"); so o beneficiario ("somente o
        //       beneficiario"); so uma vez ("ja sacado"). Marque sacado e envie
        //       todo o address(this).balance ao beneficiario (exija ok).
        revert("TODO: implemente sacar");
    }

    function reembolsar() external {
        // TODO: so depois do prazo ("ainda em andamento") e so se a meta NAO foi
        //       atingida ("meta atingida"); pegue valor = contribuido[msg.sender]
        //       (>0, senao "nada a reembolsar"); ZERE contribuido[msg.sender]
        //       ANTES de enviar; envie 'valor' a msg.sender (exija ok).
        revert("TODO: implemente reembolsar");
    }
}
