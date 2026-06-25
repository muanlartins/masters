// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "../comum/IERC20.sol";

// Exercicio 6 — DvP: entrega contra pagamento  (o climax: troca atomica)
//
// "Entrega contra pagamento" (Delivery versus Payment) e a regra de ouro da
// liquidacao financeira: a entrega do ativo e o pagamento acontecem JUNTOS, ou
// nenhum dos dois acontece. Ninguem paga e fica sem receber; ninguem entrega e
// fica sem ser pago. (No mundo real isso e o risco Herstatt; o smart contract
// resolve com atomicidade.)
//
// Aqui o ativo e um token ERC-20 (do vendedor) e o pagamento e ETH (do
// comprador). O construtor fixa o token, as duas partes, a quantidade e o
// preco. Pre-condicao: o vendedor da approve neste contrato para os tokens.
//
// O segredo da atomicidade: se a entrega do token falhar (ex.: o vendedor nao
// aprovou), o transferFrom REVERTE e leva a transacao inteira junto — entao o
// ETH do comprador nem chega a sair. Uma transacao, tudo-ou-nada.
//
// Voce implementa liquidar() e cancelar(). O token vem da interface IERC20
// (token.transferFrom(de, para, qtd)). Ligue "dvp": true em config.js ao passar.

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
        // TODO, nesta ordem:
        //   - require(!liquidado, "ja liquidado")
        //   - require(!cancelado, "cancelado")
        //   - so o comprador: msg.sender == comprador ("somente o comprador")
        //   - pagamento exato: msg.value == preco ("pagamento incorreto")
        //   marque liquidado = true ANTES de mexer com terceiros; entao:
        //   - entrega: require(token.transferFrom(vendedor, comprador,
        //              quantidadeToken), "falha na entrega")
        //   - pagamento: envie 'preco' wei ao vendedor com call (exija ok,
        //              "falha no pagamento")
        revert("TODO: implemente liquidar");
    }

    function cancelar() external {
        // TODO: so antes de liquidar ("ja liquidado"); so o comprador ou o
        //       vendedor ("somente as partes"); marque cancelado = true.
        revert("TODO: implemente cancelar");
    }
}
