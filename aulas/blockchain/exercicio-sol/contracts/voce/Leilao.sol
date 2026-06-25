// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// Exercicio 4 — Leilao ingles  (o padrao "pull payment": cada um saca o seu)
//
// Lances crescentes ate o prazo. Quando alguem e superado, o contrato NAO
// devolve o ETH na hora (enviar para muita gente em loop e arriscado e caro) —
// ele credita o valor num saldo "aDevolver", e quem foi superado chama
// retirar() pra sacar o seu. Esse e o padrao seguro recomendado em Solidity.
// No fim, o beneficiario recebe o maior lance.
//
// Voce pratica: comparar contra o maior lance, creditar o anterior, e o
// pull-payment (zere antes de enviar). Construtor pronto. Ligue
// "leilao": true em config.js quando passar.

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
        // TODO: so antes do prazo ("leilao encerrado"); o lance precisa ser
        //       MAIOR que maiorLance ("lance baixo"). Se ja havia um
        //       maiorComprador (!= address(0)), some o maiorLance atual em
        //       aDevolver[maiorComprador]. Depois atualize maiorComprador e
        //       maiorLance para msg.sender / msg.value.
        revert("TODO: implemente darLance");
    }

    function retirar() external {
        // TODO (pull payment): valor = aDevolver[msg.sender] (>0, senao
        //       "nada a retirar"); ZERE aDevolver[msg.sender] ANTES de enviar;
        //       envie 'valor' a msg.sender (exija ok, "falha no envio").
        revert("TODO: implemente retirar");
    }

    function encerrar() external {
        // TODO: so depois do prazo ("ainda em andamento"); so uma vez
        //       ("ja encerrado"). Marque encerrado e envie maiorLance ao
        //       beneficiario (exija ok, "falha no envio").
        revert("TODO: implemente encerrar");
    }
}
