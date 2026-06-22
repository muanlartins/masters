"""Quais partes VOCÊ já implementou.

Enquanto uma parte está em False, o exercício usa a peça pronta do GABARITO —
assim você pode rodar e testar qualquer parte em qualquer ordem, sem precisar
ter feito as outras. Quando terminar de implementar uma parte em
`minichain/voce/`, mude para True: o sistema (e os testes daquela parte) passam
a usar o SEU código — inclusive dentro das outras peças.

Exemplo: quer fazer só o PoW (Parte 4)? Deixe tudo False, ligue só "pow": True,
implemente `voce/pow.py`. Seu PoW vai usar o Merkle/cabeçalho do gabarito.
Depois volte, ligue "merkle"/"block", e o seu PoW passa a usar as SUAS peças.
"""

MINHA = {
    "merkle": False,  # Parte 1 — árvore de Merkle
    "tx":     False,  # Parte 2 — transações assinadas
    "block":  False,  # Parte 3 — cabeçalho de 80 bytes e hash do bloco
    "pow":    False,  # Parte 4 — mineração (proof of work)
    "chain":  False,  # Parte 5 — encadeamento e validação
    "fork":   False,  # Parte 6 — cadeia mais longa (forks)
}
