"""Regras do cruzamento SF1/SD1 (Protheus) × XML de NF-e, com a configuração das TES (SF4)."""
import collections
import pandas as pd
from leitura import txt, to_date

TOL = 0.05
SEVO = {'Alta': 0, 'Depende da TES': 1, 'Média': 2, 'Baixa': 3, 'Info': 4, 'OK': 5}
CRTN = {'1': 'Simples Nacional', '2': 'Simples (excesso)', '3': 'Regime normal', '4': 'MEI'}
INSUMO = {'101', '102', '401', '403', '151', '152', '122', '124', '125', '126'}
CONSUMO_ATIVO = ('551', '556', '407', '406', '653')
SALE = set('101 102 103 104 105 106 107 108 109 110 111 112 113 114 115 116 117 118 119 120 122 123 124 125 401 402 403 404 405 651 652 653 654 655 656 929 922'.split())
SALE_IN = set('101 102 111 113 116 117 118 120 121 122 124 125 126 128 401 403 406 407 551 556 651 652 653'.split())
TRF = set('151 152 153 155 156 408 409 552 557 659'.split()); TRF_IN = set('151 152 153 154 155 156 408 409 552 557 658 659'.split())
DEV = set('201 202 203 204 205 206 207 208 209 210 410 411 412 413 503 553 555 556 660 661 662 918 919'.split())
DEV_IN = set('201 202 203 204 208 209 410 411 503 553 554 555 660 661 662 918 919'.split())
GRP = [(SALE, SALE_IN, 'compra'), (TRF, TRF_IN, 'transferência'), (DEV, DEV_IN, 'devolução'),
       ({'915', '916'}, {'915', '916'}, 'conserto'),
       ({'901', '902', '903', '924', '925'}, {'901', '902', '903', '924', '925', '949'}, 'industrialização por encomenda'),
       ({'910'}, {'910'}, 'bonificação'), ({'911'}, {'911'}, 'amostra grátis'), ({'920', '921'}, {'920', '921'}, 'vasilhame/sacaria'),
       ({'912', '913'}, {'912', '913'}, 'demonstração'), ({'908', '909'}, {'908', '909'}, 'comodato')]
STCST = {'10', '30', '60', '61', '70'}; STCSOSN = {'201', '202', '203', '500'}
SF1_NUM = ['Vlr.Frete', 'Vlr.Despesas', 'Base p/ICMS', 'Vlr.ICMS', 'Base p/IPI', 'Vlr.IPI', 'Vlr.Mercad', 'Vlr.Bruto', 'Descontos', 'Base ICM Sol', 'ICMS Solid.', 'Vlr.Seguro']
SD1_NUM = ['Quantidade', 'Vlr.Unitario', 'Vlr.Total', 'Base Icms', 'Aliq. ICMS', 'Vlr.ICMS', 'Vlr.Base IPI', 'Aliq. IPI', 'Vlr.IPI', 'ICMS Solid.', 'Desconto']
EXCL = {'352': 'CT-e (frete), conferido na aba CT-e Comparativo', '933': 'Nota de serviço (ISS)', '302': 'NFCom (comunicação)', '301': 'NFCom (comunicação)', '252': 'NF3e (energia elétrica)', '251': 'NF3e (energia elétrica)', '253': 'NF3e (energia elétrica)'}
ESPEC = {'CTE': 'CT-e (frete), conferido na aba CT-e Comparativo', 'CTEOS': 'CT-e (frete), conferido na aba CT-e Comparativo', 'NFS': 'Nota de serviço (ISS)', 'NFSE': 'Nota de serviço (ISS)', 'RPS': 'Nota de serviço (ISS)',
         'NFCOM': 'NFCom (comunicação)', 'NF3E': 'NF3e (energia elétrica)', 'NFCE': 'NFC-e (cupom)'}

# Tabelas do Simples Nacional (LC 123, Anexos I e II, redação da LC 155/2016): (limite RBT12, alíq. nominal, parcela a deduzir, % do ICMS na partilha)
ANEXO = {
    'I':  [(180000, .040, 0, .34), (360000, .073, 5940, .34), (720000, .095, 13860, .335), (1800000, .107, 22500, .335), (3600000, .143, 87300, .335)],
    'II': [(180000, .045, 0, .32), (360000, .078, 5940, .32), (720000, .100, 13860, .32), (1800000, .112, 22500, .32), (3600000, .147, 85500, .32)],
}
SUBLIMITE = 3600000          # sublimite estadual de ICMS (RBT12)
ALERTA_SUBLIMITE = 3000000   # a partir daqui, avisa que o fornecedor está perto do sublimite
IND = {'101', '103', '105', '109', '401'}   # CFOPs de saída de produção própria (indicam indústria)
PRESUMIDO = dict(uf='SC', pct=0.07, tes='004')   # RICMS/SC, Anexo 2, art. 15, XXVI
COMB_NCM = ('2710', '2711', '2207', '3826')      # combustíveis e lubrificantes (CST 060 no Protheus é o padrão da empresa)
COMB_CFOP = {'653', '656', '667', '661', '662', '663', '664'}
NAT = {'consumo': {'556', '407', '653'}, 'ativo': {'551', '406'}, 'insumo/revenda': {'101', '102', '401', '403', '122', '124', '125', '126'}}
MODELO = {'55': ({'SPED', 'NFE', 'NF-E'}, 'SPED (NF-e)'), '57': ({'CTE', 'CT-E'}, 'CTE'), '67': ({'CTEOS'}, 'CTEOS'),
          '66': ({'NF3E'}, 'NF3E (energia elétrica)'), '62': ({'NFCOM'}, 'NFCOM (comunicação)'), '65': ({'NFCE'}, 'NFCE')}
ESPEC_ELETR = {'SPED', 'NFE', 'CTE', 'CTEOS', 'NF3E', 'NFCOM', 'NFCE'}

def dv_ok(ch):
    """Confere o dígito verificador (módulo 11) da chave de acesso."""
    if len(ch) != 44 or not ch.isdigit(): return False
    soma, peso = 0, 2
    for d in reversed(ch[:43]):
        soma += int(d) * peso; peso = 2 if peso == 9 else peso + 1
    dv = 11 - soma % 11
    return (0 if dv >= 10 else dv) == int(ch[43])

def fcnpj(c):
    c = ''.join(ch for ch in txt(c) if ch.isdigit())
    return f'{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:]}' if len(c) == 14 else c

def brl(v):
    return f'{v:,.2f}'.replace(',', '#').replace('.', ',').replace('#', '.')

def _ser(v):
    v = txt(v).upper().lstrip('0'); return v or '0'

def combustivel(z):
    return bool(z) and (z['ncm'].startswith(COMB_NCM) or z['cfop'][1:] in COMB_CFOP or z['cst'] == '61')

def sn_faixa(p, anexo):
    """Recebe o pCredSN (em %) e devolve (teto do anexo em %, RBT12 estimada do fornecedor ou None)."""
    tab = ANEXO[anexo]; p = p / 100
    teto = (tab[-1][1] - tab[-1][2] / tab[-1][0]) * tab[-1][3]
    if p > teto + 0.00005: return teto * 100, None
    lo = 0
    for lim, nom, pd_, sh in tab:
        ef_lo = (nom - pd_ / lo) * sh if lo else nom * sh
        ef_hi = (nom - pd_ / lim) * sh
        if p <= ef_hi + 0.00005:
            if pd_ == 0 or p <= ef_lo: return teto * 100, (lo + lim) / 2 if pd_ == 0 else lo
            return teto * 100, pd_ / (nom - p / sh)
        lo = lim
    return teto * 100, SUBLIMITE

def sevmin(lst):
    return min(lst, key=lambda s: SEVO[s]) if lst else 'OK'

class TES:
    def __init__(self, sf4):
        self.ok = sf4 is not None
        self.f4 = {}
        if self.ok:
            for _, r in sf4.iterrows():
                c = txt(r.get('Cod. do Tipo'))
                if c: self.f4[c] = {k: txt(v) for k, v in r.items()}
    def g(self, t, c): return self.f4.get(t, {}).get(c, '')
    def incoerencias(self, t):
        """Crédito e livro fiscal desencontrados na TES: aí a TES sozinha não diz o que vai para o SPED."""
        if t not in self.f4: return []
        out = []
        ci, li = self.g(t, 'Cred. ICMS ?'), self.g(t, 'L.Fisc. ICMS')
        if self.g(t, 'Calcula ICMS') == 'Sim':
            if ci == 'Sim' and li != 'Tributado': out.append(f'ICMS: credita, mas livro {li or "vazio"}')
            if ci == 'Nao' and li == 'Tributado': out.append('ICMS: não credita, mas livro Tributado')
        cp, lp = self.g(t, 'Credita IPI?'), self.g(t, 'L.Fiscal IPI')
        if self.g(t, 'Calcula IPI?') == 'Sim':
            if cp == 'Sim' and lp != 'Tributado': out.append(f'IPI: credita, mas livro {lp or "vazio"}')
            if cp == 'Nao' and lp == 'Tributado': out.append('IPI: não credita, mas livro Tributado')
        return out
    def incoerente_icms(self, t): return any(x.startswith('ICMS') for x in self.incoerencias(t))
    def credita(self, t):
        """True/False pela TES; None se não há SF4, a TES não está nela ou crédito e livro estão desencontrados."""
        if not self.ok or t not in self.f4 or self.incoerente_icms(t): return None
        return self.g(t, 'Cred. ICMS ?') == 'Sim'
    def credita_ipi(self, t):
        if not self.ok or t not in self.f4 or any(x.startswith('IPI') for x in self.incoerencias(t)): return None
        return self.g(t, 'Credita IPI?') == 'Sim'
    def desc(self, t):
        return f"TES {t} ({self.g(t,'Txt Padrao')}): Calcula ICMS {self.g(t,'Calcula ICMS')}, Credita ICMS {self.g(t,'Cred. ICMS ?')}, livro {self.g(t,'L.Fisc. ICMS')}."

