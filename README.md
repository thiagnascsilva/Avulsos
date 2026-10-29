Last updated: Thursday, October 29, 2026.

# Avulsos

Standalone scripts, one per file.

## Naming convention

The code follows [PEP 8](https://peps.python.org/pep-0008/), with names in Portuguese.

| Kind | Format | Example |
|---|---|---|
| Variable | `snake_case`, a noun | `total_projetado` |
| Function | `snake_case`, starting with an infinitive verb | `projetar_votos()` |
| Constant | `UPPER_CASE`, at the top of the module | `INTERVALO = 10` |
| Module/file | short `snake_case` | `tse_eleicoes.py` |
| Boolean | `is_` or `tem_` prefix | `is_eleito`, `tem_cache` |
| Internal use | `_` prefix | `_sessao`, `_baixar_json()` |
| Python special name | `__dunder__` | `__name__` |

- Avoid `camelCase` (`votosPorNumero`) in functions and variables.
- `_name` marks an internal detail that should not be used from outside. It is only a convention: Python does not enforce it.
- `__name__` is reserved for Python's special names: it is not private, and new ones are not created.
- Code that runs goes in `def main():`, called by `if __name__ == "__main__": main()`. The top of the file holds only imports, constants and functions.
- Type hints where they help readability: `def formatar_percentual(parte: int, total: int) -> str:`.

To check the names:

```
ruff check --select N .
```

## tse_eleicoes.py

Follows the vote count of Brazil's 2026 presidential election live in the terminal, reading the public files published by the TSE, Brazil's Superior Electoral Court
([resultados.tse.jus.br](https://resultados.tse.jus.br)).

### Requirements

- Python 3.10+
- `requests` 2.34+

```
pip install -r requirements.txt
```

### Usage

```
python tse_eleicoes.py [round]
```

`round` can be `1` or `2`. Without the argument, it shows the second round.

The screen refreshes every 10 seconds (constant `INTERVALO`) until the count reaches 100%. Press Ctrl+C to exit.

### What it shows

- **Candidates:** votes, percentage, projected votes, how many votes the leader still needs to be mathematically
  elected (second round only), and the status reported by the TSE.
- **By state:** percentage of polling sections counted and each candidate's share, with each row colored by the leading
  candidate and a flag when a candidate has mathematically won the state. The closest race and each candidate's
  largest lead are highlighted.
- **By region:** the same percentages, aggregated over the states in each region (excluding votes cast abroad).
- **Final result:** when the TSE declares the winner.

### How it works

**Projection.** The votes still to be counted are distributed as if they will follow the proportion each candidate
has received so far. This is done separately for each state (and for votes cast abroad), then summed for the national
projection. For a state with no sections counted yet, it uses the turnout and vote split from the first round.

**Mathematical win.** For each state and for the national total, the script checks whether a candidate has already
won mathematically, that is, whether their lead is larger than all the votes still left to count, so no outcome of the
remaining votes could change the result.

First-round data, already final, is downloaded once and cached in the system's temporary folder (`tse_ele2026`).
