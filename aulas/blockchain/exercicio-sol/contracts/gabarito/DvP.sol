// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "../comum/IERC20.sol";

/// Entrega-contra-pagamento (Delivery versus Payment) atomico: o token do
/// vendedor e o ETH do comprador trocam de mao na MESMA transacao — ou nada
/// acontece. Elimina o risco de liquidacao (pagar e nao receber). (REFERENCIA)
contract DvP {
    address public vendedor;
    address public comprador;
    IERC20 public token;
    uint public quantidadeToken;
    uint public preco; // em wei
    bool public liquidado;
    bool public cancelado;

    constructor(
        address _token,
        address _vendedor,
        address _comprador,
        uint _qtd,
        uint _preco
    ) {
        token = IERC20(_token);
        vendedor = _vendedor;
        comprador = _comprador;
        quantidadeToken = _qtd;
        preco = _preco;
    }

    function liquidar() external payable {
        require(!liquidado, "ja liquidado");
        require(!cancelado, "cancelado");
        require(msg.sender == comprador, "somente o comprador");
        require(msg.value == preco, "pagamento incorreto");
        liquidado = true; // efeito antes da interacao
        // entrega: exige que o vendedor tenha dado approve a este contrato.
        // se faltar approve/saldo, transferFrom reverte e TODA a tx volta atras
        // (o ETH do comprador nao e gasto) — e a atomicidade.
        require(token.transferFrom(vendedor, comprador, quantidadeToken), "falha na entrega");
        // pagamento: ETH ao vendedor.
        (bool pago, ) = payable(vendedor).call{value: preco}("");
        require(pago, "falha no pagamento");
    }

    function cancelar() external {
        require(!liquidado, "ja liquidado");
        require(msg.sender == comprador || msg.sender == vendedor, "somente as partes");
        cancelado = true;
    }
}
