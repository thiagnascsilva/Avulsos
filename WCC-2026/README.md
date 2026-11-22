Last updated: Sunday, November 22, 2026.

# WCC 2026

Monte Carlo simulation of the 2026 World Chess Championship match between Gukesh Dommaraju and Javokhir Sindarov.
It estimates each player's chance of winning the title, starting from the current score of the match.

## Requirements

- Python 3.10+ (standard library only)

## Usage

```
python simular_sindarov_gukesh.py [--semente N] [--brancas-jogo1 PLAYER]
```

- `--semente`: random seed, for reproducible runs.
- `--brancas-jogo1`: who has White in game 1 (`Sindarov` or `Gukesh`). Only used while no match game is recorded;
  after that, the colors come from game 1 in the history. Without it, the colors are drawn at random in each
  simulation.

Each run plays 100,000 simulated matches (`N_SIMULACOES` in `config.py`).

## Files

| File | Contents |
|---|---|
| `simular_sindarov_gukesh.py` | Reads the history, runs the simulation and prints the result. |
| `config.py` | FIDE ratings, match rules, number of simulations and head-to-head weights. |
| `elo_model.py` | Elo model for a single classical game, including the draw-rate formula. |
| `historico_sindarov_gukesh.json` | Classical head-to-head games, including the match games. |
| `evolucao_probabilidades.csv` | Title chances after each match game, kept by hand for charting. |

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

**Match.** Recorded match games make up the starting score, and only the remaining games are simulated. Colors
alternate from game 1. A player wins the title at 7½ points. At 7–7 the match counts as drawn, because the tiebreak
is not simulated.

## Naming convention

Standardization per: [Padronizacao](https://github.com/thiagnascsilva/Padronizacao) (in Portuguese).
