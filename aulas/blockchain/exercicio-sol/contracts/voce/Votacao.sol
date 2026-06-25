// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// Exercicio 2 — Votacao  (mapping, struct/array, prazo com block.timestamp)
//
// Uma urna: o deploy recebe a lista de candidatos e uma duracao. Cada endereco
// vota UMA vez, dentro do prazo. Depois do prazo, qualquer um apura o vencedor.
// Voce pratica: contar com mapping, impedir acao repetida (1 endereco = 1 voto)
// e usar o relogio da rede (block.timestamp) pra abrir/fechar a votacao.
//
// O construtor e a lista de candidatos ja estao prontos. Quando os testes
// ficarem verdes, ligue "votacao": true em config.js.

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
        // TODO, nesta ordem de checagem:
        //   - so antes do prazo: block.timestamp < fim   ("votacao encerrada")
        //   - idx tem que existir: idx < candidatos.length ("candidato invalido")
        //   - quem chama nao pode ter votado: !jaVotou[msg.sender] ("ja votou")
        // depois: marque jaVotou[msg.sender] e some 1 em votos[idx].
        revert("TODO: implemente votar");
    }

    function vencedor() external view returns (uint) {
        // TODO: so depois do prazo (block.timestamp >= fim, senao "votacao em
        //       andamento"); percorra os candidatos e devolva o INDICE do mais
        //       votado (em empate, o de menor indice serve).
        revert("TODO: implemente vencedor");
    }
}
