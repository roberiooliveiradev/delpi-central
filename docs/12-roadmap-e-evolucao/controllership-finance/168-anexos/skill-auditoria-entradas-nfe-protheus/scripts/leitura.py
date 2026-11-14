"""Leitura dos arquivos de entrada: relatórios do Protheus (SF1, SD1, SF4) e XML de NF-e."""
import os, re, glob, zipfile, subprocess, tempfile, shutil, io
import pandas as pd
from lxml import etree

NS = {'n': 'http://www.portalfiscal.inf.br/nfe', 'c': 'http://www.portalfiscal.inf.br/cte'}

# ----------------------------------------------------------------- Protheus
def _to_num(v):
    if v is None or (isinstance(v, float) and pd.isna(v)): return 0.0
    if isinstance(v, (int, float)): return float(v)
    s = str(v).strip()
    if not s: return 0.0
    if ',' in s and '.' in s: s = s.replace('.', '').replace(',', '.')
    elif ',' in s: s = s.replace(',', '.')
    try: return float(s)
    except ValueError: return 0.0

def _raw_table(path):
    """Devolve (DataFrame sem cabeçalho, formato_data). Lê xlsx normal, xlsx Strict OOXML (o padrão
    do relatório do Protheus) via LibreOffice, ou csv."""
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.csv', '.txt'):
        raw = open(path, 'rb').read()
        txt = raw.decode('utf-8', errors='ignore') if b'\xc3' in raw else raw.decode('latin-1')
        sep = ';' if txt.count(';') > txt.count(',') else ','
        return pd.read_csv(io.StringIO(txt), sep=sep, header=None, dtype=str), 'dayfirst'
    try:
        df = pd.read_excel(path, header=None, dtype=object)
        if df.shape[1] > 1: return df, 'excel'
    except Exception:
        pass
    tmp = tempfile.mkdtemp()
    src = os.path.join(tmp, 'in' + ext); shutil.copy(path, src)
    subprocess.run(['soffice', '--headless', '--convert-to',
                    'csv:Text - txt - csv (StarCalc):59,34,76,1,,0,false,true,false,false', '--outdir', tmp, src],
                   capture_output=True, timeout=300)
    csvp = os.path.join(tmp, 'in.csv')
    if not os.path.exists(csvp):
        raise RuntimeError(f'Não consegui ler {path} (nem como xlsx, nem convertendo com o LibreOffice).')
    return pd.read_csv(csvp, sep=';', header=None, dtype=str), 'monthfirst'

def read_protheus(path, numeric=()):
    """Lê um relatório exportado do Protheus. Acha a linha de cabeçalho (a que tem 'Filial'),
    limpa espaços e converte as colunas numéricas indicadas."""
    raw, datefmt = _raw_table(path)
    hdr = None
    for i in range(min(15, len(raw))):
        vals = [str(v).strip() for v in raw.iloc[i].tolist()]
        if 'Filial' in vals or any(v.upper().endswith('_FILIAL') for v in vals): hdr = i; break
    if hdr is None: raise RuntimeError(f'Cabeçalho com a coluna "Filial" (ou XX_FILIAL) não encontrado em {path}.')
    cols = [str(v).strip() if not pd.isna(v) else f'_col{j}' for j, v in enumerate(raw.iloc[hdr].tolist())]
    df = raw.iloc[hdr + 1:].copy(); df.columns = cols
    df = df.loc[:, ~pd.Index(cols).duplicated()]
    for c in df.columns:
        df[c] = df[c].map(lambda v: v.strip() if isinstance(v, str) else v)
    for c in numeric:
        if c in df.columns: df[c] = df[c].map(_to_num)
    df.attrs['datefmt'] = datefmt
    return df

def to_date(series, datefmt):
    if datefmt == 'excel':
        return pd.to_datetime(series, errors='coerce', dayfirst=True)
    return pd.to_datetime(series, errors='coerce', dayfirst=(datefmt == 'dayfirst'))

def txt(v):
    return '' if v is None or (isinstance(v, float) and pd.isna(v)) else str(v).strip()

# ----------------------------------------------------------------- XML
def _iter_xml_bytes(paths):
    for p in paths:
        if os.path.isdir(p):
            for f in glob.glob(os.path.join(p, '**', '*'), recursive=True):
                if f.lower().endswith('.xml'): yield f, open(f, 'rb').read()
                elif f.lower().endswith('.zip'): yield from _iter_xml_bytes([f])
        elif p.lower().endswith('.zip'):
            with zipfile.ZipFile(p) as z:
                for n in z.namelist():
                    if n.lower().endswith('.xml'): yield n, z.read(n)
                    elif n.lower().endswith('.zip'):
                        tmp = tempfile.mkdtemp(); fp = os.path.join(tmp, os.path.basename(n))
                        open(fp, 'wb').write(z.read(n)); yield from _iter_xml_bytes([fp])
        elif p.lower().endswith('.xml'):
            yield p, open(p, 'rb').read()

