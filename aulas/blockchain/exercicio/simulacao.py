#!/usr/bin/env python3
"""Simulação narrada da mini-blockchain. Rode:  ./simulacao.sh

Não vale nota. Percorre cada peça mostrando EXATAMENTE o que é feito e como: os
hashes reais, a árvore de Merkle sendo montada, uma transação sendo assinada e
adulterada, o cabeçalho de 80 bytes, a mineração tentando nonces, a cadeia
quebrando ao ser adulterada e o desempate por trabalho acumulado.

Usa as peças do gabarito por padrão; conforme você liga as suas em config.py,
passa a mostrar o seu código rodando.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from minichain import kit, config              # noqa: E402
from minichain import build                    # noqa: E402
from minichain.crypto import sha256d, gen_keys  # noqa: E402
from minichain.types import Tx, Block          # noqa: E402

GENESIS_PREV = b"\x00" * 32
_TTY = sys.stdout.isatty()


def _c(code):
    return code if _TTY else ""


BOLD, DIM = _c("\033[1m"), _c("\033[2m")
CYAN, GREEN, RED, YEL = _c("\033[36m"), _c("\033[32m"), _c("\033[31m"), _c("\033[33m")
R = _c("\033[0m")


def hx(b, n=6):
    """Hex dos primeiros n bytes (… se houver mais)."""
    return b[:n].hex() + ("…" if len(b) > n else "")


def titulo(n, txt):
    print(f"\n{BOLD}{CYAN}{'━' * 72}{R}")
    print(f"{BOLD}{CYAN}  {n}. {txt}{R}")
    print(f"{BOLD}{CYAN}{'━' * 72}{R}")


def p(txt=""):
    print(f"  {txt}")


def det(txt):
    print(f"     {DIM}{txt}{R}")


def sim(b):
    return f"{GREEN}sim{R}" if b else f"{RED}não{R}"


def _signed(sk, vk, para, valor):
    tx = Tx(sender=vk.to_string(), recipient=para, amount=valor)
    kit.sign_tx(tx, sk)
    return tx


# ── 1. hash ─────────────────────────────────────────────────────────────────
def parte_hash():
    titulo(1, "Hash: a impressão digital de mão única")
    m1 = "Alice paga 5 a Bob"
    m2 = "Alice paga 6 a Bob"
    p(f'mensagem: "{m1}"')
    p(f"sha256d = {hx(sha256d(m1.encode()), 32)}")
    det("determinístico: a mesma entrada dá sempre o mesmo hash")
    print()
    p(f'troquei só o "5" por "6": "{m2}"')
    p(f"sha256d = {hx(sha256d(m2.encode()), 32)}")
    det("efeito avalanche: 1 caractere muda o hash inteiro — e não há volta")


# ── 2. árvore de Merkle ─────────────────────────────────────────────────────
def parte_merkle():
    titulo(2, "Árvore de Merkle: provar que uma tx está no bloco")
    sk, vk = gen_keys()
    alvo = 2  # vamos provar que a tx de Dave (índice 2) está no bloco
    dests = [b"Bob", b"Carol", b"Dave", b"Erin"]
    txs = [_signed(sk, vk, d, v) for d, v in zip(dests, [5, 2, 9, 1])]
    folhas = [kit.txid(t) for t in txs]
    p(f"{BOLD}folhas{R} — uma por transação (folha = txid = sha256d da tx):")
    for i, (d, h) in enumerate(zip(dests, folhas)):
        marca = f"   {YEL}← queremos provar esta{R}" if i == alvo else ""
        p(f"  h{i}  {d.decode():<6} {hx(h)}{marca}")

    h01 = sha256d(folhas[0] + folhas[1])
    h23 = sha256d(folhas[2] + folhas[3])
    raiz = sha256d(h01 + h23)
    nome = {folhas[0]: "h0", folhas[1]: "h1", folhas[2]: "h2", folhas[3]: "h3",
            h01: "h01", h23: "h23", raiz: "raiz"}
    print()
    p(f"{BOLD}a árvore sobe emparelhando vizinhos{R} (pai = sha256d(esq ‖ dir)):")
    p("  h01  = H(h0 ‖ h1)")
    p("  h23  = H(h2 ‖ h3)")
    p(f"  raiz = H(h01 ‖ h23) = {hx(raiz)}")
    det(f"bate com kit.merkle_root(folhas)? {sim(raiz == kit.merkle_root(folhas))}")

    print()
    prova = kit.merkle_proof(folhas, alvo)
    p(f"{BOLD}a prova de que h2 (Dave) está no bloco{R} são só os irmãos no caminho:")
    for lado, irmao in prova:
        onde = "direita" if lado == "right" else "esquerda"
        p(f"  {nome[irmao]:<4} (o irmão à {onde})")
    det(f"{len(prova)} hashes, não as {len(txs)} txs inteiras "
        "(num bloco real: ~12, não milhares)")

    print()
    p(f"{BOLD}quem tem só a tx de Dave + a prova refaz o caminho até a raiz:{R}")
    h = folhas[alvo]
    for lado, irmao in prova:
        if lado == "left":
            novo = sha256d(irmao + h)
            eq = f"H({nome[irmao]} ‖ {nome[h]})"
        else:
            novo = sha256d(h + irmao)
            eq = f"H({nome[h]} ‖ {nome[irmao]})"
        p(f"  {eq:<14} = {nome[novo]}")
        h = novo
    p(f"  → {nome[h]} = {hx(h)} — é a raiz publicada? {sim(h == raiz)}")


# ── 3. assinatura ───────────────────────────────────────────────────────────
def parte_assinatura():
    titulo(3, "Assinatura: quem autorizou, e que nada foi alterado")
    sk, vk = gen_keys()
    tx = Tx(sender=vk.to_string(), recipient=b"Bob", amount=5)
    p(f"chave pública de quem envia: {hx(tx.sender, 10)}")
    p(f"payload a assinar = sender ‖ recipient ‖ amount")
    det(f"= {hx(kit.payload(tx), 18)}")
    kit.sign_tx(tx, sk)
    p(f"assinatura (com a chave privada): {hx(tx.signature, 12)}")
    p(f"a rede confere com a chave pública — válida? {sim(kit.tx_is_valid(tx))}")
    print()
    p("um atacante troca o valor de 5 para 5000 (sem a chave privada)…")
    tx.amount = 5000
    p(f"válida agora? {sim(kit.tx_is_valid(tx))}")
    det("o payload mudou, então a assinatura não corresponde mais a ele")


# ── 4. cabeçalho ────────────────────────────────────────────────────────────
def parte_cabecalho():
    titulo(4, "Cabeçalho de 80 bytes — é o que se faz hash e o que encadeia")
    sk, vk = gen_keys()
    b = Block(version=1, prev_hash=GENESIS_PREV,
              txs=[_signed(sk, vk, b"Bob", 5)], timestamp=1_700_000_000, bits=16)
    kit.compute_merkle(b)
    p(f"version      (4B) = {b.version}")
    p(f"prev_hash   (32B) = {hx(b.prev_hash)}   (hash do bloco anterior)")
    p(f"merkle_root (32B) = {hx(b.merkle_root)}   (resume todas as txs)")
    p(f"timestamp    (4B) = {b.timestamp}")
    p(f"bits         (4B) = {b.bits}   (o alvo da mineração)")
    p(f"nonce        (4B) = {b.nonce}   (o que o minerador varia)")
    hdr = kit.header_bytes(b)
    print()
    p(f"serializado: {len(hdr)} bytes")
    det(hx(hdr, 80))
    p(f"hash do bloco = sha256d(cabeçalho) = {hx(kit.block_hash(b))}")
    det("esse hash vira o prev_hash do próximo bloco — é o elo da corrente")


# ── 5. mineração ────────────────────────────────────────────────────────────
def parte_mineracao():
    titulo(5, "Mineração: achar um nonce cujo hash caia abaixo do alvo")
    bits = 16
    sk, vk = gen_keys()
    b = Block(version=1, prev_hash=GENESIS_PREV,
              txs=[_signed(sk, vk, b"Bob", 5)], timestamp=1_700_000_000, bits=bits)
    kit.compute_merkle(b)
    p(f"alvo: bits={bits} → o hash precisa começar com {bits // 4} zeros hex")
    p("varrendo nonces (não há atalho — só testar):")
    nonce = 0
    mostrados = 0
    while True:
        b.nonce = nonce
        h = kit.block_hash(b)
        ok = kit.meets_target(h, bits)
        if ok or mostrados < 3:
            marca = f"{GREEN}< alvo  ✓{R}" if ok else f"{DIM}≥ alvo{R}"
            p(f"  nonce={nonce:<7} hash={hx(h)}  {marca}")
            mostrados += 1
        if ok:
            break
        nonce += 1
    print()
    p(f"achou em {YEL}{nonce + 1}{R} tentativas — daí os nonces grandes")
    det(f"~2^{bits} = {2 ** bits} tentativas em média; esse trabalho é o que custa energia")


# ── 6. encadeamento ─────────────────────────────────────────────────────────
def parte_cadeia():
    titulo(6, "Encadeamento: adulterar um bloco quebra a cadeia")
    sk, vk = gen_keys()
    chain = build.genesis(bits=12)
    build.append(chain, [_signed(sk, vk, b"Bob", 5)], bits=12)
    build.append(chain, [_signed(sk, vk, b"Carol", 3)], bits=12)
    for i, b in enumerate(chain):
        p(f"bloco {i}: hash={hx(kit.block_hash(b))}  prev={hx(b.prev_hash)}")
    det("o prev de cada bloco é exatamente o hash do anterior")
    p(f"cadeia inteira válida? {sim(kit.is_valid_chain(chain))}")
    print()
    p("adultero uma transação dentro do bloco 1…")
    chain[1].txs[0].amount = 999_999
    p(f"cadeia válida agora? {sim(kit.is_valid_chain(chain))}")
    p("checando bloco a bloco:")
    for i, b in enumerate(chain):
        prev = chain[i - 1] if i > 0 else None
        ok = kit.validate_block(b, prev)
        p(f"  bloco {i}: {'ok' if ok else RED + 'QUEBRADO' + R}")
    det("a raiz de Merkle do bloco 1 não bate mais com as txs (e a assinatura caiu)")


# ── 7. cadeia mais longa ────────────────────────────────────────────────────
def parte_forks():
    titulo(7, "Cadeia mais longa: o desempate objetivo entre versões")
    sk, vk = gen_keys()

    def faz(n):
        c = build.genesis(bits=8)
        for _ in range(n):
            build.append(c, [_signed(sk, vk, b"Bob", 1)], bits=8)
        return c

    a, b = faz(1), faz(3)
    p(f"versão A: {len(a)} blocos · trabalho acumulado = {kit.chain_work(a)}")
    p(f"versão B: {len(b)} blocos · trabalho acumulado = {kit.chain_work(b)}")
    vencedora = kit.best_chain([a, b])
    qual = "B" if vencedora is b else "A"
    p(f"a rede adota a versão {YEL}{qual}{R} — a de mais trabalho acumulado")
    det("reescrever a história = refazer todo esse trabalho e ainda alcançar a rede")


def main():
    ligadas = [k for k, v in config.MINHA.items() if v] or ["nenhuma (tudo gabarito)"]
    print(f"\n{BOLD}Simulação minichain{R}  ·  peças com o seu código: {', '.join(ligadas)}")
    parte_hash()
    parte_merkle()
    parte_assinatura()
    parte_cabecalho()
    parte_mineracao()
    parte_cadeia()
    parte_forks()
    print(f"\n{DIM}fim — rode ./testar.sh e ./progresso.sh para implementar as peças.{R}\n")


if __name__ == "__main__":
    main()
