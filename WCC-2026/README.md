Last updated: Thursday, November 26, 2026.

# WCC 2026

Monte Carlo simulation of the 2026 World Chess Championship match between Gukesh and Sindarov.
It estimates each player's chance of winning the match in the classical format (14 classical games), starting from the
current score. Rapid and blitz tiebreaks are not simulated, so a 7–7 score counts as a drawn match.

## Requirements

- Python 3.10+ (standard library only for the simulation)
- matplotlib, only for the chart (`pip install matplotlib`)

## Usage

```
python simular_sindarov_gukesh.py
```

Each run plays 100,000 simulated matches (`N_SIMULACOES` in `config.py`).

To chart how the title chances changed over the match:

```
python plotar_evolucao_probabilidades.py
```

This reads `evolucao_probabilidades.csv` and saves `evolucao_probabilidades.png`.

## Files

| File | Contents |
|---|---|
| `simular_sindarov_gukesh.py` | Reads the history, runs the simulation and prints the result. |
| `config.py` | FIDE ratings, match rules, number of simulations and head-to-head weights. |
| `elo_model.py` | Elo model for a single classical game, including the draw-rate formula. |
| `historico_sindarov_gukesh.json` | Classical head-to-head games, including the match games. |
| `evolucao_probabilidades.csv` | Title chances after each match game, kept by hand for charting. |
| `plotar_evolucao_probabilidades.py` | Plots the CSV as a line chart. |
| `evolucao_probabilidades.png` | The chart, regenerated after each game. |

## After each match game

All updates are manual:

1. Add the game to the end of `historico_sindarov_gukesh.json`:

   ```json
   {
     "data": "2026-11",
     "evento": "Mundial 2026",
     "brancas": "Gukesh",
     "resultado": "1/2-1/2"
   }
   ```

   `data` is `YYYY-MM`, `brancas` is the player with White, and `resultado` is `1-0`, `0-1` or `1/2-1/2`.
   `evento` must be exactly `Mundial 2026` for the game to count in the match score.

2. Update the live ratings in `config.py`.
3. Run the script and add a row to `evolucao_probabilidades.csv` with the number of games played and the three
   percentages (Sindarov, Gukesh, drawn match).
4. Run `plotar_evolucao_probabilidades.py` to refresh the chart.

## What it shows

- Current ratings and match score.
- Probabilities for a single classical game (Sindarov win / draw / Gukesh win), with each player as White.
- Share of simulations won by each player, and share ending 7–7.
- The most likely final scores.

## How it works

**Single game (Elo).** The rating difference, plus 35 points for White, gives the expected score. The draw rate also
comes from the ratings: it rises with the average rating and falls as the difference grows. With equal ratings, it is
about 60% at 2700 and 70% at 2800. The coefficients are rough estimates for elite classical chess, not fitted to
data.

**Head-to-head.** The Elo probabilities count as 30 games of evidence (`FORCA_PRIOR`). The real classical games
between the two players are added on top, each weighted by age: a game loses half its weight every six months
(`MEIA_VIDA_ANOS`).

**Match.** Recorded match games make up the starting score, and only the remaining games are simulated. Sindarov
has White in game 1 (`BRANCAS_PARTIDA_1` in `config.py`) and colors alternate from there. A player wins the title at
7½ points. At 7–7 the match counts as drawn, because the tiebreak is not simulated.

## Naming convention

Standardization per: [Padronizacao](https://github.com/thiagnascsilva/Padronizacao) (in Portuguese).