def _s(el, path):
    r = el.xpath('string(' + path + ')', namespaces=NS); return r.strip()

def _f(el, path):
    try: return float(_s(el, path))
    except ValueError: return 0.0

def _cte(t):
    """Lê um CT-e (procCTe/CTe, modelo 57 ou 67). Devolve dict ou None."""
    inf = t.xpath('//c:infCte', namespaces=NS)
    if not inf: return None
    inf = inf[0]; ch = inf.get('Id', '')[3:]
    if len(ch) != 44: return None
    g = lambda p: _s(t, p); f = lambda p: _f(t, p)
    ic = t.xpath('//c:imp/c:ICMS/*', namespaces=NS)
    ic = ic[0] if ic else etree.Element('x')
    grp = etree.QName(ic).localname if ic.tag != 'x' else ''
    cst = _s(ic, 'c:CST'); vbc, pic, vic = _f(ic, 'c:vBC'), _f(ic, 'c:pICMS'), _f(ic, 'c:vICMS')
    if grp == 'ICMSOutraUF':
        cst = cst or '90'; vbc, pic, vic = _f(ic, 'c:vBCOutraUF'), _f(ic, 'c:pICMSOutraUF'), _f(ic, 'c:vICMSOutraUF')
    elif grp == 'ICMS60':
        vbc, pic, vic = _f(ic, 'c:vBCSTRet'), _f(ic, 'c:pICMSSTRet'), _f(ic, 'c:vICMSSTRet')
    elif grp == 'ICMSSN':
        cst = cst or '90'; vbc = pic = vic = 0.0
    toma = g('//c:ide/c:toma3/c:toma') or g('//c:ide/c:toma03/c:toma')
    papel = {'0': 'rem', '1': 'exped', '2': 'receb', '3': 'dest'}.get(toma, '')
    cnpjde = lambda tag: g(f'//c:{tag}/c:CNPJ') or g(f'//c:{tag}/c:CPF')
    toma_cnpj = cnpjde(papel) if papel else (g('//c:ide/c:toma4/c:CNPJ') or g('//c:ide/c:toma4/c:CPF'))
    dh = g('//c:ide/c:dhEmi')
    docs = [x.strip() for x in t.xpath('//c:infDoc/c:infNFe/c:chave/text()', namespaces=NS)]
    v = f('//c:vPrest/c:vTPrest')
    return dict(
        modelo='CT-e', chave=ch, mod=g('//c:ide/c:mod'), numero=int(g('//c:ide/c:nCT') or 0), serie=g('//c:ide/c:serie'),
        emissao=pd.to_datetime(dh[:19], errors='coerce'), tpNF='', tipo='CT-e', natop=g('//c:ide/c:natOp'),
        cfop=g('//c:ide/c:CFOP'), cfops=g('//c:ide/c:CFOP'), uf_ini=g('//c:ide/c:UFIni'), uf_fim=g('//c:ide/c:UFFim'),
        emit_cnpj=g('//c:emit/c:CNPJ') or g('//c:emit/c:CPF'), emit=g('//c:emit/c:xNome'), emit_uf=g('//c:emit/c:enderEmit/c:UF'),
        crt=g('//c:emit/c:CRT'), toma=papel or ('outros' if toma_cnpj else ''), toma_cnpj=toma_cnpj,
        rem_cnpj=cnpjde('rem'), dest_cnpj=cnpjde('dest'), dest_uf=g('//c:dest/c:enderDest/c:UF'),
        grupo=grp, cst=cst, csts=cst, sn=grp == 'ICMSSN', st=grp == 'ICMS60', vBC=vbc, pICMS=pic, vICMS=vic,
        vNF=v, vTPrest=v, vIPI=0.0, docs=docs, cStat=g('//c:protCTe/c:infProt/c:cStat'))

