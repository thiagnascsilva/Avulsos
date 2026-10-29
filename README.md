Atualizado em: Quinta-feira, 29/10/2026.

# Avulsos

Scripts avulsos, um por arquivo.

## Convenção de nomes

O código segue a [PEP 8](https://peps.python.org/pep-0008/), com os nomes em português.

| Tipo | Formato | Exemplo |
|---|---|---|
| Variável | `snake_case`, substantivo | `total_alunos` |
| Função | `snake_case`, começando por verbo no infinitivo | `calcular_media()` |
| Constante | `MAIÚSCULAS`, no topo do módulo | `TAXA_JUROS = 0.05` |
| Classe | `PascalCase` | `QuestaoProva` |
| Módulo/arquivo | `snake_case` curto | `estatistica.py` |
| Booleano | prefixo `is_` ou `tem_` | `is_valido`, `tem_gabarito` |
| Uso interno | prefixo `_` | `_cache`, `_somar()` |
| Nome especial do Python | `__dunder__` | `__init__` |

- Evite `camelCase` (`votosPorNumero`) em funções e variáveis.
- `_nome` indica detalhe interno, que não deve ser usado de fora. É só convenção: o Python não bloqueia.
- `__nome__` é reservado para os nomes especiais do Python: não é privado, e não se criam novos.
- O código que executa fica em `def main():`, chamado por `if __name__ == "__main__": main()`. No topo do arquivo ficam imports, constantes e funções.
- Type hints quando ajudarem a leitura: `def calcular_media(notas: list[float]) -> float:`.

Para conferir os nomes:

```
ruff check --select N .
```

## tse_eleicoes.py

Acompanha no terminal a apuração da eleição para Presidente de 2026, lendo os arquivos públicos do TSE
([resultados.tse.jus.br](https://resultados.tse.jus.br)).

### Requisitos

- Python 3.10+
- `requests` 2.34+

```
pip install -r requirements.txt
```

### Uso

```
python tse_eleicoes.py [turno]
```

`turno` pode ser `1` ou `2`. Sem o argumento, mostra o 2º turno.

A tela é atualizada a cada 10 segundos (constante `INTERVALO`) até a apuração chegar a 100%. Ctrl+C para sair.

### O que mostra

- **Candidatos:** votos, percentual, projeção de votos, quanto falta para o 1º colocado ser eleito
  matematicamente (só no 2º turno) e a situação informada pelo TSE.
- **Por estado:** percentual de seções apuradas e de cada candidato, com a linha colorida pela cor de quem lidera
  e a indicação de quando um candidato já ganhou o estado matematicamente. Ficam destacados o estado com a disputa
  mais acirrada e o de maior vantagem de cada candidato.
- **Por região:** os mesmos percentuais, somando os estados de cada região (sem o exterior).
- **Resultado definitivo:** quando o TSE declara o eleito.

### Projeção

Em cada estado (e no exterior), os votos que ainda faltam apurar são divididos na proporção que cada candidato tem
até agora naquele estado. Em estado sem nenhuma seção apurada, usa o comparecimento e a divisão de votos do 1º turno.

Os dados do 1º turno, já encerrado, são baixados uma vez e guardados na pasta temporária do sistema (`tse_ele2026`).
