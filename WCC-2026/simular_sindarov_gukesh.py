"""
1. Ratings FIDE (modelo Elo em elo_model.py, com vantagem das brancas e taxa
   de empate calculada pelos ratings).
2. Todos os confrontos diretos clássicos, salvos em um arquivo JSON ao lado
   do script.

Ratings e parâmetros do match ficam em config.py.

Os ratings entram como "prior" (pseudo-partidas) e o confronto direto ajusta
as probabilidades. Partidas do Mundial já registradas entram no placar, e a
simulação de Monte Carlo joga apenas o que falta. Só as partidas clássicas são
simuladas: 7 x 7 conta como empate, sem desempate.

Uso:
    python simular_sindarov_gukesh.py

Novas partidas são adicionadas à mão no arquivo JSON.
"""

import json
import random
from collections import Counter
from datetime import date
from pathlib import Path

from config import (BRANCAS_PARTIDA_1, EVENTO_MUNDIAL, FORCA_PRIOR,
                    MEIA_VIDA_ANOS, N_SIMULACOES, PARTIDAS_MATCH,
                    PONTOS_TITULO, RATINGS)
from elo_model import calcular_probabilidades_elo

ARQUIVO_HISTORICO = Path(__file__).with_name("historico_sindarov_gukesh.json")

SINDAROV = "Sindarov"
GUKESH = "Gukesh"
JOGADORES = (SINDAROV, GUKESH)
EMPATE = "Empate"
RESULTADOS_VALIDOS = ("1-0", "0-1", "1/2-1/2")

# (vitória Sindarov, empate, vitória Gukesh)
Probabilidades = tuple[float, float, float]


# ---------------------------------------------------------------- histórico
# O histórico fica em historico_sindarov_gukesh.json, ao lado do script.
# Partidas iniciais: base 365Chess, nov/2026. Datas no formato AAAA-MM.

def carregar_historico(caminho: Path = ARQUIVO_HISTORICO) -> list[dict]:
    """Lê o histórico do arquivo JSON e confere os campos editados à mão."""
    if not caminho.exists():
        raise SystemExit(f"Arquivo de histórico não encontrado: {caminho}")
    historico = json.loads(caminho.read_text(encoding="utf-8"))
    for indice, partida in enumerate(historico, start=1):
        brancas = partida["brancas"]
        resultado = partida["resultado"]
        if brancas not in JOGADORES:
            raise SystemExit(
                f"Partida {indice}: brancas inválidas {brancas!r}. "
                f"Use {' ou '.join(JOGADORES)}."
            )
        if resultado not in RESULTADOS_VALIDOS:
            raise SystemExit(
                f"Partida {indice}: resultado inválido {resultado!r}. "
                f"Use {', '.join(RESULTADOS_VALIDOS)}."
            )
    conferir_cores_mundial(historico)
    return historico


def obter_adversario(jogador: str) -> str:
    return GUKESH if jogador == SINDAROV else SINDAROV


def conferir_cores_mundial(historico: list[dict]) -> None:
    """Confere se as cores das partidas do Mundial alternam a partir da 1."""
    partidas_match = [p for p in historico if p["evento"] == EVENTO_MUNDIAL]
    primeiro = BRANCAS_PARTIDA_1
    for numero, partida in enumerate(partidas_match, start=1):
        if numero % 2 == 1:
            esperado = primeiro
        else:
            esperado = obter_adversario(primeiro)
        if partida["brancas"] != esperado:
            raise SystemExit(
                f"{EVENTO_MUNDIAL}, partida {numero}: brancas deveriam ser "
                f"{esperado}, mas o JSON diz {partida['brancas']}. "
                f"As cores alternam a partir da partida 1 ({primeiro}, "
                f"BRANCAS_PARTIDA_1 em config.py)."
            )


def calcular_pontos_sindarov(partida: dict) -> float:
    """Pontos de Sindarov na partida (1, 0.5 ou 0)."""
    if partida["resultado"] == "1/2-1/2":
        return 0.5
    if partida["resultado"] == "1-0":
        vencedor = partida["brancas"]
    else:
        vencedor = obter_adversario(partida["brancas"])
    return 1.0 if vencedor == SINDAROV else 0.0


# ---------------------------------------------------------------- modelo

def calcular_idade_anos(data_partida: str, hoje: date | None = None) -> float:
    """Idade aproximada da partida em anos (data no formato 'AAAA-MM')."""
    hoje = hoje or date.today()
    ano, mes = int(data_partida[:4]), int(data_partida[5:7])
    return max((hoje.year - ano) + (hoje.month - mes) / 12, 0.0)


def contar_confrontos(historico: list[dict]) -> dict[str, float]:
    """Vitórias/empates/derrotas de Sindarov nos confrontos clássicos.

    Cada partida é ponderada pela idade (meia-vida de MEIA_VIDA_ANOS).
    """
    contagem = {"vitoria": 0.0, "empate": 0.0, "derrota": 0.0}
    for partida in historico:
        idade = calcular_idade_anos(partida["data"])
        peso = 0.5 ** (idade / MEIA_VIDA_ANOS)
        pontos = calcular_pontos_sindarov(partida)
        chave = {1.0: "vitoria", 0.5: "empate", 0.0: "derrota"}[pontos]
        contagem[chave] += peso
    return contagem