# Livro fiscal por item (SFT). O relatório do Protheus pode vir com o título do campo ou com o nome
# técnico (FT_xxx); os apelidos abaixo cobrem os dois. Se a SFT vier com outro título, acrescente aqui.
SFT_COLS = {
    'filial': ['Filial', 'FT_FILIAL'],
    'tipomov': ['Tipo Movim.', 'Tp. Movim.', 'Tipo Mov.', 'Tipo Movimento', 'Tp Movimento', 'Entrada/Saida', 'FT_TIPOMOV'],
    'doc': ['Nota Fiscal', 'Documento', 'No. Documento', 'Num. Docto', 'Num.Docto.', 'Numero', 'Nro. Nota', 'Doc. Fiscal', 'FT_NFISCAL'],
    'serie': ['Serie', 'Serie NF', 'Serie Docto', 'FT_SERIE'],
    'clifor': ['Cli/For', 'Cli/Forn', 'Cliente/Forn', 'Cliente/Fornec', 'Cod. Cli/For', 'Fornecedor', 'Forn/Cliente', 'FT_CLIEFOR'],
    'loja': ['Loja', 'FT_LOJA'],
    'item': ['Item', 'Item NF', 'Item Docto', 'Item Nota', 'FT_ITEM'],
    'chave': ['Chave NFe', 'Chave NF-e', 'Chave Nfe', 'FT_CHVNFE'],
    'valicm': ['Valor ICMS', 'Vlr. ICMS', 'Vlr.ICMS', 'Val. ICMS', 'Vl. ICMS', 'Vlr ICMS', 'FT_VALICM'],
    'outricm': ['ICMS Outras', 'Outras ICMS', 'ICMS Outros', 'Outros ICMS', 'Vlr Outras ICMS', 'FT_OUTRICM'],
    'isenicm': ['ICMS Isento', 'Isento ICMS', 'ICMS Isentas', 'Isentas ICMS', 'FT_ISENICM'],
    'valipi': ['Valor IPI', 'Vlr. IPI', 'Vlr.IPI', 'Val. IPI', 'Vl. IPI', 'Vlr IPI', 'FT_VALIPI'],
    'dtcanc': ['Dt. Cancel.', 'Dt.Cancel.', 'Data Cancel.', 'Dt Cancelam.', 'FT_DTCANC'],
}
SFT_OBRIG = ('doc', 'serie', 'clifor', 'loja', 'item', 'valicm')

def _norm(c):
    import unicodedata
    c = unicodedata.normalize('NFKD', str(c)).encode('ascii', 'ignore').decode().lower()
    return ''.join(ch for ch in c if ch.isalnum())

def sft_colunas(df):
    """Mapeia os campos lógicos para as colunas da SFT. Devolve (mapa, faltando)."""
    idx = {_norm(c): c for c in df.columns}
    mp = {}
    for k, als in SFT_COLS.items():
        for a in als:
            if _norm(a) in idx: mp[k] = idx[_norm(a)]; break
    return mp, [k for k in SFT_OBRIG if k not in mp]

def _kdoc(filial, doc, serie, forn, loja):
    return '|'.join([txt(filial), txt(doc).lstrip('0'), txt(serie).lstrip('0'), txt(forn), txt(loja)])

def _num(v):
    from leitura import _to_num
    return _to_num(v)

class Livro:
    """O que de fato está no livro fiscal (SFT), que é o que o SPED leva para o C170/C190 e a apuração."""
    def __init__(self, sft, filial):
        self.ok = sft is not None
        self.it, self.nota, self.ignorados = {}, {}, 0
        if not self.ok: return
        mp, falta = sft_colunas(sft)
        if falta: raise RuntimeError(f'SFT sem as colunas {falta}. Colunas encontradas: {list(sft.columns)}. Acrescente o título em SFT_COLS (regras.py).')
        g = lambda r, k: r[mp[k]] if k in mp else ''
        for _, r in sft.iterrows():
            if 'filial' in mp and txt(g(r, 'filial')) != filial: continue
            if 'tipomov' in mp and txt(g(r, 'tipomov')).upper()[:1] not in ('E', ''): continue
            if 'dtcanc' in mp and txt(g(r, 'dtcanc')): self.ignorados += 1; continue
            kd = _kdoc(filial, g(r, 'doc'), g(r, 'serie'), g(r, 'clifor'), g(r, 'loja'))
            try: it = int(float(txt(g(r, 'item')) or 0))
            except ValueError: it = 0
            d = self.it.setdefault((kd, it), dict(valicm=0.0, outricm=0.0, isenicm=0.0, valipi=0.0))
            for k in d: d[k] += _num(g(r, k)) if k in mp else 0.0
        for (kd, _), d in self.it.items():
            n = self.nota.setdefault(kd, dict(valicm=0.0, valipi=0.0))
            n['valicm'] += d['valicm']; n['valipi'] += d['valipi']
    def item(self, r):
        if not self.ok: return None
        try: it = int(float(txt(r['Item NF']) or 0))
        except ValueError: it = 0
        return self.it.get((_kdoc(r['Filial'], r['Documento'], r['Serie'], r['Forn/Cliente'], r['Loja']), it))
    def doc(self, k):
        if not self.ok: return None
        f, d, s_, fo, lo = (k.split('|') + [''] * 5)[:5]
        return self.nota.get(_kdoc(f, d, s_, fo, lo))

def _ufdig(uf, uf_emp): return '3' if uf == 'EX' else ('1' if uf == uf_emp else '2')

