RATINGS = {
    "Sindarov": 2779,
    "Gukesh": 2713,
}

# Match
# Partidas com este evento entram no placar do match.
EVENTO_MUNDIAL = "Mundial 2026"
PARTIDAS_MATCH = 14
BRANCAS_PARTIDA_1 = "Sindarov"   # cores alternam a partir daqui
PONTOS_TITULO = 7.5

# Simulação
N_SIMULACOES = 100_000

# Confronto direto
FORCA_PRIOR = 30.0      # peso dos ratings, em "partidas equivalentes"
MEIA_VIDA_ANOS = 0.5    # um confronto perde metade do peso a cada 6 meses
