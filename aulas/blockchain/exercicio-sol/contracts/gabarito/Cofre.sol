// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// Cofre coletivo: qualquer um deposita ETH; so o dono libera. (REFERENCIA)
contract Cofre {
    address public dono;
    mapping(address => uint) public depositado;

    constructor() {
        dono = msg.sender;
    }

    function depositar() external payable {
        require(msg.value > 0, "envie algum valor");
        depositado[msg.sender] += msg.value;
    }

    function sacar(address para, uint valor) external {
        require(msg.sender == dono, "somente o dono");
        require(valor <= address(this).balance, "saldo insuficiente");
        (bool ok, ) = payable(para).call{value: valor}("");
        require(ok, "falha no envio");
    }

    function saldo() external view returns (uint) {
        return address(this).balance;
    }
}