def read_xmls(paths):
    """Lê NF-e (modelo 55), CT-e (57/67) e eventos de cancelamento. Devolve (notas, ignorados, ctes)."""
    notas, ctes, canc, ignorados = {}, {}, set(), 0
    for name, data in _iter_xml_bytes(paths):
        try: t = etree.fromstring(data)
        except Exception: ignorados += 1; continue
        if t.xpath('//c:infEvento', namespaces=NS) and not t.xpath('//c:infCte', namespaces=NS):
            if _s(t, '//c:infEvento/c:tpEvento') == '110111': canc.add(_s(t, '//c:infEvento/c:chCTe'))
            continue
        if t.xpath('//c:infCte', namespaces=NS):
            c = _cte(t)
            if c: ctes[c['chave']] = c
            else: ignorados += 1
            continue
        if t.xpath('//n:infEvento', namespaces=NS) and not t.xpath('//n:infNFe', namespaces=NS):
            if _s(t, '//n:infEvento/n:tpEvento') == '110111': canc.add(_s(t, '//n:infEvento/n:chNFe'))
            continue
        inf = t.xpath('//n:infNFe', namespaces=NS)
        if not inf or _s(t, '//n:ide/n:mod') != '55': ignorados += 1; continue
        inf = inf[0]; ch = inf.get('Id', '')[3:]
        if len(ch) != 44: continue
        crt = _s(t, '//n:emit/n:CRT')
        itens = []
        for de in t.xpath('//n:det', namespaces=NS):
            ic = de.xpath('.//n:imposto/n:ICMS/*', namespaces=NS)
            ic = ic[0] if ic else etree.Element('x')
            itens.append(dict(
                nItem=int(de.get('nItem')), cprod=_s(de, 'n:prod/n:cProd'), xprod=_s(de, 'n:prod/n:xProd'),
                ncm=_s(de, 'n:prod/n:NCM'), cfop=_s(de, 'n:prod/n:CFOP'), q=_f(de, 'n:prod/n:qCom'),
                vprod=_f(de, 'n:prod/n:vProd'), vdesc=_f(de, 'n:prod/n:vDesc'), vfrete=_f(de, 'n:prod/n:vFrete'),
                vout=_f(de, 'n:prod/n:vOutro'), orig=_s(ic, 'n:orig'), cst=_s(ic, 'n:CST'), csosn=_s(ic, 'n:CSOSN'),
                vbc=_f(ic, 'n:vBC'), picms=_f(ic, 'n:pICMS'), vicms=_f(ic, 'n:vICMS'),
                pcredsn=_f(ic, 'n:pCredSN'), vcredsn=_f(ic, 'n:vCredICMSSN'), vicmsst=_f(ic, 'n:vICMSST'),
                vipi_trib=_f(de, 'n:imposto/n:IPI/n:IPITrib/n:vIPI'), vipidevol=_f(de, 'n:impostoDevol/n:IPI/n:vIPIDevol'),
                pipi=_f(de, 'n:imposto/n:IPI/n:IPITrib/n:pIPI'), vbcipi=_f(de, 'n:imposto/n:IPI/n:IPITrib/n:vBC'),
                cstipi=_s(de, 'n:imposto/n:IPI/*/n:CST'), crt=crt))
            itens[-1]['vipi'] = itens[-1]['vipi_trib'] + itens[-1]['vipidevol']
        dh = _s(t, '//n:ide/n:dhEmi') or _s(t, '//n:ide/n:dEmi')
        tot = lambda k: _f(t, '//n:ICMSTot/n:' + k)
        notas[ch] = dict(
            chave=ch, numero=int(_s(t, '//n:ide/n:nNF') or 0), serie=_s(t, '//n:ide/n:serie'),
            emissao=pd.to_datetime(dh[:19], errors='coerce'), tpNF=_s(t, '//n:ide/n:tpNF'),
            tipo='Entrada' if _s(t, '//n:ide/n:tpNF') == '0' else 'Saída', natop=_s(t, '//n:ide/n:natOp'),
            emit_cnpj=_s(t, '//n:emit/n:CNPJ') or _s(t, '//n:emit/n:CPF'), emit=_s(t, '//n:emit/n:xNome'),
            emit_uf=_s(t, '//n:emit/n:enderEmit/n:UF'), crt=crt,
            dest_cnpj=_s(t, '//n:dest/n:CNPJ') or _s(t, '//n:dest/n:CPF'), dest_uf=_s(t, '//n:dest/n:enderDest/n:UF'),
            vProd=tot('vProd'), vFrete=tot('vFrete'), vSeg=tot('vSeg'), vDesc=tot('vDesc'), vOutro=tot('vOutro'),
            vBC=tot('vBC'), vICMS=tot('vICMS'), vST=tot('vST'), vIPI=tot('vIPI'), vIPIDevol=tot('vIPIDevol'), vNF=tot('vNF'),
            cStat=_s(t, '//n:protNFe/n:infProt/n:cStat'), itens=itens,
            cfops=', '.join(sorted({i['cfop'] for i in itens})),
            csts=', '.join(sorted({i['cst'] or i['csosn'] for i in itens})),
            credsn=round(sum(i['vcredsn'] for i in itens), 2),
            ipi_it=round(sum(i['vipi'] for i in itens), 2))
    for ch in canc:
        if ch in notas: notas[ch]['cancelada'] = True
        if ch in ctes: ctes[ch]['cancelada'] = True
    return notas, ignorados, ctes
