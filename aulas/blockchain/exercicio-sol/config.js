// Quais exercicios VOCE ja implementou.
//
// Enquanto uma parte esta em false, os testes daquela parte rodam contra a peca
// pronta do GABARITO — assim voce pode rodar e testar qualquer exercicio em
// qualquer ordem, sem precisar ter feito os outros (todos sao INDEPENDENTES).
// Quando terminar de implementar um exercicio em contracts/voce/, mude para
// true: os testes daquela parte passam a usar o SEU contrato.
//
// Exemplo: quer fazer so o DvP? Deixe tudo false, ligue so "dvp": true e
// implemente contracts/voce/DvP.sol. Os testes do DvP passam a instanciar o
// seu contrato; os demais seguem verdes no gabarito.

module.exports = {
  cofre:        false, // 1 — Cofre (payable, saque do dono)
  votacao:      false, // 2 — Votacao (mapping, prazo, 1 voto por endereco)
  crowdfunding: false, // 3 — Crowdfunding (meta, prazo, reembolso)
  leilao:       false, // 4 — Leilao ingles (lances, pull payments)
  moeda:        false, // 5 — Moeda ERC-20 (transfer, approve, transferFrom)
  dvp:          false, // 6 — DvP (entrega contra pagamento, atomico)
};
