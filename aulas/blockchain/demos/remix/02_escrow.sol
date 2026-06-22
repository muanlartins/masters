// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// Confiança programável: comprador deposita, e só o árbitro libera para o
/// vendedor (ou devolve). Nem comprador nem vendedor controla o dinheiro
/// sozinho — o código garante as regras. Mostra: payable, msg.value,
/// require (controle de acesso) e uma pequena máquina de estados.
contract Escrow {
    address public buyer;
    address public seller;
    address public arbiter;
    uint    public amount;
    bool    public funded;
    bool    public released;

    constructor(address _seller, address _arbiter) {
        buyer   = msg.sender; // quem faz o deploy é o comprador
        seller  = _seller;
        arbiter = _arbiter;
    }

    function deposit() external payable {
        require(msg.sender == buyer, "somente o comprador");
        require(!funded, "ja depositado");
        amount = msg.value;
        funded = true;
    }

    function release() external {
        require(msg.sender == arbiter, "somente o arbitro");
        require(funded && !released, "estado invalido");
        released = true; // efeito antes da interacao (checks-effects-interactions)
        (bool ok, ) = payable(seller).call{value: amount}(""); // vendedor recebe
        require(ok, "falha no envio");
    }

    function refund() external {
        require(msg.sender == arbiter, "somente o arbitro");
        require(funded && !released, "estado invalido");
        released = true; // efeito antes da interacao
        (bool ok, ) = payable(buyer).call{value: amount}(""); // comprador reembolsado
        require(ok, "falha no envio");
    }
}
