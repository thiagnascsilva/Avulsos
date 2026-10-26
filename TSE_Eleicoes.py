# Resultado de Presidente da eleição de 2026, direto dos arquivos públicos do TSE (resultados.tse.jus.br).
# Uso: python TSE_Eleicoes.py [turno]   (turno 1 ou 2; sem turno, mostra o 2º)
# Atualiza sozinho a cada INTERVALO segundos até a apuração chegar a 100%. Ctrl+C para sair.
import json
import os
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE = 'https://resultados.tse.jus.br/oficial/ele2026'
ELEICOES = {1: '6257', 2: '6258'}  # Eleição Ordinária Federal - 2026, cargo 0001 = Presidente
UFS = ['ac', 'al', 'am', 'ap', 'ba', 'ce', 'df', 'es', 'go', 'ma', 'mg', 'ms', 'mt', 'pa', 'pb', 'pe',
       'pi', 'pr', 'rj', 'rn', 'ro', 'rr', 'rs', 'sc', 'se', 'sp', 'to', 'zz']  # zz = exterior
ESTADOS = {'ac': 'no Acre', 'al': 'em Alagoas', 'am': 'no Amazonas', 'ap': 'no Amapá', 'ba': 'na Bahia',
           'ce': 'no Ceará', 'df': 'no Distrito Federal', 'es': 'no Espírito Santo', 'go': 'em Goiás',
           'ma': 'no Maranhão', 'mg': 'em Minas Gerais', 'ms': 'em Mato Grosso do Sul', 'mt': 'em Mato Grosso',
           'pa': 'no Pará', 'pb': 'na Paraíba', 'pe': 'em Pernambuco', 'pi': 'no Piauí', 'pr': 'no Paraná',
           'rj': 'no Rio de Janeiro', 'rn': 'no Rio Grande do Norte', 'ro': 'em Rondônia', 'rr': 'em Roraima',
           'rs': 'no Rio Grande do Sul', 'sc': 'em Santa Catarina', 'se': 'em Sergipe', 'sp': 'em São Paulo',
           'to': 'no Tocantins', 'zz': 'no exterior'}
REGIOES = {'Norte': ['ac', 'am', 'ap', 'pa', 'ro', 'rr', 'to'],
           'Nordeste': ['al', 'ba', 'ce', 'ma', 'pb', 'pe', 'pi', 'rn', 'se'],
           'Centro-Oeste': ['df', 'go', 'ms', 'mt'],
           'Sudeste': ['es', 'mg', 'rj', 'sp'],
           'Sul': ['pr', 'rs', 'sc']}
NOMES = {'22': 'BOLSONARO'}  # nome exibido no lugar do nome de urna do TSE
INTERVALO = 10  # segundos entre as atualizações
CORES = {'13': '\033[91m', '22': '\033[94m'}  # cor da linha do estado pelo número de quem lidera: Lula vermelho, Flávio azul

def numero(valor):
    return f'{int(valor):,}'.replace(',', '.')

# Uma sessão só, para reaproveitar a conexão (o handshake SSL é o que trava com o servidor do TSE sobrecarregado),
# e com novas tentativas quando o servidor demora ou falha.
sessao = requests.Session()
sessao.mount('https://', HTTPAdapter(pool_maxsize=8, max_retries=Retry(
    total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])))

# O 1º turno já está fechado: baixa uma vez e guarda no temp.
CACHE = os.path.join(tempfile.gettempdir(), 'tse_ele2026')

def baixa(turno, uf='br'):
    eleicao = ELEICOES[turno]
    arquivo = f'{uf}-c0001-e{int(eleicao):06d}-u.json'
    cache = os.path.join(CACHE, arquivo)
    if turno == 1 and os.path.exists(cache):
        with open(cache, encoding='utf-8') as f:
            return json.load(f)
    resposta = sessao.get(f'{BASE}/{eleicao}/dados/{uf}/{arquivo}', timeout=(10, 20))
    resposta.raise_for_status()
    dados = resposta.json()
    if turno == 1 and dados['s']['pst'] == '100,00':
        os.makedirs(CACHE, exist_ok=True)
        with open(cache, 'w', encoding='utf-8') as f:
            json.dump(dados, f)
    return dados

def votosPorNumero(dados):
    # {número do candidato: votos}
    return {cand['n']: int(cand['vap'])
            for agremiacao in dados['carg'][0]['agr'] for partido in agremiacao['par'] for cand in partido['cand']}

