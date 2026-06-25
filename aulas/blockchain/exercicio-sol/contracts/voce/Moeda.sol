// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// Exercicio 5 — Moeda ERC-20  (o padrao de token que move trilhoes la fora)
//
// Voce vai implementar o coracao do ERC-20 — o MESMO padrao do USDC que a aula
// mostra no Etherscan. Sao tres funcoes:
//   - transfer(to, value)            : mando MEU saldo pra alguem.
//   - approve(spender, value)        : autorizo um terceiro a gastar ate 'value'
//                                       do MEU saldo (allowance).
//   - transferFrom(from, to, value)  : um terceiro autorizado move o saldo de
//                                       'from' (debitando a allowance dele).
// Cada movimento emite o evento Transfer; approve emite Approval. Esses eventos
// sao a fonte que o Etherscan/carteiras leem pra montar "quem tem quanto".
//
// O estado, os eventos e o construtor (que cria o supply na sua conta) ja vem
// prontos. Ligue "moeda": true em config.js quando passar.

contract Moeda {
    string public name = "Moeda da Aula";
    string public symbol = "AULA";
    uint8 public constant decimals = 18;
    uint public totalSupply;
    mapping(address => uint) public balanceOf;
    mapping(address => mapping(address => uint)) public allowance;

    event Transfer(address indexed from, address indexed to, uint value);
    event Approval(address indexed owner, address indexed spender, uint value);

    constructor(uint supplyInicial) {
        totalSupply = supplyInicial;
        balanceOf[msg.sender] = supplyInicial;
        emit Transfer(address(0), msg.sender, supplyInicial);
    }

    function transfer(address to, uint value) external returns (bool) {
        // TODO: exija saldo ("saldo insuficiente"); mova value de
        //       balanceOf[msg.sender] para balanceOf[to]; emita
        //       Transfer(msg.sender, to, value); retorne true.
        revert("TODO: implemente transfer");
    }

    function approve(address spender, uint value) external returns (bool) {
        // TODO: grave allowance[msg.sender][spender] = value; emita
        //       Approval(msg.sender, spender, value); retorne true.
        revert("TODO: implemente approve");
    }

    function transferFrom(address from, address to, uint value) external returns (bool) {
        // TODO: exija saldo de 'from' ("saldo insuficiente") e allowance
        //       suficiente de 'from' para msg.sender ("allowance insuficiente");
        //       debite a allowance; mova value de from para to; emita
        //       Transfer(from, to, value); retorne true.
        revert("TODO: implemente transferFrom");
    }
}
