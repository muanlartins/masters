// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// Exercicio 1 — Cofre  (aquecimento: payable, msg.value/sender, require, enviar ETH)
//
// Um cofre coletivo: QUALQUER um deposita ETH, mas SO o dono (quem fez o deploy)
// pode liberar. Voce vai praticar os 4 ingredientes basicos de um contrato que
// mexe com dinheiro:
//   - receber ETH        -> a funcao precisa ser `payable`; o valor vem em msg.value
//   - saber quem chamou   -> msg.sender
//   - travar quem pode o que -> require(condicao, "mensagem")
//   - enviar ETH          -> (bool ok, ) = payable(dest).call{value: x}("");  require(ok, ...)
//
// Quando os testes ficarem verdes, ligue "cofre": true em config.js.

contract Cofre {
    address public dono;                        // quem fez o deploy
    mapping(address => uint) public depositado; // quanto cada endereco ja pos

    constructor() {
        dono = msg.sender;
    }

    function depositar() external payable {
        // TODO: exija que msg.value > 0 ("envie algum valor") e some msg.value
        //       em depositado[msg.sender].
        revert("TODO: implemente depositar");
    }

    function sacar(address para, uint valor) external {
        // TODO: so o dono pode sacar ("somente o dono"); 'valor' nao pode passar
        //       do saldo do contrato address(this).balance ("saldo insuficiente");
        //       envie 'valor' wei para 'para' com call{value:...} e exija que o
        //       envio deu certo ("falha no envio").
        revert("TODO: implemente sacar");
    }

    function saldo() external view returns (uint) {
        // TODO: devolva o ETH guardado no contrato (address(this).balance).
        revert("TODO: implemente saldo");
    }
}
