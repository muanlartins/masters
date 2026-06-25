// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// Token ERC-20 minimo: transfer, approve/allowance, transferFrom + eventos.
/// E o mesmo padrao do USDC que a aula mostra no Etherscan. (REFERENCIA)
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
        require(balanceOf[msg.sender] >= value, "saldo insuficiente");
        balanceOf[msg.sender] -= value;
        balanceOf[to] += value;
        emit Transfer(msg.sender, to, value);
        return true;
    }

    function approve(address spender, uint value) external returns (bool) {
        allowance[msg.sender][spender] = value;
        emit Approval(msg.sender, spender, value);
        return true;
    }

    function transferFrom(address from, address to, uint value) external returns (bool) {
        require(balanceOf[from] >= value, "saldo insuficiente");
        require(allowance[from][msg.sender] >= value, "allowance insuficiente");
        allowance[from][msg.sender] -= value;
        balanceOf[from] -= value;
        balanceOf[to] += value;
        emit Transfer(from, to, value);
        return true;
    }
}
