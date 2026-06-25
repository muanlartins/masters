// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// ERC-20 minimo PRONTO, usado pelos testes do DvP como o ativo a ser entregue.
/// Nao e exercicio — o supply nasce todo na conta de quem faz o deploy.
contract TestToken {
    string public name = "Test Token";
    string public symbol = "TST";
    uint8 public constant decimals = 18;
    uint public totalSupply;
    mapping(address => uint) public balanceOf;
    mapping(address => mapping(address => uint)) public allowance;

    event Transfer(address indexed from, address indexed to, uint value);
    event Approval(address indexed owner, address indexed spender, uint value);

    constructor(uint supply) {
        totalSupply = supply;
        balanceOf[msg.sender] = supply;
        emit Transfer(address(0), msg.sender, supply);
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
