// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// Votacao com prazo: cada endereco vota uma vez; apura o vencedor. (REFERENCIA)
contract Votacao {
    address public admin;
    uint public fim; // timestamp de encerramento
    string[] public candidatos;
    mapping(uint => uint) public votos; // idx do candidato -> contagem
    mapping(address => bool) public jaVotou;

    constructor(string[] memory nomes, uint duracaoSegundos) {
        admin = msg.sender;
        candidatos = nomes;
        fim = block.timestamp + duracaoSegundos;
    }

    function totalCandidatos() external view returns (uint) {
        return candidatos.length;
    }

    function votar(uint idx) external {
        require(block.timestamp < fim, "votacao encerrada");
        require(idx < candidatos.length, "candidato invalido");
        require(!jaVotou[msg.sender], "ja votou");
        jaVotou[msg.sender] = true;
        votos[idx] += 1;
    }

    function vencedor() external view returns (uint) {
        require(block.timestamp >= fim, "votacao em andamento");
        uint melhor = 0;
        for (uint i = 1; i < candidatos.length; i++) {
            if (votos[i] > votos[melhor]) melhor = i;
        }
        return melhor;
    }
}
