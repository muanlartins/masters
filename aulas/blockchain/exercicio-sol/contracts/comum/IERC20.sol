// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// Interface ERC-20 (so o que o DvP precisa enxergar de um token externo).
interface IERC20 {
    function transfer(address to, uint value) external returns (bool);
    function transferFrom(address from, address to, uint value) external returns (bool);
    function approve(address spender, uint value) external returns (bool);
    function balanceOf(address owner) external view returns (uint);
    function allowance(address owner, address spender) external view returns (uint);
}
