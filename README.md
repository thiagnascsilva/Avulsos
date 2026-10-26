# Avulsos

Scripts avulsos, um por arquivo.

## TSE_Eleicoes.py

Acompanha no terminal a apuração da eleição para Presidente de 2026, lendo os arquivos públicos do TSE
([resultados.tse.jus.br](https://resultados.tse.jus.br)).

### Requisitos

- Python 3
- `requests`

```
pip install -r requirements.txt
```

### Uso

```
python TSE_Eleicoes.py [turno]
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
