import os
import sys

# Garante que `import minichain` funcione rodando pytest de qualquer lugar.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pytest

# ── saída legível para ./testar.sh (flag --pretty) ──────────────────────────
# Mostra, agrupado por parte, cada teste (a docstring), com ✓/✗ e o motivo da
# falha. O progresso.sh não usa --pretty, então continua compacto.

_TITLES = {
    "test_merkle": "Parte 1 · Árvore de Merkle",
    "test_tx":     "Parte 2 · Transações assinadas",
    "test_block":  "Parte 3 · Cabeçalho & hash do bloco",
    "test_pow":    "Parte 4 · Mineração (proof of work)",
    "test_chain":  "Parte 5 · Encadeamento & validação",
    "test_fork":   "Parte 6 · Cadeia mais longa (forks)",
}

_TTY = sys.stdout.isatty()
_G = "\033[32m" if _TTY else ""   # verde
_R = "\033[31m" if _TTY else ""   # vermelho
_D = "\033[2m" if _TTY else ""    # apagado
_B = "\033[1m" if _TTY else ""    # negrito
_0 = "\033[0m" if _TTY else ""    # reset

_results = []  # (modname, desc, outcome, reason)


def pytest_addoption(parser):
    parser.addoption("--pretty", action="store_true",
                     help="saída legível, agrupada por parte")


def _modname(nodeid):
    fname = nodeid.split("::", 1)[0]
    return os.path.splitext(os.path.basename(fname))[0]


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" and not report.failed:
        return
    desc = (item.obj.__doc__ or item.name).strip().splitlines()[0]
    reason = ""
    if report.failed and call.excinfo is not None:
        # exconly() -> "ExcType: mensagem" (independe do estilo de traceback)
        reason = call.excinfo.exconly().strip().splitlines()[0]
    _results.append((_modname(item.nodeid), desc, report.outcome, reason))


def pytest_report_teststatus(report, config):
    # Com --pretty, suprime o ponto padrão SÓ na fase "call" (imprimimos nosso
    # relatório no fim). As fases setup/teardown seguem o padrão, senão o total
    # de "passed" contaria cada teste 3×.
    if config.getoption("--pretty") and report.when == "call":
        return report.outcome, "", ""
    return None


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    if not config.getoption("--pretty") or not _results:
        return
    w = terminalreporter.write_line
    by_mod = {}
    for mod, desc, outcome, reason in _results:
        by_mod.setdefault(mod, []).append((desc, outcome, reason))
    order = [m for m in _TITLES if m in by_mod] + [m for m in by_mod if m not in _TITLES]
    n_ok = n_fail = 0
    for mod in order:
        w("")
        w(f"{_B}{_TITLES.get(mod, mod)}{_0}")
        for desc, outcome, reason in by_mod[mod]:
            if outcome == "passed":
                n_ok += 1
                w(f"  {_G}✓{_0}  {desc}")
            else:
                n_fail += 1
                w(f"  {_R}✗  {desc}{_0}")
                if reason:
                    w(f"       {_D}{reason}{_0}")
    w("")
    cor = _G if n_fail == 0 else _R
    resumo = f"{n_ok}/{n_ok + n_fail} testes passaram"
    if n_fail:
        resumo += f" · {n_fail} a corrigir"
    w(f"{cor}{_B}{resumo}{_0}")
    w("")