def projecaoEstado(atual, primeiro):
    # Votos que faltam no estado, divididos na proporção que cada candidato tem até agora no estado.
    # Estado sem nenhuma seção apurada: usa o 1º turno do estado (comparecimento em válidos e divisão entre os candidatos).
    votos = votosPorNumero(atual)
    eleitorado, apurado, validos = int(atual['e']['te']), int(atual['e']['est']), int(atual['v']['vv'])
    if validos > 0:
        faltam = (eleitorado - apurado) * validos / apurado
        base = votos
    else:
        faltam = eleitorado * int(primeiro['v']['vv']) / int(primeiro['e']['te'])
        base = {n: v for n, v in votosPorNumero(primeiro).items() if n in votos}
    total = sum(base.values())
    return {n: votos[n] + (faltam * base[n] / total if total else 0) for n in votos}

def projecao(turno):
    # {número do candidato: votos projetados}, somando a projeção de cada estado e do exterior,
    # e a lista de (uf, dados do estado) para a tabela por estado.
    with ThreadPoolExecutor(max_workers=8) as executor:
        atuais = list(executor.map(lambda uf: baixa(turno, uf), UFS))
        primeiros = list(executor.map(lambda uf: baixa(1, uf), UFS))
    soma = {}
    for atual, primeiro in zip(atuais, primeiros):
        for n, votos in projecaoEstado(atual, primeiro).items():
            soma[n] = soma.get(n, 0) + votos
    return soma, list(zip(UFS, atuais))

def percentual(parte, total):
    return f'{100 * parte / total:.2f}'.replace('.', ',') if total else '-'

def exibeEstados(estados, lista):
    # Uma linha por estado: % de seções, o % de cada candidato e a situação.
    # Ganhou matematicamente: a vantagem do líder é maior que o eleitorado das seções que faltam apurar.
    # Caixa no estado com a disputa mais acirrada e no de maior vantagem de cada candidato
    # (diferença entre os dois primeiros, sem o exterior).
    nomes = {n: nome for nome, n, *_ in lista}
    largura = 14 + 22 * len(lista) + 54
    linhas, diferencas = [], {}
    for i, (uf, atual) in enumerate(estados):
        votos = votosPorNumero(atual)
        validos = int(atual['v']['vv'])
        linha = f'{"EXT" if uf == "zz" else uf.upper():<4}{atual["s"]["pst"]:>10}'
        for _, n, *_ in lista:
            linha += f'{percentual(votos[n], validos):>22}'
        # Sem votos ou empate: sem cor e sem situação.
        ordem = sorted(votos.values(), reverse=True) + [0]
        lider = max(votos, key=votos.get) if validos and ordem[0] > ordem[1] else None
        faltam = int(atual['e']['te']) - int(atual['e']['est'])
        if lider and ordem[0] - ordem[1] > faltam:
            linha += f'  {nomes[lider]} ganhou {ESTADOS[uf]}.'
        if validos and uf != 'zz':
            diferencas[i] = ((ordem[0] - ordem[1]) / validos, lider)
        linhas.append((f'{linha:<{largura}}', CORES.get(lider, '')))

    # Se a mesma linha ganhar duas caixas, os rótulos são juntados.
    caixas = {}
    def marca(i, rotulo):
        caixas[i] = f'{caixas[i]} / {rotulo}' if i in caixas else rotulo
    for nome, n, *_ in lista:
        liderados = [i for i, (_, lider) in diferencas.items() if lider == n]
        if liderados:
            marca(max(liderados, key=lambda i: diferencas[i][0]), f'Maior vantagem {nome.split()[-1].title()}')
    if diferencas:
        marca(min(diferencas, key=lambda i: diferencas[i][0]), 'Disputa mais acirrada')

    print('\nPOR ESTADO')
    print(f' {"UF":<4}{"Seções %":>10}' + ''.join(f'{nome[:20]:>22}' for nome, *_ in lista) + '  Situação')
    print(' ' + '-' * largura)
    for i, (linha, cor) in enumerate(linhas):
        texto = f'{cor}{linha}\033[0m' if cor else linha
        if i in caixas:
            rotulo = f'─ {caixas[i]} '
            print('┌' + rotulo + '─' * (largura - len(rotulo)) + '┐')
            print('│' + texto + '│')
            print('└' + '─' * largura + '┘')
        else:
            print(' ' + texto)

