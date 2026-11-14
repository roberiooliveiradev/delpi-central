#!/usr/bin/env python3
"""Cruzamento mensal das entradas: SF1/SD1/SF4 do Protheus × XML de NF-e e CT-e.

Uso:
  python auditoria.py --xml <zip|pasta|xml> [--xml ...] --sf1 SF1.xlsx [--sd1 SD1.xlsx] [--sf4 SF4.xlsx]
                      [--filial 02] [--cnpj 00000000000000] [--out /mnt/user-data/outputs]

Sem --sf4, usa a SF4 guardada na skill (references/sf4/SF4.csv), se existir.
"""
import argparse, datetime as dt, json, os, sys, warnings
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from leitura import read_protheus, read_xmls, txt
from regras import analisar, sft_colunas, SF1_NUM, SD1_NUM
from relatorio import gerar, MESES

SF4_DIR = os.path.join(os.path.dirname(HERE), 'references', 'sf4')
SF4_IDADE_AVISO = 90  # dias

ap = argparse.ArgumentParser()
ap.add_argument('--xml', action='append', required=True)
ap.add_argument('--sf1', required=True); ap.add_argument('--sd1'); ap.add_argument('--sf4')
ap.add_argument('--sft', help='livro fiscal por item (SFT): decide o crédito pelo que foi de fato para o livro/SPED')
ap.add_argument('--sem-sf4', action='store_true', help='ignora a SF4 guardada na skill (aba TES a confirmar)')
ap.add_argument('--filial'); ap.add_argument('--uf', help='força a UF da empresa'); ap.add_argument('--tes-presumido', default='004', help='TES do crédito presumido de 7%% de SC (padrão 004)'); ap.add_argument('--cfop-frete', default='352', help='final do CFOP de entrada do CT-e (padrão 352: estabelecimento industrial)'); ap.add_argument('--cnpj'); ap.add_argument('--out', default='/mnt/user-data/outputs')
a = ap.parse_args()

notas, ign, ctes = read_xmls(a.xml)
sf1 = read_protheus(a.sf1, SF1_NUM)
sd1 = read_protheus(a.sd1, SD1_NUM) if a.sd1 else None
if sd1 is not None and 'Item NF' not in sd1.columns: sys.exit('O arquivo informado em --sd1 não parece ser a SD1 (falta a coluna "Item NF").')
if 'Chave NFe' not in sf1.columns: sys.exit('O arquivo informado em --sf1 não parece ser a SF1 (falta a coluna "Chave NFe").')

# ---------- SF4: a enviada agora ou a guardada na skill
sf4, sf4_fonte, sf4_avisos = None, 'SF4 não informada', []
if a.sf4:
    sf4 = read_protheus(a.sf4)
    if 'Cred. ICMS ?' not in sf4.columns: sys.exit('O arquivo informado em --sf4 não parece ser a SF4 (falta a coluna "Cred. ICMS ?").')
    sf4_fonte = f'SF4 enviada nesta execução ({os.path.basename(a.sf4)})'
elif not a.sem_sf4 and os.path.exists(os.path.join(SF4_DIR, 'SF4.csv')):
    sf4 = read_protheus(os.path.join(SF4_DIR, 'SF4.csv'))
    info = {}
    try: info = json.load(open(os.path.join(SF4_DIR, 'sf4_info.json'), encoding='utf-8'))
    except Exception: pass
    d = info.get('data_extracao', '')
    sf4_fonte = f'SF4 guardada na skill, extraída em {dt.date.fromisoformat(d):%d/%m/%Y}' if d else 'SF4 guardada na skill (data de extração desconhecida)'
    if d:
        idade = (dt.date.today() - dt.date.fromisoformat(d)).days
        if idade > SF4_IDADE_AVISO:
            sf4_avisos.append(f'A SF4 guardada tem {idade} dias. Se alguma TES foi criada ou editada desde então, reenviar a SF4.')

sft, sft_fonte = None, 'SFT não informada: crédito decidido pela TES'
if a.sft:
    sft = read_protheus(a.sft)
    mp, falta = sft_colunas(sft)
    if falta: sys.exit(f'O arquivo informado em --sft não tem as colunas {falta}. Colunas encontradas: {list(sft.columns)}. Acrescente o título em SFT_COLS (regras.py).')
    if sd1 is None: sys.exit('A SFT só é usada com a SD1 (--sd1).')
    sft_fonte = f'Crédito decidido pelo livro fiscal (SFT: {os.path.basename(a.sft)})'

R = analisar(notas, sf1, sd1, sf4, filial=a.filial, cnpj=a.cnpj, uf=a.uf, tes_presumido=a.tes_presumido, sft=sft, ctes=ctes, cfop_frete=a.cfop_frete)
R['sft_fonte'] = sft_fonte + '.'


# TES usadas na SD1 que não existem na SF4 (TES nova, criada depois da extração)
if sf4 is not None and R.get('meta'):
    cad = {txt(c) for c in sf4['Cod. do Tipo']}
    usadas = sorted({txt(t) for t in R['meta']['tesdf']['Tipo Entrada'] if txt(t)})
    faltam = [t for t in usadas if t not in cad]
    inco = [f"{t} ({'; '.join(R['tes'].incoerencias(t))})" for t in usadas if R['tes'].incoerencias(t)]
    if inco and sft is None:
        sf4_avisos.append(f'TES com crédito e livro fiscal desencontrados usada(s) no período: {", ".join(inco)}. Sem a SFT não dá para afirmar o que foi para o SPED.')
    if faltam:
        sf4_avisos.append(f'TES usada(s) no período e ausente(s) da SF4: {", ".join(faltam)}. Os itens dessas TES ficam como "Depende da TES"; reenviar a SF4 atualizada.')
R['sf4_fonte'] = sf4_fonte; R['sf4_avisos'] = sf4_avisos

os.makedirs(a.out, exist_ok=True)
per = f"{MESES[R['ini'].month-1]}{R['ini'].year}"
out = os.path.join(a.out, f"cruzamento_entradas_filial{R['filial']}_{per}.xlsx")
gerar(R, out)
for line in R['log']: print(line)
print(sf4_fonte); print(sft_fonte)
for w in sf4_avisos: print('AVISO SF4:', w)
print(f'XML NF-e lidos: {len(notas)} | CT-e: {len(ctes)} (ignorados: {ign}) | NF-e casadas: {R["nm"]} | CT-e casados: {R["nctm"]} | só XML: {len(R["sox"])} | só SF1: {len(R["sos"])}')
if R['sup']: print('Não apontado (regra do usuário):', dict(R['sup']))
import collections
print('Cabeçalho:', dict(collections.Counter(d['sev'] for d in R['div'])))
if R['meta']: print('Itens:', dict(collections.Counter(d['sev'] for d in R['idiv'])))
print('SAIDA=' + out)
