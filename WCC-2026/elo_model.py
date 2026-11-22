"""Modelo Elo para uma partida clássica: vitória, empate e derrota."""

VANTAGEM_BRANCAS = 35   # bônus de Elo para quem joga de brancas

# Taxa de empate, calculada a partir dos ratings:
#   empate = BASE
#            + INCLINACAO_MEDIA * (média - REFERENCIA)
#            - QUEDA_DIFERENCA * |diferença|
# Empata-se mais quanto mais alto o nível e menos quanto maior a diferença
# (já com a vantagem das brancas). Calibrado para a elite: ~60% entre dois
# 2700 de mesmo rating, ~70% entre dois 2800.
EMPATE_BASE = 0.60
EMPATE_REFERENCIA = 2700
EMPATE_INCLINACAO_MEDIA = 0.001   # +0,1 p.p. por ponto de média
EMPATE_QUEDA_DIFERENCA = 0.0005   # -0,05 p.p. por ponto de diferença
EMPATE_LIMITES = (0.05, 0.85)


def calcular_taxa_empate(media: float, diferenca: float) -> float:
    """Probabilidade de empate a partir da média e da diferença de rating."""
    empate = (EMPATE_BASE
              + EMPATE_INCLINACAO_MEDIA * (media - EMPATE_REFERENCIA)
              - EMPATE_QUEDA_DIFERENCA * abs(diferenca))
    minimo, maximo = EMPATE_LIMITES
    return min(max(empate, minimo), maximo)


def calcular_probabilidades_elo(
    rating_jogador: float,
    rating_adversario: float,
    jogador_de_brancas: bool,
) -> tuple[float, float, float]:
    """(vitória, empate, derrota) do jogador contra o adversário."""
    media = (rating_jogador + rating_adversario) / 2
    diferenca = rating_jogador - rating_adversario
    if jogador_de_brancas:
        diferenca += VANTAGEM_BRANCAS
    else:
        diferenca -= VANTAGEM_BRANCAS
    esperado = 1 / (1 + 10 ** (-diferenca / 400))
    empate = calcular_taxa_empate(media, diferenca)
    vitoria = max(esperado - empate / 2, 0.01)
    derrota = max(1 - esperado - empate / 2, 0.01)
    total = vitoria + empate + derrota
    return vitoria / total, empate / total, derrota / total
