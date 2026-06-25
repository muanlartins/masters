// Resolvedor: para cada exercicio, aponta os testes para o SEU contrato ou para
// o do GABARITO, conforme config.js. NAO precisa mexer aqui.
//
// Os dois contratos (voce/ e gabarito/) tem o mesmo nome, entao os testes
// instanciam pelo "nome totalmente qualificado" (caminho:Contrato) que esta
// funcao monta — assim a escolha "meu vs gabarito" de config.js vale em todos
// os testes automaticamente.

const config = require("./config");

function sol(parte, nome) {
  const dir = config[parte] ? "voce" : "gabarito";
  return `contracts/${dir}/${nome}.sol:${nome}`;
}

module.exports = { sol };