def exibeRegioes(estados, lista):
    # Uma linha por região, somando os estados (sem o exterior): % de seções e o % de cada candidato.
    porUf = dict(estados)
    print('\nPOR REGIÃO')
    print(f' {"Região":<14}{"Seções %":>10}' + ''.join(f'{nome[:20]:>22}' for nome, *_ in lista))
    print(' ' + '-' * (24 + 22 * len(lista)))
    for regiao, ufs in REGIOES.items():
        votos, validos, secoes, totalSecoes = {}, 0, 0, 0
        for uf in ufs:
            atual = porUf[uf]
            for n, v in votosPorNumero(atual).items():
                votos[n] = votos.get(n, 0) + v
            validos += int(atual['v']['vv'])
            secoes += int(atual['s']['st'])
            totalSecoes += int(atual['s']['ts'])
        linha = f'{regiao:<14}{percentual(secoes, totalSecoes):>10}'
        for _, n, *_ in lista:
            linha += f'{percentual(votos[n], validos):>22}'
        # Sem votos ou empate: sem cor.
        ordem = sorted(votos.values(), reverse=True) + [0]
        lider = max(votos, key=votos.get) if validos and ordem[0] > ordem[1] else None
        cor = CORES.get(lider, '')
        print(' ' + (f'{cor}{linha}\033[0m' if cor else linha))

def candidatos(dados):
    # Os candidatos ficam dentro de agremiação > partido > cand.
    lista = []
    for agremiacao in dados['carg'][0]['agr']:
        for partido in agremiacao['par']:
            for cand in partido['cand']:
                lista.append((NOMES.get(cand['n'], cand['nmu']), cand['n'], int(cand['vap']), cand['pvap'], cand['st']))
    return sorted(lista, key=lambda c: c[2], reverse=True)

def exibe(dados, projetados, estados):
    totalProjetado = sum(projetados.values())
    lista = candidatos(dados)
    s = dados['s']
    print(f'Seções totalizadas: {s["pst"]}%  ({numero(s["st"])} de {numero(s["ts"])})\n')

    # Votos que o 1º colocado ainda precisa para ser eleito matematicamente (só no 2º turno): no pior caso, todo o
    # eleitorado das seções que faltam vota e o que não for dele vai para o 2º colocado. Precisa de x votos com
    # líder + x > segundo + (faltam - x).
    faltam = int(dados['e']['te']) - int(dados['e']['est'])
    if dados['t'] == '2' and len(lista) > 1:
        precisa = numero(max(0, (lista[1][2] + faltam - lista[0][2]) // 2 + 1))
    else:
        precisa = '-'

    print(f'{"Candidato":<25}{"Votos":>14}{"%":>8}{"Projeção":>14}{"%":>8}{"Falta p/ eleger":>18}  Situação')
    print('-' * 104)
    for i, (nome, n, votos, perc, situacao) in enumerate(lista):
        percProjetado = f'{100 * projetados[n] / totalProjetado:.2f}'.replace('.', ',')
        print(f'{nome:<25}{numero(votos):>14}{perc:>8}'
              f'{numero(round(projetados[n])):>14}{percProjetado:>8}{precisa if i == 0 else "":>18}  {situacao}')

    print('-' * 104)

    exibeEstados(estados, lista)
    exibeRegioes(estados, lista)

turno = int(sys.argv[1]) if len(sys.argv) > 1 else 2
try:
    while True:
        # Baixa tudo antes de limpar a tela, para não ficar em branco enquanto o TSE responde.
        try:
            dados = baixa(turno)
            projetados, estados = projecao(turno)
        except requests.RequestException as erro:
            print(f'\nFalha ao baixar do TSE ({type(erro).__name__}), tentando de novo em {INTERVALO} s.')
        else:
            os.system('cls' if os.name == 'nt' else 'clear')
            exibe(dados, projetados, estados)
            # Resultado definitivo: o TSE marca o candidato como Eleito (matematicamente garantido).
            eleitos = [nome for nome, *_, situacao in candidatos(dados) if situacao.startswith('Eleito')]
            if eleitos:
                print(f'\nRESULTADO DEFINITIVO: {eleitos[0]} ELEITO.')
            if dados['s']['pst'] == '100,00':
                print('\nApuração encerrada.')
                break
        time.sleep(INTERVALO)
except KeyboardInterrupt:
    pass
