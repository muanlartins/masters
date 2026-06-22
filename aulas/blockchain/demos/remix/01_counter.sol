// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// Demo de aquecimento: estado on-chain, transação vs. leitura, gas, revert.
/// `count` é public => o Solidity gera um getter automático (botão azul).
contract Counter {
    uint public count;

    // Cada chamada é uma TRANSAÇÃO: muda o estado, custa gas (botão laranja).
    function increment() external {
        count += 1;
    }

    // 0.8.x reverte em underflow sozinho; o require dá uma mensagem clara.
    function decrement() external {
        require(count > 0, "count ja esta em zero");
        count -= 1;
    }
}