def calcular_probabilidades(historico: list[dict],
                            brancas: str) -> Probabilidades:
    """Média posterior: Elo como prior (FORCA_PRIOR) + confronto direto."""
    prior = calcular_probabilidades_elo(
        RATINGS[SINDAROV], RATINGS[GUKESH], brancas == SINDAROV
    )
    contagem = contar_confrontos(historico)
    observados = (
        contagem["vitoria"], contagem["empate"], contagem["derrota"]
    )
    posterior = [FORCA_PRIOR * p + o for p, o in zip(prior, observados)]
    total = sum(posterior)
    return tuple(valor / total for valor in posterior)


def montar_tabela_probabilidades(
    historico: list[dict],
) -> dict[str, Probabilidades]:
    """Probabilidades por partida, indexadas por quem joga de brancas."""
    return {
        brancas: calcular_probabilidades(historico, brancas)
        for brancas in JOGADORES
    }


def sortear_pontos(probabilidades: Probabilidades,
                   rng: random.Random) -> float:
    """Sorteia o resultado de uma partida e devolve os pontos de Sindarov."""
    vitoria, empate, _ = probabilidades
    sorteio = rng.random()
    if sorteio < vitoria:
        return 1.0
    if sorteio < vitoria + empate:
        return 0.5
    return 0.0


# ---------------------------------------------------------------- simulação

def simular_match(historico: list[dict], n_simulacoes: int,
                  rng: random.Random) -> dict:
    """Monte Carlo do match, partindo do placar atual do Mundial.

    As cores alternam a partir de BRANCAS_PARTIDA_1 (config.py).
    """
    tabela = montar_tabela_probabilidades(historico)
    partidas_match = [p for p in historico if p["evento"] == EVENTO_MUNDIAL]
    placar_inicial = sum(calcular_pontos_sindarov(p) for p in partidas_match)
    jogadas_inicial = len(partidas_match)

    titulos = Counter()
    placares = Counter()
    for _ in range(n_simulacoes):
        pontos_sindarov = placar_inicial
        jogadas = jogadas_inicial
        while jogadas < PARTIDAS_MATCH:
            pontos_gukesh = jogadas - pontos_sindarov
            if max(pontos_sindarov, pontos_gukesh) >= PONTOS_TITULO:
                break
            if jogadas % 2 == 0:
                cor = BRANCAS_PARTIDA_1
            else:
                cor = obter_adversario(BRANCAS_PARTIDA_1)
            pontos_sindarov += sortear_pontos(tabela[cor], rng)
            jogadas += 1
        pontos_gukesh = jogadas - pontos_sindarov
        placares[(pontos_sindarov, pontos_gukesh)] += 1
        if pontos_sindarov >= PONTOS_TITULO:
            titulos[SINDAROV] += 1
        elif pontos_gukesh >= PONTOS_TITULO:
            titulos[GUKESH] += 1
        else:
            titulos[EMPATE] += 1

    return {
        "tabela": tabela,
        "placar_atual": (placar_inicial, jogadas_inicial - placar_inicial),
        "jogadas": jogadas_inicial,
        "titulos": titulos,
        "placares": placares,
        "n": n_simulacoes,
    }


# ---------------------------------------------------------------- saída

def formatar_pontos(valor: float) -> str:
    inteiro = int(valor)
    if valor - inteiro != 0.5:
        return str(inteiro)
    return f"{inteiro}½" if inteiro else "½"


def exibir_simulacao(resultado: dict) -> None:
    n = resultado["n"]
    tabela = resultado["tabela"]
    titulos = resultado["titulos"]
    sindarov, gukesh = resultado["placar_atual"]
    print(f"Ratings: Sindarov {RATINGS[SINDAROV]} | "
          f"Gukesh {RATINGS[GUKESH]}")
    print(f"Placar atual do Mundial: Sindarov {formatar_pontos(sindarov)} x "
          f"{formatar_pontos(gukesh)} Gukesh "
          f"({resultado['jogadas']}/{PARTIDAS_MATCH} partidas)\n")

    print("Probabilidades por partida clássica "
          "(vitória Sindarov / empate / vitória Gukesh):")
    for cor in JOGADORES:
        vitoria, empate, derrota = tabela[cor]
        print(f"  {cor} de brancas: "
              f"{vitoria:6.1%} / {empate:6.1%} / {derrota:6.1%}")

    print(f"\nResultado de {n:,} simulações:".replace(",", "."))
    for jogador in JOGADORES:
        print(f"  {jogador} campeão: {titulos[jogador] / n:6.1%}")
    metade = formatar_pontos(PARTIDAS_MATCH / 2)
    print(f"  Empate ({metade} x {metade}): {titulos[EMPATE] / n:6.1%}")

    print("\nPlacares (todos, do mais provável ao menos):")
    for (pontos_s, pontos_g), contagem in resultado["placares"].most_common():
        print(f"  Sindarov {formatar_pontos(pontos_s):>3} x "
              f"{formatar_pontos(pontos_g):<3} Gukesh  {contagem / n:6.1%}")


# ---------------------------------------------------------------- main

def main() -> None:
    historico = carregar_historico()
    resultado = simular_match(historico, N_SIMULACOES, random.Random())
    exibir_simulacao(resultado)


if __name__ == "__main__":
    main()