def analisar(notas, sf1, sd1, sf4, filial=None, cnpj=None, uf=None, tes_presumido=None, sft=None, ctes=None, cfop_frete='352'):
    log = []; ctes = ctes or {}
    sup = collections.Counter()   # o que deixou de ser apontado por regra do usuário (vai no Resumo)
    # ---------- empresa
    cnt = collections.Counter(n['dest_cnpj'] for n in notas.values() if n['tpNF'] == '1' and n['dest_cnpj'])
    cnpj = cnpj or (cnt.most_common(1)[0][0] if cnt else '')
    ufs = collections.Counter(n['dest_uf'] for n in notas.values() if n['dest_cnpj'] == cnpj)
    uf_emp = uf or (ufs.most_common(1)[0][0] if ufs else '')
    TESP = tes_presumido or PRESUMIDO['tes']
    pres_on = uf_emp == PRESUMIDO['uf']
    def elegivel(emit_uf, crt, cfop):
        return pres_on and emit_uf == PRESUMIDO['uf'] and crt == '1' and cfop[:1] == '5' and cfop[1:] in IND
    # ---------- SF1
    df = sf1.attrs.get('datefmt', 'excel')
    sf1 = sf1[sf1['Filial'].map(txt) != ''].copy()
    sf1['Chave NFe'] = sf1['Chave NFe'].map(txt)
    for c in ('Filial', 'Numero', 'Serie', 'Fornecedor', 'Loja', 'Estado', 'Nome Forn.', 'Tipo da Nota', 'Form. Prop.', 'Espec.Docum.'):
        if c in sf1.columns: sf1[c] = sf1[c].map(txt)
        else: sf1[c] = ''
    if filial is None:
        hits = sf1[sf1['Chave NFe'].isin(notas)].groupby('Filial').size()
        filial = hits.idxmax() if len(hits) else sf1['Filial'].mode().iloc[0]
    sf1 = sf1[sf1['Filial'] == filial].copy()
    sf1['k'] = sf1['Filial'] + '|' + sf1['Numero'] + '|' + sf1['Serie'] + '|' + sf1['Fornecedor'] + '|' + sf1['Loja']
    sf1['dEmi'] = to_date(sf1['DT Emissao'], df); sf1['dRec'] = to_date(sf1['Dt. Receb.'], df)
    # chave digitada errada: acha o XML pelo número e pelo valor e passa a cruzar por ele
    docs = {**notas, **ctes}; sf1['chave_orig'] = sf1['Chave NFe']; fix = set(); k_sf1 = set(sf1['Chave NFe'])
    livres = collections.defaultdict(list)
    for c_, d_ in docs.items():
        if c_ not in k_sf1 and not d_.get('cancelada') and not (d_['emit_cnpj'] == cnpj and d_['tipo'] == 'Saída'):
            livres[d_['numero']].append(d_)
    for i, r in sf1.iterrows():
        if r['Chave NFe'] in docs: continue
        try: num = int(float(r['Numero']))
        except ValueError: continue
        cand = [d_ for d_ in livres.get(num, []) if abs(d_['vNF'] - r['Vlr.Bruto']) <= TOL]
        if len(cand) > 1: cand = [d_ for d_ in cand if _ser(d_['serie']) == _ser(r['Serie'])]
        if len(cand) == 1:
            sf1.at[i, 'Chave NFe'] = cand[0]['chave']; livres[num].remove(cand[0]); fix.add(i)
    sf1['danfe'] = sf1['Chave NFe'].map(lambda c: len(c) == 44 and c[20:22] == '55')
    sf1['cte'] = sf1['Chave NFe'].map(lambda c: len(c) == 44 and c[20:22] in ('57', '67'))
    sf1_all = sf1
    sf1 = sf1[sf1['danfe']].copy()
    ini, fim = sf1_all['dRec'].min(), sf1_all['dRec'].max()
    log.append(f'Filial {filial}; CNPJ {cnpj}/{uf_emp}; SF1 {len(sf1)} DANFE de {len(sf1_all)} notas; recebimento {ini:%d/%m/%Y} a {fim:%d/%m/%Y}')
    # ---------- SD1
    tes = TES(sf4)
    livro = Livro(sft, filial)
    if livro.ok: log.append(f'SFT {len(livro.it)} itens de entrada no livro fiscal da filial ({livro.ignorados} cancelados ignorados)')
    sd1fmt = sd1.attrs.get('datefmt', 'excel') if sd1 is not None else 'excel'
    if sd1 is not None:
        sd1 = sd1[sd1['Filial'].map(txt) == filial].copy()
        for c in ('Documento', 'Serie', 'Forn/Cliente', 'Loja', 'Cod. Fiscal', 'Sit.Tribut.', 'Tipo Entrada', 'Item NF', 'Produto'):
            sd1[c] = sd1[c].map(txt) if c in sd1.columns else ''
        sd1['k'] = filial + '|' + sd1['Documento'] + '|' + sd1['Serie'] + '|' + sd1['Forn/Cliente'] + '|' + sd1['Loja']
        sd1 = sd1.merge(sf1_all[['k', 'Chave NFe', 'Nome Forn.', 'Estado', 'Tipo da Nota', 'Form. Prop.', 'Espec.Docum.', 'danfe']], on='k', how='left')
        sd1['danfe'] = sd1['danfe'].fillna(False).astype(bool)
        TESN = sd1.groupby('k')['Tipo Entrada'].apply(lambda s: ', '.join(sorted(set(s)))).to_dict()
        log.append(f'SD1 {len(sd1)} itens; DANFE {int(sd1["danfe"].sum())}')
    else:
        TESN = {}
    def note_cred(k):
        lv = livro.doc(k)
        if lv is not None: return lv['valicm'] > TOL
        ts = [t for t in TESN.get(k, '').split(', ') if t]
        if not ts or not tes.ok: return None
        cr = [tes.credita(t) for t in ts]
        if any(c is True for c in cr): return True
        if any(c is None for c in cr): return None   # TES fora da SF4: continua dependendo da TES
        return False
    def note_consumo(k):
        ts = [t for t in TESN.get(k, '').split(', ') if t]
        return bool(ts) and tes.ok and all(tes.g(t, 'Mat.Consumo') == 'Sim' or tes.g(t, 'Cod. Fiscal')[1:] in CONSUMO_ATIVO for t in ts)

    # ================================================= cabeçalho
    div, comp = [], []
    def addh(r, n, sev, tipo, campo, vp, vx, acao):
        if n is None: n = dict(emit=r['Nome Forn.'], emit_uf=r['Estado'], emissao=r['dEmi'], crt='', csts='', cfops='')
        if sev == 'Depende da TES':
            cr = note_cred(r['k']); tl = TESN.get(r['k'], '')
            lv = livro.doc(r['k']); fonte = f"Livro fiscal (SFT) com R$ {brl(lv['valicm'])} de ICMS" if lv is not None else f'TES {tl}'
            if cr is True and lv is not None: vp = round(lv['valicm'], 2)
            if cr is True: sev = 'Alta'; tipo = tipo.replace('ICMS calculado', 'Crédito de ICMS'); acao = f'{fonte} credita ICMS: crédito indevido a estornar. ' + acao
            elif cr is False: sup['ICMS calculado em TES sem crédito (não vai para o SPED)'] += 1; return
        div.append(dict(sev=sev, tipo=tipo, nf=r['Numero'], serie=r['Serie'], forn=n['emit'], uf=n['emit_uf'], emi=n['emissao'], campo=campo,
                        vp=vp, vx=vx, crt=CRTN.get(n['crt'], n['crt']), cst=n['csts'], cfop=n['cfops'], tes=TESN.get(r['k'], ''), acao=acao, chave=r['Chave NFe']))
    m = sf1[sf1['Chave NFe'].isin(notas)]
    for _, r in m.sort_values(['Nome Forn.', 'Numero']).iterrows():
        n = notas[r['Chave NFe']]; n0 = len(div); sn = n['crt'] in ('1', '4')
        ref = n['credsn'] if sn else n['vICMS']
        p = r['Vlr.ICMS']; okic = abs(p - ref) <= TOL
        if sn:
            pmax = max((z['pcredsn'] for z in n['itens']), default=0)
            anexo = 'II' if any(z['cfop'][1:] in IND for z in n['itens']) else 'I'
            if pmax > 0:
                teto, rbt = sn_faixa(pmax, anexo)
                if rbt is None:
                    addh(r, n, 'Média', 'Alíquota de crédito SN acima do teto do Simples', 'pCredSN (%)', pmax, round(teto, 2),
                         f'Pela tabela do Anexo {anexo}, o maior percentual de ICMS possível dentro do sublimite (RBT12 de R$ 3,6 mi) é {teto:.2f}%. {pmax:g}% só se explica se o fornecedor ultrapassou o sublimite (aí o ICMS sai do DAS e é pago por fora, sem crédito SN) ou se calculou errado. Consultar a situação do fornecedor e pedir correção; em SC, acima do sublimite também não há crédito presumido de 7%.')
                elif rbt >= ALERTA_SUBLIMITE:
                    addh(r, n, 'Baixa', 'Fornecedor do Simples perto do sublimite', 'pCredSN (%)', pmax, round(teto, 2),
                         f'{pmax:g}% corresponde a um faturamento (RBT12) estimado de R$ {rbt/1e6:.2f} mi no Anexo {anexo}, perto do sublimite de R$ 3,6 mi. Acompanhar: ao ultrapassar, o crédito SN (e, em SC, o presumido de 7%) deixa de valer.')
            if any(z['csosn'] in ('101', '201') and z['pcredsn'] == 0 for z in n['itens']):
                addh(r, n, 'Baixa', 'CSOSN com permissão de crédito sem alíquota informada', 'pCredSN (%)', 0.0, 0.0,
                     'O item vem com CSOSN 101/201, mas sem pCredSN/vCredICMSSN. Sem a alíquota no documento não há crédito do art. 23 (LC 123, art. 23, § 4º, II). Pedir carta de correção ou nota complementar ao fornecedor.')
        if any(elegivel(n['emit_uf'], n['crt'], z['cfop']) for z in n['itens']):
            okic = True; ref = p
        if not okic:
            if p > 0 and ref == 0:
                addh(r, n, 'Depende da TES', 'ICMS calculado sem destaque no XML', 'ICMS', p, ref,
                     ('Fornecedor do Simples sem crédito SN no XML. ' if sn else f'XML sem ICMS destacado (CST {n["csts"]}). '))
            elif p > ref:
                addh(r, n, 'Depende da TES', 'ICMS calculado acima do XML', 'ICMS', p, ref,
                     (f'Simples: o crédito permitido é só o vCredICMSSN ({brl(ref)}).' if sn else 'Alíquota ou base no Protheus maior que no XML.'))
            elif p == 0 and sd1 is None and not note_consumo(r['k']):
                addh(r, n, 'Média', 'ICMS do XML não creditado', 'ICMS', p, ref,
                     f'ICMS destacado e zerado no Protheus em nota que não é só de consumo/ativo (TES {TESN.get(r["k"],"")}). Se for insumo ou revenda, é crédito perdido.')
            elif p > 0 and note_cred(r['k']) is False:
                sup['ICMS calculado em TES sem crédito (não vai para o SPED)'] += 1
            elif p > 0:
                addh(r, n, 'Média', 'Crédito de ICMS a menor', 'ICMS', p, ref, 'ICMS no Protheus menor que o do XML: conferir alíquota/redução na TES.')
        if not sn and not any(elegivel(n['emit_uf'], n['crt'], z['cfop']) for z in n['itens']):
            db = round(r['Base p/ICMS'] - n['vBC'], 2)
            if abs(db) > TOL:
                sev = None
                if not okic and len(div) > n0: sev, t, a = div[-1]['sev'], 'Base de ICMS divergente', 'Acompanha a divergência de ICMS acima.'
                elif not okic: sev = None
                elif p <= TOL or note_cred(r['k']) is False: sup['Base de ICMS diferente em nota sem crédito'] += 1
                else: sev, t, a = 'Média', 'Base de ICMS divergente (ICMS confere)', 'ICMS igual ao XML, mas a base escriturada difere (ex.: IPI na base). Vai assim para o C100/C190 do SPED: corrigir a base no documento.'
                if sev: addh(r, n, sev, t, 'Base ICMS', r['Base p/ICMS'], n['vBC'], a)
        ipix = n['ipi_it'] or n['vIPI']
        dbr = round(r['Vlr.Bruto'] - n['vNF'], 2)
        if abs(r['Vlr.IPI'] - ipix) > TOL:
            if abs(dbr) <= TOL: sup['IPI diferente do XML com total conferindo (TES sem crédito de IPI ou IPI em outro campo)'] += 1
            elif r['Vlr.IPI'] < ipix: addh(r, n, 'Alta', 'IPI destacado no XML não escriturado', 'IPI', r['Vlr.IPI'], ipix, 'TES sem cálculo de IPI: total e título a pagar menores que o documento. Corrigir a TES e relançar.')
            else: addh(r, n, 'Alta', 'IPI escriturado sem destaque no XML', 'IPI', r['Vlr.IPI'], ipix, 'Protheus calcula IPI que o documento não traz.')
        if abs(dbr) > TOL: addh(r, n, 'Alta', 'Valor total da nota diverge', 'Vlr Total', r['Vlr.Bruto'], n['vNF'], 'Total escriturado diferente do vNF: afeta contas a pagar e SPED.')
        if abs(r['Vlr.Mercad'] - n['vProd']) > TOL: addh(r, n, 'Alta', 'Valor das mercadorias diverge', 'Vlr Mercadorias', r['Vlr.Mercad'], n['vProd'], 'Quantidade/preço digitado diferente do XML.')
        if abs(r['ICMS Solid.'] - n['vST']) > TOL: addh(r, n, 'Alta', 'ICMS ST diverge', 'ICMS ST', r['ICMS Solid.'], n['vST'], 'Conferir ST na TES.')
        if abs(r['Descontos'] - n['vDesc']) > TOL and abs(dbr) <= TOL: addh(r, n, 'Baixa', 'Desconto classificado diferente', 'Desconto', r['Descontos'], n['vDesc'], 'Total confere.')
        for a, b, c in [('Vlr.Frete', 'vFrete', 'Frete'), ('Vlr.Despesas', 'vOutro', 'Outras despesas')]:
            ipimis = abs(r['Vlr.IPI'] - ipix) > TOL and abs((r[a] + r['Vlr.IPI']) - (n[b] + ipix)) <= TOL
            if abs(r[a] - n[b]) > TOL and abs(dbr) <= TOL and not (c == 'Outras despesas' and ipimis):
                addh(r, n, 'Baixa', 'Acessório lançado em campo diferente (total confere)', c, r[a], n[b],
                     'Nota de importação: vOutro do XML soma II/PIS/COFINS/despesas aduaneiras. Total confere.' if r['Estado'] == 'EX'
                     else 'Frete lançado como despesa (ou o inverso). Sem impacto no total; afeta rateio de custo e SPED.')
        if _ser(r['Serie']) != _ser(n['serie']):
            addh(r, n, 'Média', 'Série divergente do XML', 'Série', r['Serie'], n['serie'], 'Série digitada diferente da do documento: corrigir (o SPED leva a série do lançamento).')
        if pd.notna(r['dEmi']) and pd.notna(n['emissao']) and r['dEmi'].date() != n['emissao'].date():
            addh(r, n, 'Média', 'Data de emissão divergente', 'Emissão', r['dEmi'].strftime('%d/%m/%Y'), n['emissao'].strftime('%d/%m/%Y'), 'Data digitada diferente da do XML: corrigir.')
        comp.append(dict(r=r, n=n, ref=ref, ipix=ipix, tes=TESN.get(r['k'], ''), ndiv=len(div) - n0, sev=sevmin([d['sev'] for d in div[n0:]])))

    # ================================================= CT-e (SF1/SD1 × XML de CT-e)
    ccomp = []
    raiz = cnpj[:8]
    natcf = lambda cf: next((k_ for k_, v_ in NAT.items() if txt(cf)[1:] in v_), 'outros')
    tes_frete = sorted(t for t in tes.f4 if tes.g(t, 'Tipo do TES') == 'Entrada' and tes.g(t, 'Cod. Fiscal')[1:] == cfop_frete) if tes.ok else []
    fr_cred = [t for t in tes_frete if tes.credita(t) is True]; fr_sem = [t for t in tes_frete if tes.credita(t) is False]
    nat_ch, g_k = {}, {}
    if sd1 is not None:
        for ch_, g_ in sd1.groupby('Chave NFe'): nat_ch[ch_] = {natcf(cf) for cf in g_['Cod. Fiscal']}
        g_k = {k_: g_ for k_, g_ in sd1.groupby('k')}
    def direito(c):
        """Se o frete dá direito a crédito de ICMS: (True/False/None, motivo)."""
        if c['sn']: return False, 'Transportadora do Simples: o CT-e não destaca ICMS'
        if c['st']: return None, 'ICMS da prestação por substituição tributária (CST 60): conferir a regra'
        if c['vICMS'] <= TOL: return False, f"Prestação sem ICMS no CT-e (CST {c['cst'] or '—'})"
        own = [d_ for d_ in c['docs'] if d_[6:14] == raiz]; third = [d_ for d_ in c['docs'] if d_[6:14] != raiz]
        nats = set().union(*[nat_ch.get(d_, set()) for d_ in third]) if third else set()
        if own: return True, f'Frete de NF-e emitida pela própria empresa ({len(own)} nota(s): venda/transferência)'
        if 'insumo/revenda' in nats: return True, 'Frete de compra para industrialização/revenda'
        if nats and nats <= {'consumo', 'ativo'}: return False, f"Frete de compra de {' e '.join(sorted(nats))} (sem crédito)"
        if third and not nats: return None, 'A NF-e transportada não está na SD1 desta filial'
        return None, 'CT-e sem NF-e vinculada'
    cte1 = sf1_all[sf1_all['cte'] & sf1_all['Chave NFe'].isin(ctes)]
    for _, r in cte1.sort_values(['Nome Forn.', 'Numero']).iterrows():
        c = ctes[r['Chave NFe']]; n0 = len(div); g = g_k.get(r['k'])
        if g is not None and len(g):
            bc, ic = float(g['Base Icms'].sum()), float(g['Vlr.ICMS'].sum()); al = float(g['Aliq. ICMS'].max())
            cfps, csts, tess = set(g['Cod. Fiscal']) - {''}, set(g['Sit.Tribut.']) - {''}, sorted(set(g['Tipo Entrada']) - {''})
        else:
            bc, ic, al, cfps, csts, tess = r['Base p/ICMS'], r['Vlr.ICMS'], None, set(), set(), []
        lv = livro.doc(r['k'])
        if lv is not None: cr = lv['valicm'] > TOL; ic_cr = round(lv['valicm'], 2)
        elif tess and tes.ok:
            crs = [tes.credita(t) for t in tess]; ic_cr = ic
            cr = True if any(x is True for x in crs) else (None if any(x is None for x in crs) else False)
        else: cr = False if ic <= TOL else None; ic_cr = ic
        dir_, mot = direito(c)
        xcst = '0' + c['cst'].zfill(2) if c['cst'] else ''
        tl = ', '.join(tess)
        if abs(r['Vlr.Bruto'] - c['vTPrest']) > TOL:
            addh(r, c, 'Alta', 'CT-e: valor da prestação diverge', 'Vlr Total', r['Vlr.Bruto'], c['vTPrest'], 'Valor escriturado diferente do vTPrest do CT-e: afeta contas a pagar e o D100 do SPED.')
        if _ser(r['Serie']) != _ser(c['serie']):
            addh(r, c, 'Média', 'Série divergente do XML', 'Série', r['Serie'], c['serie'], 'Série digitada diferente da do CT-e: corrigir.')
        if pd.notna(r['dEmi']) and pd.notna(c['emissao']) and r['dEmi'].date() != c['emissao'].date():
            addh(r, c, 'Média', 'Data de emissão divergente', 'Emissão', r['dEmi'].strftime('%d/%m/%Y'), c['emissao'].strftime('%d/%m/%Y'), 'Data digitada diferente da do CT-e: corrigir.')
        if c['toma_cnpj'] and c['toma_cnpj'] != cnpj:
            addh(r, c, 'Média', 'CT-e escriturado sem a empresa ser a tomadora', 'Tomador', fcnpj(cnpj), fcnpj(c['toma_cnpj']),
                 f"No CT-e o tomador (quem paga o frete) é o {c['toma'] or 'outro'}, CNPJ {fcnpj(c['toma_cnpj'])}. Só o tomador escritura o CT-e e toma o crédito: conferir se o lançamento é desta filial.")
        pref = '3' if c['uf_ini'] == 'EX' else ('1' if c['uf_ini'] == uf_emp else '2'); exp = pref + cfop_frete
        if cfps and c['mod'] == '57' and any(cf != exp for cf in cfps):
            addh(r, c, 'Média', 'CT-e: CFOP divergente', 'CFOP', ', '.join(sorted(cfps)), exp,
                 f"Transporte de {c['uf_ini']} para {c['uf_fim']} (CFOP do CT-e {c['cfop']}), empresa em {uf_emp}. Aquisição de serviço de transporte por estabelecimento industrial: {exp} (1 quando a prestação começa na UF da empresa, 2 quando começa em outra UF).")
        crt_txt = f' Base R$ {brl(c["vBC"])}, alíquota {c["pICMS"]:g}%, ICMS R$ {brl(c["vICMS"])}, CST {xcst}.'
        if cr is True and dir_ is False:
            addh(r, c, 'Alta', 'CT-e: crédito de ICMS em frete sem direito', 'ICMS', ic_cr, 0.0,
                 f'{mot}. TES {tl} credita ICMS: crédito indevido. Zerar base, alíquota e ICMS e lançar com CST 090' + (f' numa TES de frete sem crédito ({", ".join(fr_sem)})' if fr_sem else '') + '.')
        elif cr is False and dir_ is True:
            addh(r, c, 'Média', 'CT-e: ICMS do frete não creditado', 'ICMS', 0.0, c['vICMS'],
                 f'{mot}: dá direito a crédito, mas a TES {tl or "usada"} não credita. Lançar com os valores do CT-e:' + crt_txt + (f' TES de frete com crédito: {", ".join(fr_cred)}.' if fr_cred else ''))
        elif cr is True:
            if abs(ic_cr - c['vICMS']) > TOL:
                if ic_cr > c['vICMS']: addh(r, c, 'Alta', 'CT-e: crédito de ICMS acima do XML', 'ICMS', ic_cr, c['vICMS'], 'Crédito maior que o ICMS do CT-e: estornar o excedente. Valores do CT-e:' + crt_txt)
                else: addh(r, c, 'Média', 'CT-e: crédito de ICMS abaixo do XML', 'ICMS', ic_cr, c['vICMS'], 'Crédito menor que o ICMS do CT-e. Valores do CT-e:' + crt_txt)
            if al is not None and abs(al - c['pICMS']) > 0.01:
                addh(r, c, 'Média', 'CT-e: alíquota de ICMS divergente', 'Alíq. ICMS', al, c['pICMS'], f'Alíquota do CT-e: {c["pICMS"]:g}% (prestação {c["uf_ini"]}→{c["uf_fim"]}). Corrigir no lançamento.')
            if abs(bc - c['vBC']) > TOL:
                addh(r, c, 'Média', 'CT-e: base de ICMS divergente', 'Base ICMS', bc, c['vBC'], 'Base escriturada diferente da do CT-e: corrigir (vai para o D100/D190).')
            if csts and xcst and any(cs != xcst for cs in csts):
                addh(r, c, 'Média', 'CT-e: CST divergente', 'CST', ', '.join(sorted(csts)), xcst, f'Com crédito, o CST é o do CT-e ({xcst}).')
        elif cr is None and ic > TOL and dir_ is False:
            addh(r, c, 'Depende da TES', 'CT-e: ICMS calculado em frete sem direito', 'ICMS', ic, 0.0, f'{mot}. Só é crédito indevido se a TES {tl} creditar.')
        elif cr is None and dir_ is True and abs(ic - c['vICMS']) > TOL:
            addh(r, c, 'Depende da TES', 'CT-e: ICMS calculado diferente do XML', 'ICMS', ic, c['vICMS'], f'{mot}. Valores do CT-e:' + crt_txt)
        if cr is False and dir_ is not True and csts and any(cs[-2:] != '90' for cs in csts):
            addh(r, c, 'Média', 'CT-e: CST divergente', 'CST', ', '.join(sorted(csts)), '090', 'Frete sem crédito de ICMS: CST 090 e base, alíquota e ICMS zerados.')
        ccomp.append(dict(r=r, c=c, bc=bc, ic=ic_cr, al=al, cfps=', '.join(sorted(cfps)), csts=', '.join(sorted(csts)), tes=tl, exp=exp, xcst=xcst,
                          dir=dir_, mot=mot, cr=cr, ndiv=len(div) - n0, sev=sevmin([d['sev'] for d in div[n0:]])))

    # ================================================= chave de acesso, espécie e fornecedor (todos os documentos)
    for i, r in sf1_all.iterrows():
        ch = r['Chave NFe']; esp = txt(r['Espec.Docum.']).upper(); n = docs.get(ch)
        if i in fix:
            addh(r, n, 'Alta', 'Chave de acesso divergente do XML', 'Chave', r['chave_orig'] or '(vazia)', ch,
                 (f"Documento lançado sem chave. O XML de mesmo número ({n['numero']}) e valor (R$ {brl(n['vNF'])}) de {n['emit']} traz a chave ao lado: informá-la no documento de entrada. Sem a chave, o SPED não identifica o documento. O cruzamento seguiu pela chave do XML."
                  if not r['chave_orig'] else
                  f"O XML de mesmo número ({n['numero']}) e valor (R$ {brl(n['vNF'])}) de {n['emit']} tem outra chave. Corrigir a chave no documento de entrada: com a chave errada o SPED informa um documento que não existe na SEFAZ. O cruzamento seguiu pela chave do XML."))
            continue
        if not ch:
            if esp in ESPEC_ELETR:
                addh(r, n, 'Alta', 'Documento eletrônico sem chave de acesso', 'Chave', '(vazia)', '', f'Espécie {esp} exige a chave de 44 dígitos. Informar a chave do XML/DANFE.')
            continue
        if not dv_ok(ch):
            addh(r, n, 'Alta', 'Chave de acesso inválida', 'Chave', ch, '', 'A chave não tem 44 dígitos ou o dígito verificador não confere: foi digitada errada. Copiar a chave do XML/DANFE.')
            continue
        mod = ch[20:22]
        if esp and mod in MODELO and esp not in MODELO[mod][0]:
            addh(r, n, 'Média', 'Espécie do documento incompatível com a chave', 'Espécie', esp, MODELO[mod][1],
                 f'A chave é de modelo {mod} ({MODELO[mod][1]}) e o documento foi lançado com espécie {esp}. Corrigir a espécie: o SPED leva cada modelo num registro diferente (C100, D100, C500...).')
        if n is None:
            try: num = int(float(r['Numero']))
            except ValueError: num = None
            if num is not None and int(ch[25:34]) != num:
                addh(r, n, 'Alta', 'Chave de acesso não confere com o número do documento', 'Número', r['Numero'], str(int(ch[25:34])),
                     'O número embutido na chave é outro: a chave ou o número foi digitado errado. Conferir no DANFE/XML.')
            elif _ser(ch[22:25]) != _ser(r['Serie']):
                addh(r, n, 'Média', 'Série divergente da chave de acesso', 'Série', r['Serie'], ch[22:25].lstrip('0') or '0', 'A série embutida na chave é outra: corrigir a série do lançamento.')
    mapa = collections.defaultdict(collections.Counter)
    for _, r in sf1_all.iterrows():
        d_ = docs.get(r['Chave NFe'])
        if d_ and d_['emit_cnpj'] and d_['emit_cnpj'] != cnpj and txt(r['Form. Prop.']) != 'S': mapa[(r['Fornecedor'], r['Loja'])][d_['emit_cnpj']] += 1
    col_cnpj = next((c_ for c_ in sf1_all.columns if _norm(c_) in ('cnpj', 'cnpjcpf', 'cpfcnpj', 'cgc', 'cgccpf', 'cnpjforn', 'cnpjfornecedor', 'cnpjcpfforn')), None)
    for _, r in sf1_all.iterrows():
        ch = r['Chave NFe']; d_ = docs.get(ch)
        emit = d_['emit_cnpj'] if d_ else (ch[6:20] if dv_ok(ch) else '')
        if not emit or emit == cnpj or txt(r['Form. Prop.']) == 'S': continue
        lanc = ''.join(x for x in txt(r[col_cnpj]) if x.isdigit()) if col_cnpj else ''
        if not col_cnpj:
            cnt_ = mapa.get((r['Fornecedor'], r['Loja']))
            if cnt_:
                top, nt = cnt_.most_common(1)[0]
                if top != emit and nt >= 2 and nt > cnt_.get(emit, 0): lanc = top
        if lanc and lanc != emit:
            addh(r, d_, 'Alta', 'Fornecedor do lançamento com CNPJ diferente do emitente', 'CNPJ', fcnpj(lanc), fcnpj(emit),
                 f"Lançada no fornecedor {r['Fornecedor']}/{r['Loja']} ({r['Nome Forn.']}), que é o CNPJ {fcnpj(lanc)}; o emitente {'do XML' if d_ else 'na chave'} é o CNPJ {fcnpj(emit)}"
                 + (f" ({d_['emit']})" if d_ else '') + '. Escriturar no código/loja do CNPJ certo: o SPED leva o participante errado (0150) e o título fica no fornecedor errado.')
    div.sort(key=lambda d: (SEVO[d['sev']], d['tipo'], d['forn'], d['nf']))

    # ---------- só XML / só SF1
    k1 = set(sf1_all['Chave NFe']); sox = []
    recent = max((n['emissao'] for n in notas.values() if pd.notna(n['emissao'])), default=pd.Timestamp.now()) - pd.Timedelta(days=3)
    for n in sorted([n for c, n in notas.items() if c not in k1], key=lambda n: n['emissao']):
        if n.get('cancelada') or n['cStat'] in ('101', '135', '151', '155'):
            mot, sev = 'Cancelada na SEFAZ: não deve ser escriturada.', 'Info'
        elif n['emit_cnpj'] == cnpj and n['tipo'] == 'Saída':
            mot, sev = 'Saída emitida pela própria filial: escritura na SF2, não na SF1.', 'Info'
        elif n['emit_cnpj'] == cnpj:
            mot, sev = 'Entrada com formulário próprio autorizada e sem lançamento na SF1. Verificar se deveria ter sido lançada ou cancelada.', 'Alta'
        elif n['dest_cnpj'] and n['dest_cnpj'] != cnpj:
            mot, sev = f'Destinatário é outro CNPJ ({n["dest_cnpj"]}): não pertence a esta filial.', 'Info'
        else:
            mot, sev = 'Recebida de terceiro e ainda não escriturada na SF1.', 'Média'
            if n['emissao'] >= recent: mot += ' Emissão recente: pode estar em trânsito.'
            elif n['vICMS'] > 0: mot += ' Tem ICMS destacado.'
        sox.append(dict(sev=sev, n=n, mot=mot))
    papel = {'rem': 'remetente', 'dest': 'destinatário', 'exped': 'expedidor', 'receb': 'recebedor', 'outros': 'outro'}
    for c in sorted([c for ch, c in ctes.items() if ch not in k1], key=lambda c: c['emissao']):
        if c.get('cancelada') or c['cStat'] in ('101', '135'):
            mot, sev = 'CT-e cancelado na SEFAZ: não deve ser escriturado.', 'Info'
        elif c['toma_cnpj'] and c['toma_cnpj'] != cnpj:
            mot, sev = (f"A empresa não é a tomadora: o tomador é o {papel.get(c['toma'], c['toma'])} ({fcnpj(c['toma_cnpj'])})"
                        + (', outra filial da empresa' if c['toma_cnpj'][:8] == raiz else '') + '. Quem paga o frete é que escritura.'), 'Info'
        else:
            mot, sev = 'CT-e em que a empresa é a tomadora, ainda não escriturado na SF1.', 'Média'
            if c['vICMS'] > 0: mot += f" ICMS de R$ {brl(c['vICMS'])} no CT-e."
        sox.append(dict(sev=sev, n=c, mot=mot))
    xi0 = min((n['emissao'] for n in notas.values() if pd.notna(n['emissao'])), default=None)
    xi1 = max((n['emissao'] for n in notas.values() if pd.notna(n['emissao'])), default=None)
    sos = []
    for _, r in sf1[~sf1['Chave NFe'].isin(notas)].sort_values('dEmi').iterrows():
        if xi0 is not None and pd.notna(r['dEmi']) and r['dEmi'].normalize() < xi0.normalize():
            mot, sev = f'Emitida em {r["dEmi"]:%m/%Y}, antes do período do download de XML ({xi0:%d/%m/%Y} a {xi1:%d/%m/%Y}). Para fechar, baixar os XML do mês anterior.', 'Info'
        else:
            mot, sev = 'Emitida dentro do período, mas o XML não veio no download. Baixar e conferir.', 'Média'
        sos.append(dict(sev=sev, r=r, mot=mot))
    if ctes:   # CT-e lançado sem XML (só quando vieram XML de CT-e no download)
        ci0 = min((c['emissao'] for c in ctes.values() if pd.notna(c['emissao'])), default=None)
        for _, r in sf1_all[sf1_all['cte'] & ~sf1_all['Chave NFe'].isin(ctes)].sort_values('dEmi').iterrows():
            if ci0 is not None and pd.notna(r['dEmi']) and r['dEmi'].normalize() < ci0.normalize():
                mot, sev = f'CT-e emitido em {r["dEmi"]:%m/%Y}, antes do período dos XML de CT-e. Para fechar, baixar os do mês anterior.', 'Info'
            else:
                mot, sev = 'CT-e emitido dentro do período, mas o XML não veio no download. Baixar e conferir.', 'Média'
            sos.append(dict(sev=sev, r=r, mot=mot))

    # ================================================= itens
    idiv, icomp, agr, exg, meta = [], [], [], None, {}
    if sd1 is not None:
        z_alta = set()
        _kit = lambda r: (r['k'], txt(r['Item NF']))
        def add(r, z, sev, tipo, campo, vp, vx, acao):
            if sev == 'Depende da TES':
                t = r['Tipo Entrada']; lv = livro.item(r)
                if lv is not None:
                    if lv['valicm'] > TOL:
                        sev = 'Alta'; tipo = tipo.replace('ICMS calculado', 'Crédito de ICMS'); vp = round(lv['valicm'], 2)
                        acao = f"O livro fiscal (SFT) traz R$ {brl(lv['valicm'])} de ICMS creditado neste item: vai para a apuração. Crédito indevido a estornar. " + acao
                        if tes.credita(t) is False: acao += f' A TES {t} não credita: o livro diverge da TES (TES alterada depois do lançamento ou ajuste manual).'
                        z_alta.add(_kit(r))
                    else:
                        sup['ICMS calculado em TES sem crédito (não vai para o SPED)'] += 1; return
                elif tes.credita(t) is not None:
                    if tes.credita(t): sev = 'Alta'; tipo = tipo.replace('ICMS calculado', 'Crédito de ICMS'); acao = tes.desc(t) + ' A TES credita: crédito indevido a estornar. ' + acao
                    else: sup['ICMS calculado em TES sem crédito (não vai para o SPED)'] += 1; return
                elif tes.incoerente_icms(t):
                    acao += f" TES {t} com crédito e livro desencontrados ({'; '.join(tes.incoerencias(t))}): só a SFT diz se foi para a apuração."
            idiv.append(dict(sev=sev, tipo=tipo, nf=r['Documento'], serie=r['Serie'], forn=txt(r['Nome Forn.']), uf=txt(r['Estado']), item=r['Item NF'],
                             nitem=z['nItem'] if z else None, prod=r['Produto'], desc=z['xprod'] if z else '', campo=campo, vp=vp, vx=vx,
                             cfop_p=r['Cod. Fiscal'], cfop_x=z['cfop'] if z else '', cst_p=r['Sit.Tribut.'], cst_x=(z['orig'] + (z['cst'] or z['csosn'])) if z else '',
                             tes=r['Tipo Entrada'], acao=acao, chave=r['Chave NFe']))
        def internal(r, z, ref=0.0, cstchk=True):
            cf = r['Cod. Fiscal']; suf = cf[1:]; ic = r['Vlr.ICMS']; cst = r['Sit.Tribut.'][-2:]; t = r['Tipo Entrada']
            if txt(r['Form. Prop.']) != 'S' and cf and txt(r['Estado']) and cf[0] != _ufdig(txt(r['Estado']), uf_emp):
                add(r, z, 'Alta', 'CFOP de entrada incompatível com a UF do fornecedor', 'CFOP', cf, 'UF ' + txt(r['Estado']), f'Fornecedor em {r["Estado"]} pede CFOP iniciado em {_ufdig(txt(r["Estado"]), uf_emp)}.')
            lvi = livro.item(r); consumo = tes.g(t, 'Mat.Consumo') == 'Sim' or suf in CONSUMO_ATIVO[:3]
            if lvi is not None:
                if consumo and lvi['valipi'] > TOL:
                    add(r, z, 'Alta', 'Crédito de IPI em material de uso e consumo', 'IPI', round(lvi['valipi'], 2), 0.0,
                        f"O livro fiscal (SFT) traz R$ {brl(lvi['valipi'])} de IPI creditado em material de consumo (TES {t}, CFOP {cf}). IPI só gera crédito em MP, PI e embalagem: estornar e ajustar a TES.")
            elif tes.ok and tes.credita_ipi(t) and tes.g(t, 'Mat.Consumo') == 'Sim' and r['Vlr.IPI'] > TOL:
                add(r, z, 'Alta', 'Crédito de IPI em material de uso e consumo', 'IPI', r['Vlr.IPI'], 0.0,
                    f"TES {t} ({tes.g(t,'Txt Padrao')}) é de material de consumo e credita IPI (livro {tes.g(t,'L.Fiscal IPI')}). IPI só gera crédito em MP, PI e embalagem: estornar e ajustar a TES.")
            if suf in ('556', '407') and ic > TOL:
                add(r, z, 'Depende da TES', 'ICMS calculado em CFOP de uso e consumo', 'ICMS', ic, ref, f'CFOP {cf} é uso e consumo, que não dá crédito.')
            if cstchk and cst in ('40', '41', '50', '60', '61') and ic > TOL and suf not in ('556', '407'):
                add(r, z, 'Depende da TES', 'ICMS calculado com CST sem tributação', 'ICMS', ic, 0.0, f'CST {r["Sit.Tribut."]} sem ICMS próprio e item com ICMS calculado.')
        lk = sd1[sd1['danfe']].copy(); lk['ItemN'] = pd.to_numeric(lk['Item NF'], errors='coerce').fillna(0).astype(int)
        pairs, unpaired = [], []
        for ch, g in lk[lk['Chave NFe'].isin(notas)].groupby('Chave NFe'):
            xi = sorted(notas[ch]['itens'], key=lambda z: z['nItem']); g = g.sort_values('ItemN')
            if len(xi) != len(g): unpaired.append((ch, g, xi)); continue
            bad = sum(abs(r['Vlr.Total'] - z['vprod']) > TOL for (_, r), z in zip(g.iterrows(), xi))
            if bad:
                rem = list(xi); alt = []
                for _, r in g.iterrows():
                    j = min(range(len(rem)), key=lambda j: abs(rem[j]['vprod'] - r['Vlr.Total'])); alt.append(rem.pop(j))
                if sum(abs(r['Vlr.Total'] - z['vprod']) > TOL for (_, r), z in zip(g.iterrows(), alt)) < bad: xi = alt
            pairs += [(r, z) for (_, r), z in zip(g.iterrows(), xi)]
        for r, z in pairs:
            n0 = len(idiv); sn = z['crt'] in ('1', '4'); t = r['Tipo Entrada']
            ref = round(z['vcredsn'], 2) if sn else z['vicms']
            internal(r, z, ref, False)
            if abs(r['Vlr.Total'] - z['vprod']) > TOL: add(r, z, 'Alta', 'Valor do item diverge', 'Vlr Item', r['Vlr.Total'], z['vprod'], 'Quantidade ou preço digitado diferente do XML.')
            cx, cp = z['cfop'], r['Cod. Fiscal']
            if txt(r['Form. Prop.']) == 'S':
                if cx != cp: add(r, z, 'Alta', 'CFOP diferente do documento emitido', 'CFOP', cp, cx, 'Formulário próprio: o CFOP lançado tem de ser o do XML.')
            elif cx and cx[0] in '123':
                add(r, z, 'Alta', 'NF de entrada do fornecedor lançada como compra', 'CFOP', cp, cx, 'O XML é uma nota de ENTRADA emitida pelo fornecedor (a empresa é a remetente). Verificar e excluir o lançamento.')
            elif cx:
                exp = {'5': '1', '6': '2', '7': '3'}.get(cx[0], '')
                if cp[:1] != exp: add(r, z, 'Alta', 'CFOP com origem trocada (interna × interestadual)', 'CFOP', cp, cx, f'CFOP {cx} do fornecedor pede entrada iniciada em {exp}.')
                grp = next((gg for gg in GRP if cx[1:] in gg[0]), None)
                if grp and cp[1:] not in grp[1]:
                    add(r, z, 'Média', 'Natureza do CFOP incompatível com o documento', 'CFOP', cp, cx, f'O fornecedor emitiu como {grp[2]} ({cx}); o CFOP de entrada {cp} é de outra natureza.')
                elif cx[1:] == '653' and cp[1:] != '653':
                    add(r, z, 'Baixa', 'Combustível fora do CFOP x653', 'CFOP', cp, cx, 'Venda de combustível a consumidor final: entrada usual em 1653/2653.')
                st = (z['cst'] in STCST) or (z['csosn'] in STCSOSN) or cx[1:] in ('401', '402', '403', '404', '405')
                if st and cp[1:] in ('101', '102', '556', '551'):
                    sug = {'556': '407', '551': '406', '101': '401', '102': '403'}[cp[1:]]
                    add(r, z, 'Média', 'Item com ST no XML lançado em CFOP sem ST', 'CFOP', cp, cx, f'Item com ICMS-ST (CST/CSOSN {z["cst"] or z["csosn"]}). CFOP de entrada correspondente: {cp[0]}{sug}.')
                elif not st and cp[1:] in ('401', '403', '406', '407'):
                    add(r, z, 'Média', 'CFOP de ST sem ST no XML', 'CFOP', cp, cx, 'Entrada classificada como ST, mas o item não tem ST no documento.')
            cstp = r['Sit.Tribut.']
            if cstp and z['orig'] and cstp[0] != z['orig']:
                add(r, z, 'Média', 'Origem da mercadoria divergente', 'CST (origem)', cstp, z['orig'] + (z['cst'] or z['csosn']),
                    f'Origem {z["orig"]} no XML e {cstp[0]} no Protheus. Origens 1, 2, 3 e 8 indicam conteúdo importado (alíquota interestadual de 4%).')
            lvc = livro.item(r); cred_it = (lvc['valicm'] > TOL) if lvc is not None else tes.credita(t)
            if not sn and z['cst'] and cstp[-2:] != z['cst']:
                if cstp[-2:] == '90' and (r['Vlr.ICMS'] <= TOL or cred_it is False):
                    sup['CST 090 em TES sem crédito (padrão da empresa)'] += 1
                elif cstp[-2:] == '60' and (combustivel(z) or z['cst'] in STCST):
                    sup['CST 060 em combustível ou item com ST (padrão da empresa)'] += 1
                else:
                    add(r, z, 'Média', 'CST diverge do documento', 'CST', cstp, z['orig'] + z['cst'], 'Tributação lançada diferente da nota do fornecedor. Rever a TES.')
            refa = z['pcredsn'] if sn else z['picms']; p = r['Vlr.ICMS']; okic = abs(p - ref) <= TOL
            eleg = elegivel(txt(r['Estado']), z['crt'], cx)
            if eleg:
                base = round(z['vprod'] - z['vdesc'], 2); esp = round(base * PRESUMIDO['pct'], 2)
                teto, rbt = sn_faixa(z['pcredsn'], 'II') if z['pcredsn'] > 0 else (None, 0)
                ref = esp; refa = PRESUMIDO['pct'] * 100
                if t != TESP:
                    cons = cp[1:] in CONSUMO_ATIVO
                    add(r, z, 'Média' if cons else 'Alta', 'Indústria do Simples (SC) fora da TES de crédito presumido', 'TES', 0.0, esp,
                        (f'Entrada como uso e consumo/ativo (CFOP {cp}): confirmar se o presumido alcança esse destino (Anexo 2, art. 15, § 25) antes de mudar a TES. ' if cons else '') + f'Compra interna de indústria do Simples de SC (CFOP {cx}) tem direito ao crédito presumido de 7% (RICMS/SC, Anexo 2, art. 15, XXVI), que deve entrar pela TES {TESP}. Lançada na TES {t}: o fornecedor não está cadastrado no Configurador de Tributos. Cadastrar e reprocessar. Crédito presumido esperado: R$ {brl(esp)} (7% de R$ {brl(base)}).')
                elif rbt is None:
                    add(r, z, 'Alta', 'Crédito presumido com fornecedor acima do sublimite', 'pCredSN (%)', z['pcredsn'], round(teto, 2),
                        f'Nota na TES {TESP} (crédito presumido de 7%), mas o pCredSN de {z["pcredsn"]:g}% passa do teto possível dentro do sublimite ({teto:.2f}%). Se o fornecedor ultrapassou o sublimite, não há direito ao presumido (COPAT 75/2022). Confirmar a situação do fornecedor antes de apropriar R$ {brl(esp)}.')
                if t == TESP and p > TOL and abs(p - esp) > TOL:
                    add(r, z, 'Média', 'Valor no item diferente do crédito presumido de 7%', 'ICMS', p, esp,
                        f'O item na TES {TESP} traz R$ {brl(p)}, mas 7% de R$ {brl(base)} são R$ {brl(esp)}. Conferir a regra do Configurador de Tributos.')
            elif pres_on and t == TESP:
                mot = ('fornecedor não é do Simples' if z['crt'] not in ('1',) else
                       f"fornecedor é de {txt(r['Estado'])}, não de SC" if txt(r['Estado']) != 'SC' else
                       f'CFOP {cx} não é de venda de produção própria (indústria)')
                add(r, z, 'Média', 'TES de crédito presumido em nota sem direito', 'TES', 0.0, 0.0,
                    f'Item lançado na TES {TESP} (crédito presumido de 7% de SC), mas {mot}. Rever a TES.')
            if not eleg and not okic and not (cp[1:] in ('556', '407') and p > TOL):
                al = f' Alíquota: Protheus {r["Aliq. ICMS"]:g}% × XML {refa:g}%.'
                if p > TOL and ref == 0: add(r, z, 'Depende da TES', 'ICMS calculado sem destaque no XML', 'ICMS', p, ref, ('Simples sem crédito SN no item.' if sn else f'Item sem ICMS no XML (CST {z["cst"]}).') + al)
                elif p > ref: add(r, z, 'Depende da TES', 'ICMS calculado acima do XML', 'ICMS', p, ref, ('Simples: só vale o vCredICMSSN.' if sn else 'Acima do destacado.') + al)
                elif p <= TOL:
                    if cp[1:] in INSUMO and not tes.ok: add(r, z, 'Média', 'ICMS do XML não creditado em insumo/revenda', 'ICMS', p, ref, f'CFOP {cp} dá direito a crédito e o ICMS ficou zerado.')
                else: add(r, z, 'Média', 'Crédito de ICMS a menor', 'ICMS', p, ref, 'Abaixo do destacado.' + al)
            lvp = livro.item(r); semcred = (lvp['valicm'] <= TOL and tes.credita(t) is not True) if lvp is not None else (tes.ok and tes.credita(t) is False)
            if not eleg and semcred and cp[1:] in INSUMO and ref > TOL:
                if sn: add(r, z, 'Média', 'Crédito do Simples não aproveitado (TES sem crédito)', 'ICMS', 0.0, ref, f"Simples informou crédito de {z['pcredsn']:g}% (CSOSN {z['csosn']}) em CFOP {cp}, que dá direito a crédito. A TES {t} ({tes.g(t,'Txt Padrao')}) não credita.")
                else: add(r, z, 'Média', 'ICMS destacado não creditado em insumo/revenda (TES sem crédito)', 'ICMS', 0.0, ref, f"CFOP {cp} dá direito a crédito e a TES {t} não credita." + (' O livro fiscal (SFT) também está sem crédito.' if lvp is not None else ''))
            if not eleg and not sn and okic and p > TOL and abs(r['Aliq. ICMS'] - z['picms']) > 0.01:
                if cred_it is False: sup['Alíquota/base de ICMS diferente em TES sem crédito'] += 1
                else: add(r, z, 'Média', 'Alíquota de ICMS divergente (valor confere)', 'Alíq. ICMS', r['Aliq. ICMS'], z['picms'], f'Valor confere, mas a alíquota gravada é {r["Aliq. ICMS"]:g}% e a do documento {z["picms"]:g}%. Vai assim para o C170 do SPED: corrigir.')
            if not sn and okic and p > TOL and abs(r['Base Icms'] - z['vbc']) > TOL:
                if cred_it is False: sup['Alíquota/base de ICMS diferente em TES sem crédito'] += 1
                else: add(r, z, 'Média', 'Base de ICMS divergente (ICMS confere)', 'Base ICMS', r['Base Icms'], z['vbc'], f'ICMS confere, mas a base escriturada (R$ {brl(r["Base Icms"])}) difere da do documento (R$ {brl(z["vbc"])}). Vai assim para o C170/C190: corrigir a base.')
            lvi = livro.item(r); cip = (lvi['valipi'] > TOL) if lvi is not None else tes.credita_ipi(t)
            if abs(r['Vlr.IPI'] - z['vipi']) > TOL:
                if cip is False: sup['IPI diferente do XML em TES sem crédito de IPI (não vai para o SPED)'] += 1
                elif r['Vlr.IPI'] > TOL and abs(r['Vlr.IPI'] - z['vout']) <= TOL: sup['IPI diferente do XML com total conferindo (TES sem crédito de IPI ou IPI em outro campo)'] += 1
                elif r['Vlr.IPI'] < z['vipi']:
                    if cip: add(r, z, 'Média', 'Crédito de IPI abaixo do XML', 'IPI', r['Vlr.IPI'], z['vipi'], f'A TES {t} credita IPI e escriturou R$ {brl(r["Vlr.IPI"])}, mas o documento destaca R$ {brl(z["vipi"])} ({z["pipi"]:g}%). Crédito perdido: conferir base e alíquota de IPI.')
                    else: add(r, z, 'Alta', 'IPI do XML não escriturado', 'IPI', r['Vlr.IPI'], z['vipi'], f'TES {t} não calcula IPI. Alíquota no XML: {z["pipi"]:g}%.')
                else:
                    add(r, z, 'Alta', 'Crédito de IPI acima do XML' if cip else 'IPI escriturado sem destaque no XML', 'IPI', r['Vlr.IPI'], z['vipi'],
                        f'A TES {t} credita IPI e escriturou mais do que o documento destaca: crédito indevido a estornar.' if cip else 'Rever a TES.')
            elif cip is not False and r['Vlr.IPI'] > TOL and abs(r['Vlr.Base IPI'] - z['vbcipi']) > TOL:
                add(r, z, 'Média', 'Base de IPI divergente', 'Base IPI', r['Vlr.Base IPI'], z['vbcipi'], f'IPI confere, mas a base escriturada (R$ {brl(r["Vlr.Base IPI"])}) difere da do documento (R$ {brl(z["vbcipi"])}). Vai assim para o C170 do SPED: corrigir a base de IPI.')
            if abs(r['ICMS Solid.'] - z['vicmsst']) > TOL: add(r, z, 'Alta', 'ICMS ST divergente', 'ICMS ST', r['ICMS Solid.'], z['vicmsst'], 'Rever ST na TES.')
            icomp.append(dict(sev=sevmin([d['sev'] for d in idiv[n0:]]), n=len(idiv) - n0, r=r, z=z, ref=ref, refa=refa, regime=CRTN.get(z['crt'], z['crt'])))
        for ch, g, xi in unpaired:
            for _, r in g.iterrows(): internal(r, None)
            agr.append(dict(nf=g['Documento'].iloc[0], forn=txt(g['Nome Forn.'].iloc[0]), uf=txt(g['Estado'].iloc[0]), nsd1=len(g), nxml=len(xi),
                            vsd1=float(g['Vlr.Total'].sum()), vxml=sum(z['vprod'] for z in xi), isd1=float(g['Vlr.ICMS'].sum()),
                            ixml=sum(z['vcredsn'] if z['crt'] in '14' else z['vicms'] for z in xi), ipis=float(g['Vlr.IPI'].sum()), ipix=sum(z['vipi'] for z in xi),
                            cfp=', '.join(sorted(set(g['Cod. Fiscal']))), cfx=', '.join(sorted({z['cfop'] for z in xi})),
                            cstp=', '.join(sorted(set(g['Sit.Tribut.']))), cstx=', '.join(sorted({z['orig'] + (z['cst'] or z['csosn']) for z in xi})), chave=ch))
        lk['nat'] = lk['Cod. Fiscal'].map(lambda cf: next((k_ for k_, v_ in NAT.items() if cf[1:] in v_), ''))
        for prod, g_ in lk[(lk['Produto'] != '') & (lk['nat'] != '')].groupby('Produto'):
            cnt_ = collections.Counter(g_['nat'])
            if len(cnt_) < 2: continue
            top, nt = cnt_.most_common(1)[0]
            if nt < 2 or list(cnt_.values()).count(nt) > 1: continue
            cfs = ', '.join(sorted(set(g_[g_['nat'] == top]['Cod. Fiscal'])))
            for _, r in g_[g_['nat'] != top].iterrows():
                add(r, None, 'Média', 'Produto lançado com natureza de CFOP diferente do usual', 'CFOP', r['Cod. Fiscal'], cfs,
                    f"O produto {prod} entrou {nt} vezes no período como {top} ({cfs}) e nesta nota como {r['nat']} ({r['Cod. Fiscal']}). Conferir a destinação (uso e consumo × industrialização/revenda × ativo): muda CFOP, TES e crédito.")
        semx = lk[~lk['Chave NFe'].isin(notas)]
        for _, r in semx.iterrows(): internal(r, None)
        ex = sd1[~sd1['danfe']].copy()
        def tipo(row):
            e = txt(row.get('Espec.Docum.')).upper()
            if e in ESPEC: return ESPEC[e]
            return EXCL.get(row['Cod. Fiscal'][1:], 'Outros documentos fora das DANFE (recibos, cupons, notas não eletrônicas)')
        ex['tipo'] = ex.apply(tipo, axis=1)
        exg = ex.groupby(['tipo', 'Documento', 'Serie', 'Forn/Cliente', 'Loja'], dropna=False).agg(
            itens=('Vlr.Total', 'size'), valor=('Vlr.Total', 'sum'), cfop=('Cod. Fiscal', lambda s: ', '.join(sorted(set(s)))),
            dt=('DT Digitacao', 'first'), icms=('Vlr.ICMS', 'sum')).reset_index()
        exg['dt'] = to_date(exg['dt'], sd1fmt)
        if livro.ok:
            for _, r in lk.iterrows():
                t = r['Tipo Entrada']; lv = livro.item(r); ic = r['Vlr.ICMS']
                if lv is None:
                    add(r, None, 'Média', 'Item sem registro no livro fiscal (SFT)', 'ICMS livro', ic, 0.0,
                        'Item classificado na SD1 sem linha correspondente na SFT: não vai para o SPED. Reprocessar os livros fiscais (MATA930) ou conferir o filtro da SFT.')
                    continue
                cr = tes.credita(t)
                if cr is False and lv['valicm'] > TOL and _kit(r) not in z_alta:
                    add(r, None, 'Alta', 'Crédito no livro fiscal em TES que não credita', 'ICMS livro', round(lv['valicm'], 2), 0.0,
                        f"A TES {t} não credita ICMS, mas o livro fiscal (SFT) traz R$ {brl(lv['valicm'])} de crédito: o livro diverge da TES (TES alterada depois do lançamento ou ajuste manual). Reprocessar o livro ou estornar.")
                elif cr is True and ic > TOL and lv['valicm'] <= TOL:
                    add(r, None, 'Média', 'Crédito previsto na TES fora do livro fiscal', 'ICMS livro', 0.0, ic,
                        f'A TES {t} credita ICMS e o item calculou R$ {brl(ic)}, mas o livro fiscal (SFT) está sem crédito: crédito não aproveitado. Reprocessar o livro.')
                elif lv['valicm'] > TOL and ic > TOL and abs(lv['valicm'] - ic) > TOL:
                    add(r, None, 'Média', 'ICMS do livro fiscal diferente do item', 'ICMS livro', round(lv['valicm'], 2), ic,
                        'Crédito no livro (SFT) diferente do ICMS calculado na SD1. Reprocessar o livro ou conferir ajuste manual.')
        idiv.sort(key=lambda d: (SEVO[d['sev']], d['tipo'], d['forn'], d['nf'], d['item']))
        meta = dict(nd1=len(sd1), ndanfe=len(lk), nnotas=lk['k'].nunique(), npaired=len(pairs), nsemx=len(semx), nsemxn=semx['k'].nunique(),
                    nex=len(ex), nexn=ex['k'].nunique(), tesdf=lk[['Tipo Entrada', 'Cod. Fiscal', 'Vlr.ICMS', 'Vlr.IPI', 'k']])
    log.append(f"CT-e: SF1 {int(sf1_all['cte'].sum())}, XML {len(ctes)}, casados {len(cte1)}; chaves corrigidas pelo XML: {len(fix)}")
    return dict(ccomp=ccomp, sup=sup, nct=int(sf1_all['cte'].sum()), nctx=len(ctes), nctm=len(cte1), nfix=len(fix), cfop_frete=cfop_frete,
                div=div, comp=comp, sox=sox, sos=sos, idiv=idiv, icomp=icomp, agr=agr, exg=exg, meta=meta, tes=tes, livro=livro,
                filial=filial, cnpj=cnpj, uf=uf_emp, ini=ini, fim=fim, nsf1=len(sf1), nsf1_all=len(sf1_all), nx=len(notas), nm=len(m), log=log)
