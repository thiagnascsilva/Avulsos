"""
Gráfico da evolução das chances de título ao longo do Mundial 2026.

Lê evolucao_probabilidades.csv (uma linha por partida jogada, preenchida à
mão depois de cada simulação) e salva evolucao_probabilidades.png ao lado do
script.

Uso:
    python plotar_evolucao_probabilidades.py

Requer matplotlib (pip install matplotlib).
"""

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, PercentFormatter

from config import PARTIDAS_MATCH

PASTA = Path(__file__).parent
ARQUIVO_CSV = PASTA / "evolucao_probabilidades.csv"
ARQUIVO_PNG = PASTA / "evolucao_probabilidades.png"

# coluna do CSV -> (rótulo, cor)
SERIES = {
    "sindarov": ("Sindarov campeão", "#257de0"),
    "gukesh": ("Gukesh campeão", "#f47230"),
    "empate": ("Empate (7 x 7)", "#00b894"),
}

COR_SUPERFICIE = "#ffffff"
COR_TEXTO = "#191919"
COR_TEXTO_SECUNDARIO = "#666666"
COR_GRADE = "#e6e6e6"


# ---------------------------------------------------------------- dados

def carregar_evolucao() -> dict[str, list[float]]:
    colunas: dict[str, list[float]] = {"partidas_jogadas": []}
    colunas.update({serie: [] for serie in SERIES})
    with ARQUIVO_CSV.open(encoding="utf-8") as arquivo:
        for linha in csv.DictReader(arquivo):
            for coluna, valores in colunas.items():
                valores.append(float(linha[coluna]))
    return colunas


# ---------------------------------------------------------------- gráfico

def afastar_rotulos(valores: dict[str, float],
                    distancia_minima: float) -> dict[str, float]:
    """Posição vertical de cada rótulo, com pelo menos distancia_minima
    pontos percentuais entre rótulos vizinhos."""
    ordenados = sorted(valores, key=valores.get)
    posicoes: dict[str, float] = {}
    anterior = None
    for serie in ordenados:
        posicao = valores[serie]
        if anterior is not None:
            posicao = max(posicao, anterior + distancia_minima)
        posicoes[serie] = anterior = posicao
    return posicoes


def plotar(colunas: dict[str, list[float]]) -> None:
    partidas = colunas["partidas_jogadas"]

    fig, eixo = plt.subplots(figsize=(10, 5.5), dpi=150)
    fig.patch.set_facecolor(COR_SUPERFICIE)
    eixo.set_facecolor(COR_SUPERFICIE)

    for serie, (rotulo, cor) in SERIES.items():
        eixo.plot(partidas, colunas[serie], color=cor, linewidth=2,
                  label=rotulo, marker="o", markersize=6,
                  markeredgecolor=COR_SUPERFICIE, markeredgewidth=1.5,
                  solid_capstyle="round", zorder=3)

    # rótulo direto só no último ponto, afastando os que ficariam colados
    finais = {serie: colunas[serie][-1] for serie in SERIES}
    posicoes = afastar_rotulos(finais, distancia_minima=5.0)
    for serie, valor in finais.items():
        eixo.annotate(f"{valor:.1f}%", (partidas[-1], valor),
                      xytext=(partidas[-1] + 0.15, posicoes[serie]),
                      textcoords="data", va="center", fontsize=10,
                      color=COR_TEXTO)

    eixo.set_xlim(-0.3, PARTIDAS_MATCH + 0.3)
    eixo.set_ylim(0, 100)
    eixo.xaxis.set_major_locator(MultipleLocator(1))
    eixo.yaxis.set_major_locator(MultipleLocator(20))
    eixo.yaxis.set_major_formatter(PercentFormatter(decimals=0))
    eixo.set_xlabel("Partidas jogadas", color=COR_TEXTO_SECUNDARIO)
    eixo.set_ylabel("Chance de título", color=COR_TEXTO_SECUNDARIO)

    eixo.grid(axis="y", color=COR_GRADE, linewidth=0.8)
    eixo.set_axisbelow(True)
    for lado in ("top", "right", "left"):
        eixo.spines[lado].set_visible(False)
    eixo.spines["bottom"].set_color(COR_GRADE)
    eixo.tick_params(colors=COR_TEXTO_SECUNDARIO, length=0)

    eixo.set_title("Mundial 2026: chances de título após cada partida",
                   loc="left", fontsize=13, color=COR_TEXTO, pad=28)
    eixo.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=3,
                frameon=False, fontsize=10, labelcolor=COR_TEXTO,
                borderaxespad=0.2, handlelength=1.5)

    fig.tight_layout()
    fig.savefig(ARQUIVO_PNG, facecolor=COR_SUPERFICIE)
    plt.close(fig)


# ---------------------------------------------------------------- main

def main() -> None:
    plotar(carregar_evolucao())
    print(f"Gráfico salvo em {ARQUIVO_PNG.name}")


if __name__ == "__main__":
    main()
