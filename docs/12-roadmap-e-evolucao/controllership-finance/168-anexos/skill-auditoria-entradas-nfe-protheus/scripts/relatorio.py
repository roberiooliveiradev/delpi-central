"""Gera a planilha do cruzamento no layout do escritório (cabeçalho azul, filtro, painel congelado, TOTAL)."""
import datetime as dt
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter as L

HF = Font(name='Arial', bold=True, color='FFFFFF', size=10); HFILL = PatternFill('solid', fgColor='1F4E78')
BF = Font(name='Arial', size=10); BOLD = Font(name='Arial', size=10, bold=True)
SEVF = {'Alta': 'F8CBAD', 'Depende da TES': 'E4DFEC', 'Média': 'FFE699', 'Baixa': 'DDEBF7', 'Info': 'E2EFDA', 'OK': 'E2EFDA'}
MON = '#,##0.00'
MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']

LEIT = {
 'Crédito de ICMS sem destaque no XML': 'Crédito tomado em TES que credita, sem ICMS no documento. Estornar.',
 'Crédito de ICMS acima do XML': 'Crédito acima do destacado (ou do crédito SN) em TES que credita. Estornar o excedente.',
 'ICMS calculado sem destaque no XML': 'ICMS calculado sem ICMS no documento. Só é crédito indevido se a TES creditar (aba TES).',
 'ICMS calculado acima do XML': 'ICMS calculado acima do destacado. Só é crédito a maior se a TES creditar (aba TES).',
 'ICMS calculado sem crédito (não vai para a apuração)': 'ICMS calculado no Protheus, mas sem crédito no livro fiscal (TES ou SFT em Outras/Isentas). Não entra no C190/E110.',
 'Item sem registro no livro fiscal (SFT)': 'Item da SD1 sem linha na SFT: não vai para o SPED. Reprocessar os livros (MATA930).',
 'Crédito no livro fiscal em TES que não credita': 'O livro (SFT) tem crédito que a TES não prevê: TES alterada depois ou ajuste manual. Vai para a apuração.',
 'Crédito previsto na TES fora do livro fiscal': 'A TES credita, mas o livro (SFT) está sem crédito: crédito não aproveitado.',
 'ICMS do livro fiscal diferente do item': 'Valor creditado no livro (SFT) diferente do calculado na SD1.',
 'IPI destacado no XML não escriturado': 'TES sem cálculo de IPI: o total da nota e o título ficam menores que o documento.',
 'Valor total da nota diverge': 'Total escriturado diferente do vNF. Em geral acompanha o IPI não escriturado.',
 'Base de ICMS divergente': 'Acompanha a divergência de ICMS da mesma nota.',
 'ICMS do XML não creditado': 'ICMS destacado zerado no Protheus em nota que não é só de consumo/ativo.',
 'Data de emissão divergente': 'Data digitada errada no documento de entrada.',
 'Base de ICMS divergente (ICMS confere)': 'Sem impacto no imposto.',
 'Base de ICMS em nota sem ICMS': 'Base preenchida em nota sem ICMS. Sem impacto.',
 'Acessório lançado em campo diferente (total confere)': 'Frete como despesa, ou composição de importação. Sem impacto no total.',
 'IPI classificado de outra forma (total confere)': 'Sem impacto no total.',
 'Crédito de ICMS em CFOP de uso e consumo': 'Uso e consumo creditando ICMS em TES que credita. Estornar e corrigir a TES.',
 'ICMS calculado em CFOP de uso e consumo': 'Uso e consumo com ICMS calculado. Só é crédito indevido se a TES creditar.',
 'Crédito de ICMS com CST sem tributação': 'CST 40/41/50/60 com crédito em TES que credita. Estornar.',
 'ICMS calculado com CST sem tributação': 'CST sem ICMS próprio com ICMS calculado. Depende da TES.',
 'Crédito de IPI em material de uso e consumo': 'TES de material de consumo creditando IPI. IPI só gera crédito em MP, PI e embalagem.',
 'Crédito do Simples não aproveitado (TES sem crédito)': 'Compra para industrialização/revenda de fornecedor do Simples com crédito SN no XML, em TES que não credita.',
 'ICMS destacado não creditado em insumo/revenda (TES sem crédito)': 'CFOP com direito a crédito em TES que não credita.',
 'IPI do XML não escriturado': 'TES sem cálculo de IPI.',
 'NF de entrada do fornecedor lançada como compra': 'XML com CFOP de entrada emitido pelo fornecedor: a empresa é remetente.',
 'Item com ST no XML lançado em CFOP sem ST': 'Itens com ICMS-ST lançados em CFOP sem ST: o correto é x407 (uso e consumo), x403 (revenda), x401 (industrialização) ou x406 (ativo).',
 'CFOP de ST sem ST no XML': 'CFOP de ST em item sem ST no documento.',
 'CST diverge do documento': 'Tributação lançada diferente da nota (ex.: CST 61 de combustível gravado como 60).',
 'Origem da mercadoria divergente': 'Primeiro dígito do CST diferente do XML. Impacta a regra dos 4% e o cadastro do produto.',
 'CST 90 no lugar do CST do documento (TES sem crédito)': 'Padrão das TES sem crédito. Não muda imposto, mas o SPED sai com CST diferente da nota.',
 'CFOP de entrada incompatível com a UF do fornecedor': 'Primeiro dígito do CFOP não bate com a UF (1 interna, 2 interestadual, 3 exterior).',
 'Alíquota de crédito SN acima do teto do Simples': 'pCredSN acima do máximo possível dentro do sublimite (3,94% indústria / 3,98% comércio): fornecedor acima do sublimite ou cálculo errado.',
 'Fornecedor do Simples perto do sublimite': 'pCredSN indica faturamento (RBT12) a partir de R$ 3 mi. Acompanhar.',
 'CSOSN com permissão de crédito sem alíquota informada': 'CSOSN 101/201 sem pCredSN: sem alíquota no documento não há crédito.',
 'Indústria do Simples (SC) fora da TES de crédito presumido': 'Compra interna de indústria do Simples de SC fora da TES do presumido: fornecedor sem cadastro no Configurador de Tributos.',
 'Crédito presumido com fornecedor acima do sublimite': 'Presumido de 7% em fornecedor com pCredSN acima do teto: possível sublimite ultrapassado.',
 'Valor no item diferente do crédito presumido de 7%': 'Valor calculado no item diferente de 7% do valor da aquisição.',
 'TES de crédito presumido em nota sem direito': 'TES do presumido usada em nota que não é de indústria do Simples de SC.',
 'Natureza do CFOP incompatível com o documento': 'Compra, transferência, devolução, conserto etc. lançada em CFOP de outra natureza.',
 'Chave de acesso divergente do XML': 'Chave digitada diferente da do XML de mesmo número e valor. O SPED leva um documento que não existe.',
 'Documento eletrônico sem chave de acesso': 'Espécie eletrônica (SPED, CTE, NF3E...) lançada sem a chave.',
 'Chave de acesso inválida': 'Dígito verificador não confere: chave digitada errada.',
 'Chave de acesso não confere com o número do documento': 'O número embutido na chave é outro (sem XML para comparar).',
 'Série divergente da chave de acesso': 'A série embutida na chave é outra (sem XML para comparar).',
 'Espécie do documento incompatível com a chave': 'Modelo da chave (55 NF-e, 57 CT-e, 66 NF3e, 62 NFCom) diferente da espécie lançada.',
 'Fornecedor do lançamento com CNPJ diferente do emitente': 'Código/loja do fornecedor de outro CNPJ: participante errado no SPED e título no fornecedor errado.',
 'Série divergente do XML': 'Série digitada diferente da do documento.',
 'Produto lançado com natureza de CFOP diferente do usual': 'Mesmo produto entrando como consumo, insumo ou ativo em notas diferentes: conferir a destinação.',
 'Base de IPI divergente': 'IPI confere, mas a base escriturada difere da do documento (C170).',
 'Crédito de IPI abaixo do XML': 'TES que credita IPI com valor menor que o destacado: crédito perdido.',
 'Crédito de IPI acima do XML': 'TES que credita IPI com valor maior que o destacado: estornar.',
 'Alíquota de ICMS divergente (valor confere)': 'Valor confere, mas a alíquota gravada difere (C170).',
 'CT-e: valor da prestação diverge': 'Valor escriturado diferente do vTPrest do CT-e.',
 'CT-e: CFOP divergente': 'Frete de estabelecimento industrial: 1352 quando o transporte começa na UF da empresa, 2352 quando começa em outra UF.',
 'CT-e: crédito de ICMS em frete sem direito': 'Frete de uso e consumo/ativo ou CT-e sem ICMS lançado em TES que credita: zerar base, alíquota e ICMS, CST 090.',
 'CT-e: ICMS do frete não creditado': 'Frete com direito a crédito (venda ou compra de insumo) em TES sem crédito: lançar base, alíquota e ICMS do CT-e.',
 'CT-e: crédito de ICMS acima do XML': 'Crédito maior que o ICMS do CT-e.',
 'CT-e: crédito de ICMS abaixo do XML': 'Crédito menor que o ICMS do CT-e.',
 'CT-e: alíquota de ICMS divergente': 'Alíquota escriturada diferente da do CT-e.',
 'CT-e: base de ICMS divergente': 'Base escriturada diferente da do CT-e.',
 'CT-e: CST divergente': 'Com crédito, CST do CT-e (000); sem crédito, 090.',
 'CT-e: ICMS calculado em frete sem direito': 'TES com crédito e livro desencontrados: só a SFT diz se foi para o SPED.',
 'CT-e: ICMS calculado diferente do XML': 'TES com crédito e livro desencontrados: só a SFT diz se foi para o SPED.',
 'CT-e escriturado sem a empresa ser a tomadora': 'O tomador do CT-e é outro CNPJ: só o tomador escritura e credita.',
}

def table(ws, headers, rows, widths, money=(), dates=(), text=(), total=None, sevcol=None, wrap=('O que fazer', 'Motivo / leitura', 'Leitura')):
    ws.append(headers)
    for c in range(1, len(headers) + 1):
        cell = ws.cell(1, c); cell.font = HF; cell.fill = HFILL; cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    ws.row_dimensions[1].height = 30
    for r in rows: ws.append(r)
    n = ws.max_row
    for row in ws.iter_rows(min_row=2, max_row=n):
        for c in row:
            c.font = BF; h = headers[c.column - 1]
            if h in money or (isinstance(c.value, float) and h.startswith('Valor')): c.number_format = MON
            if h in dates: c.number_format = 'dd/mm/yyyy hh:mm' if isinstance(c.value, dt.datetime) and (c.value.hour or c.value.minute) else 'dd/mm/yyyy'
            if h in text: c.number_format = '@'
            c.alignment = Alignment(wrap_text=h in wrap, vertical='top')
        if sevcol:
            s = row[sevcol - 1]; s.fill = PatternFill('solid', fgColor=SEVF.get(s.value, 'FFFFFF')); s.font = BOLD
    for i, w in enumerate(widths, 1): ws.column_dimensions[L(i)].width = w
    ws.auto_filter.ref = f'A1:{L(len(headers))}{max(n,2)}'; ws.freeze_panes = 'C2' if sevcol else 'B2'
    if total and n > 1:
        tr = n + 2; ws.cell(tr, 1, 'TOTAL').font = BOLD
        for h in total:
            c = headers.index(h) + 1; col = L(c)
            cell = ws.cell(tr, c, f'=SUBTOTAL(109,{col}2:{col}{n})'); cell.font = BOLD; cell.number_format = MON
    return n

def _py(d):
    return d.to_pydatetime() if isinstance(d, pd.Timestamp) and pd.notna(d) else (None if isinstance(d, pd.Timestamp) else d)

def gerar(R, out_path):
    wb = Workbook(); tes = R['tes']; temitens = bool(R['meta'])
    # ---------------- Divergências (cabeçalho)
    ws = wb.active; ws.title = 'Divergências'
    H = ['Severidade', 'Ocorrência', 'NF', 'Série', 'Fornecedor (XML)', 'UF', 'Emissão XML', 'Campo', 'Valor Protheus', 'Valor XML', 'Diferença (Protheus − XML)', 'Regime do emitente', 'CST/CSOSN no XML', 'CFOP no XML', 'TES (SD1)', 'O que fazer', 'Chave de Acesso']
    rows = []
    for i, d in enumerate(R['div'], start=2):
        num = isinstance(d['vp'], (int, float)) and isinstance(d['vx'], (int, float))
        rows.append([d['sev'], d['tipo'], d['nf'], d['serie'], d['forn'], d['uf'], _py(d['emi']), d['campo'], d['vp'], d['vx'], f'=I{i}-J{i}' if num else None, d['crt'], d['cst'], d['cfop'], d['tes'], d['acao'], d['chave']])
    table(ws, H, rows, [13, 34, 11, 6, 34, 5, 15, 13, 14, 14, 15, 16, 13, 13, 10, 70, 47], money=('Valor Protheus', 'Valor XML', 'Diferença (Protheus − XML)'), dates=('Emissão XML',), text=('NF', 'Série', 'CST/CSOSN no XML', 'CFOP no XML', 'TES (SD1)', 'Chave de Acesso'), sevcol=1)
    # ---------------- Comparativo
    wc = wb.create_sheet('Comparativo')
    H2 = ['Situação', 'NF', 'Série', 'Fornecedor (XML)', 'UF', 'Emissão XML', 'Regime do emitente', 'CST/CSOSN XML', 'CFOP XML', 'Mercadoria Protheus', 'Mercadoria XML', 'Base ICMS Protheus', 'Base ICMS XML', 'ICMS Protheus', 'ICMS XML (ou crédito SN)', 'Dif. ICMS', 'IPI Protheus', 'IPI XML', 'Total Protheus', 'Total XML', 'Dif. Total', 'TES (SD1)', 'Ocorrências', 'Chave de Acesso']
    rows = []
    for i, c in enumerate(R['comp'], start=2):
        r, n = c['r'], c['n']
        rows.append([c['sev'], r['Numero'], r['Serie'], n['emit'], n['emit_uf'], _py(n['emissao']), {'1': 'Simples Nacional', '3': 'Regime normal', '4': 'MEI', '2': 'Simples (excesso)'}.get(n['crt'], n['crt']), n['csts'], n['cfops'],
                     r['Vlr.Mercad'], n['vProd'], r['Base p/ICMS'], n['vBC'], r['Vlr.ICMS'], c['ref'], f'=N{i}-O{i}', r['Vlr.IPI'], c['ipix'], r['Vlr.Bruto'], n['vNF'], f'=S{i}-T{i}', c['tes'], c['ndiv'], r['Chave NFe']])
    mny = tuple(H2[9:21])
    table(wc, H2, rows, [11, 11, 6, 34, 5, 15, 16, 12, 12] + [14] * 12 + [10, 11, 47], money=mny, dates=('Emissão XML',), text=('NF', 'Série', 'CST/CSOSN XML', 'CFOP XML', 'TES (SD1)', 'Chave de Acesso'), total=mny, sevcol=1)
    # ---------------- Só no XML
    wx = wb.create_sheet('Só no XML')
    H3 = ['Situação', 'NF', 'Série', 'Emissão', 'Emitente', 'CNPJ Emitente', 'UF', 'Tipo', 'Natureza da Operação', 'CFOP', 'CST/CSOSN', 'Vlr Total NF', 'Base ICMS', 'Vlr ICMS', 'Vlr IPI', 'Motivo / leitura', 'Chave de Acesso']
    rows = [[s['sev'], s['n']['numero'], s['n']['serie'], _py(s['n']['emissao']), s['n']['emit'], s['n']['emit_cnpj'], s['n']['emit_uf'], s['n']['tipo'], s['n']['natop'], s['n']['cfops'], s['n']['csts'], s['n']['vNF'], s['n']['vBC'], s['n']['vICMS'], s['n']['vIPI'], s['mot'], s['n']['chave']] for s in R['sox']]
    table(wx, H3, rows, [10, 10, 6, 15, 34, 16, 5, 8, 34, 11, 11, 14, 14, 13, 12, 60, 47], money=('Vlr Total NF', 'Base ICMS', 'Vlr ICMS', 'Vlr IPI'), dates=('Emissão',), text=('CNPJ Emitente', 'Série', 'CFOP', 'CST/CSOSN', 'Chave de Acesso'), total=('Vlr Total NF', 'Base ICMS', 'Vlr ICMS', 'Vlr IPI'), sevcol=1)
    # ---------------- Só no SF1
    wsf = wb.create_sheet('Só no SF1')
    H4 = ['Situação', 'NF', 'Série', 'Emissão', 'Dt. Receb.', 'Fornecedor', 'Cód./Loja', 'UF', 'Vlr Bruto', 'Base ICMS', 'Vlr ICMS', 'Vlr IPI', 'Motivo / leitura', 'Chave NF-e']
    rows = [[s['sev'], s['r']['Numero'], s['r']['Serie'], _py(s['r']['dEmi']), _py(s['r']['dRec']), s['r']['Nome Forn.'], f"{s['r']['Fornecedor']}/{s['r']['Loja']}", s['r']['Estado'], s['r']['Vlr.Bruto'], s['r']['Base p/ICMS'], s['r']['Vlr.ICMS'], s['r']['Vlr.IPI'], s['mot'], s['r']['Chave NFe']] for s in R['sos']]
    table(wsf, H4, rows, [10, 11, 6, 12, 12, 26, 12, 5, 14, 14, 13, 12, 60, 47], money=('Vlr Bruto', 'Base ICMS', 'Vlr ICMS', 'Vlr IPI'), dates=('Emissão', 'Dt. Receb.'), text=('NF', 'Série', 'Cód./Loja', 'Chave NF-e'), total=('Vlr Bruto', 'Base ICMS', 'Vlr ICMS', 'Vlr IPI'), sevcol=1)
    # ---------------- CT-e
    if R.get('ccomp'):
        wct = wb.create_sheet('CT-e Comparativo')
        HCT = ['Situação', 'CT-e', 'Série', 'Transportadora', 'UF', 'Emissão', 'Trajeto', 'Tomador', 'Direito ao crédito', 'Motivo', 'CFOP CT-e', 'CFOP Protheus', 'CFOP esperado', 'TES', 'Crédito no Protheus',
               'CST XML', 'CST Protheus', 'Base Protheus', 'Base XML', 'Alíq. Protheus', 'Alíq. XML', 'ICMS Protheus', 'ICMS XML', 'Dif. ICMS', 'Valor Protheus', 'Valor XML', 'Ocorrências', 'Chave de Acesso']
        sn = {True: 'Sim', False: 'Não', None: 'Indefinido'}
        rows = []
        for i, c in enumerate(R['ccomp'], start=2):
            r, x = c['r'], c['c']
            rows.append([c['sev'], r['Numero'], r['Serie'], x['emit'], x['emit_uf'], _py(x['emissao']), f"{x['uf_ini']} → {x['uf_fim']}", x['toma'], sn[c['dir']], c['mot'], x['cfop'], c['cfps'], c['exp'], c['tes'], sn[c['cr']],
                         c['xcst'], c['csts'], c['bc'], x['vBC'], c['al'], x['pICMS'], c['ic'], x['vICMS'], f'=V{i}-W{i}', r['Vlr.Bruto'], x['vTPrest'], c['ndiv'], r['Chave NFe']])
        mny = ('Base Protheus', 'Base XML', 'ICMS Protheus', 'ICMS XML', 'Dif. ICMS', 'Valor Protheus', 'Valor XML')
        table(wct, HCT, rows, [11, 10, 6, 30, 5, 12, 10, 9, 11, 40, 9, 11, 10, 8, 11, 8, 10, 13, 13, 8, 8, 13, 13, 12, 13, 13, 10, 47], money=mny, dates=('Emissão',),
              text=('CT-e', 'Série', 'CFOP CT-e', 'CFOP Protheus', 'CFOP esperado', 'TES', 'CST XML', 'CST Protheus', 'Chave de Acesso'), total=mny, sevcol=1, wrap=('Motivo',))
    # ---------------- Itens
    if temitens:
        wi = wb.create_sheet('Itens Divergências')
        HI = ['Severidade', 'Ocorrência', 'NF', 'Série', 'Fornecedor', 'UF', 'Item SD1', 'Item XML', 'Produto', 'Descrição (XML)', 'Campo', 'Valor Protheus', 'Valor XML', 'Diferença (Protheus − XML)', 'CFOP Protheus', 'CFOP XML', 'CST Protheus', 'CST XML', 'TES', 'O que fazer', 'Chave de Acesso']
        rows = []
        for i, d in enumerate(R['idiv'], start=2):
            num = isinstance(d['vp'], (int, float)) and isinstance(d['vx'], (int, float))
            rows.append([d['sev'], d['tipo'], d['nf'], d['serie'], d['forn'], d['uf'], d['item'], d['nitem'], d['prod'], d['desc'], d['campo'], d['vp'], d['vx'], f'=L{i}-M{i}' if num else None, d['cfop_p'], d['cfop_x'], d['cst_p'], d['cst_x'], d['tes'], d['acao'], d['chave']])
        table(wi, HI, rows, [13, 36, 11, 6, 24, 5, 8, 8, 12, 30, 11, 13, 13, 14, 10, 10, 10, 10, 7, 70, 47], money=('Diferença (Protheus − XML)',), text=('NF', 'Série', 'Item SD1', 'Produto', 'CFOP Protheus', 'CFOP XML', 'CST Protheus', 'CST XML', 'TES', 'Chave de Acesso'), sevcol=1)
        for row in wi.iter_rows(min_row=2, max_row=wi.max_row):
            for c in (row[11], row[12]):
                if isinstance(c.value, (int, float)): c.number_format = MON
        wic = wb.create_sheet('Itens Comparativo')
        HC = ['Situação', 'NF', 'Série', 'Fornecedor', 'UF', 'Item SD1', 'Item XML', 'Produto', 'Descrição (XML)', 'NCM', 'Regime emitente', 'CFOP XML', 'CFOP Protheus', 'TES', 'CST XML', 'CST Protheus', 'Vlr Item Protheus', 'Vlr Item XML', 'Base ICMS Protheus', 'Base ICMS XML', 'Alíq. Protheus', 'Alíq. XML (ou SN)', 'ICMS Protheus', 'ICMS XML (ou crédito SN)', 'Dif. ICMS', 'IPI Protheus', 'IPI XML', 'Ocorrências', 'Chave de Acesso']
        rows = []
        for i, c in enumerate(R['icomp'], start=2):
            r, z = c['r'], c['z']
            rows.append([c['sev'], r['Documento'], r['Serie'], r['Nome Forn.'], r['Estado'], r['Item NF'], z['nItem'], r['Produto'], z['xprod'], z['ncm'], c['regime'], z['cfop'], r['Cod. Fiscal'], r['Tipo Entrada'],
                         z['orig'] + (z['cst'] or z['csosn']), r['Sit.Tribut.'], r['Vlr.Total'], z['vprod'], r['Base Icms'], z['vbc'], r['Aliq. ICMS'], c['refa'], r['Vlr.ICMS'], c['ref'], f'=W{i}-X{i}', r['Vlr.IPI'], z['vipi'], c['n'], r['Chave NFe']])
        mny = ('Vlr Item Protheus', 'Vlr Item XML', 'Base ICMS Protheus', 'Base ICMS XML', 'ICMS Protheus', 'ICMS XML (ou crédito SN)', 'Dif. ICMS', 'IPI Protheus', 'IPI XML')
        table(wic, HC, rows, [11, 11, 6, 24, 5, 8, 8, 12, 30, 10, 12, 9, 9, 7, 9, 9] + [13] * 4 + [8, 8] + [13] * 5 + [10, 47], money=mny, text=('NF', 'Série', 'Item SD1', 'Produto', 'NCM', 'CFOP XML', 'CFOP Protheus', 'TES', 'CST XML', 'CST Protheus', 'Chave de Acesso'), total=mny, sevcol=1)
        wa = wb.create_sheet('Itens Agrupados')
        HA = ['NF', 'Fornecedor', 'UF', 'Itens SD1', 'Itens XML', 'Valor SD1', 'Valor XML', 'ICMS SD1', 'ICMS XML', 'IPI SD1', 'IPI XML', 'CFOP Protheus', 'CFOP XML', 'CST Protheus', 'CST XML', 'Leitura', 'Chave de Acesso']
        rows = [[a['nf'], a['forn'], a['uf'], a['nsd1'], a['nxml'], a['vsd1'], a['vxml'], a['isd1'], a['ixml'], a['ipis'], a['ipix'], a['cfp'], a['cfx'], a['cstp'], a['cstx'],
                 'Itens agrupados ou desmembrados no lançamento; conferência só por nota. ' + ('Total confere.' if abs(a['vsd1'] - a['vxml']) <= 0.05 else 'Total DIVERGE: conferir.'), a['chave']] for a in R['agr']]
        table(wa, HA, rows, [11, 26, 5, 9, 9, 13, 13, 12, 12, 11, 11, 13, 13, 13, 18, 50, 47], money=('Valor SD1', 'Valor XML', 'ICMS SD1', 'ICMS XML', 'IPI SD1', 'IPI XML'), text=('NF', 'CFOP Protheus', 'CFOP XML', 'CST Protheus', 'CST XML', 'Chave de Acesso'))
        we = wb.create_sheet('Itens Excluídos')
        HE = ['Tipo de documento', 'Documento', 'Série', 'Fornecedor', 'Loja', 'CFOP', 'Itens', 'Valor', 'ICMS', 'Dt. Digitação']
        e = R['exg'].sort_values(['tipo', 'Documento'])
        rows = [[r['tipo'], r['Documento'], r['Serie'], r['Forn/Cliente'], r['Loja'], r['cfop'], int(r['itens']), float(r['valor']), float(r['icms']), _py(r['dt'])] for _, r in e.iterrows()]
        table(we, HE, rows, [52, 12, 6, 11, 6, 12, 7, 14, 12, 12], money=('Valor', 'ICMS'), dates=('Dt. Digitação',), text=('Documento', 'Série', 'Fornecedor', 'Loja', 'CFOP'), total=('Itens', 'Valor', 'ICMS'))
        # ---------------- TES
        wt = wb.create_sheet('TES usadas' if tes.ok else 'TES a confirmar', 0)
        td = R['meta']['tesdf']
        if tes.ok:
            HT = ['TES', 'Descrição (SF4)', 'CFOPs de entrada', 'Itens DANFE', 'Notas', 'Calcula ICMS', 'Credita ICMS', 'Livro ICMS', 'CST na TES', 'Material de consumo', 'Calcula IPI', 'Credita IPI', 'Livro IPI', 'ICMS calculado nos itens', 'IPI escriturado nos itens', 'Crédito de ICMS indevido', 'Crédito de IPI indevido', 'Crédito × livro na TES']
            rows = []
            for i, (t, g) in enumerate(sorted(td.groupby('Tipo Entrada')), start=2):
                G = tes.g
                rows.append([t, G(t, 'Txt Padrao') if t in tes.f4 else 'NÃO ESTÁ NA SF4 — reenviar a SF4', ', '.join(sorted(set(g['Cod. Fiscal']))), len(g), g['k'].nunique(), G(t, 'Calcula ICMS'), G(t, 'Cred. ICMS ?'), G(t, 'L.Fisc. ICMS'), G(t, 'Sit.Trib.ICM'), G(t, 'Mat.Consumo'), G(t, 'Calcula IPI?'), G(t, 'Credita IPI?'), G(t, 'L.Fiscal IPI'),
                             float(g['Vlr.ICMS'].sum()), float(g['Vlr.IPI'].sum()),
                             f"=SUMIFS('Itens Divergências'!$L:$L,'Itens Divergências'!$S:$S,A{i},'Itens Divergências'!$A:$A,\"Alta\",'Itens Divergências'!$K:$K,\"ICMS\")",
                             f'=IF(AND(L{i}="Sim",J{i}="Sim"),O{i},0)', ('; '.join(tes.incoerencias(t)) + '. Só a SFT diz o que foi para o SPED.') if tes.incoerencias(t) else ('OK' if t in tes.f4 else '')])
            mm = ('ICMS calculado nos itens', 'IPI escriturado nos itens', 'Crédito de ICMS indevido', 'Crédito de IPI indevido')
            n = table(wt, HT, rows, [7, 30, 20, 8, 7, 9, 9, 10, 8, 10, 9, 9, 10, 14, 14, 14, 14, 44], money=mm, text=('TES', 'CST na TES'), total=mm)
            RED = PatternFill('solid', fgColor='F8CBAD')
            for rr in range(2, n + 1):
                if wt.cell(rr, 12).value == 'Sim' and wt.cell(rr, 10).value == 'Sim':
                    for cc in (10, 12): wt.cell(rr, cc).fill = RED
                if wt.cell(rr, 18).value not in (None, '', 'OK'):
                    for cc in (7, 8, 11, 12, 13, 18): wt.cell(rr, cc).fill = RED
                    wt.cell(rr, 18).alignment = Alignment(wrap_text=True, vertical='top')
            nota = R.get('sf4_fonte', 'SF4') + '. Crédito de IPI indevido = TES de material de consumo com Credita IPI = Sim. Crédito de ICMS indevido = ICMS acima do XML, sem destaque ou em uso e consumo dentro de TES que credita. Coluna R: TES com crédito e livro fiscal desencontrados (o que vai para o SPED depende da SFT).'
        else:
            HT = ['TES', 'CFOPs de entrada', 'Itens DANFE', 'Notas', 'ICMS calculado (todos os itens)', 'ICMS em itens que dependem da TES', 'Credita ICMS? (S/N)', 'Livro ICMS (T/I/O/N)', 'Crédito indevido confirmado']
            rows = []
            for i, (t, g) in enumerate(sorted(td.groupby('Tipo Entrada')), start=2):
                rows.append([t, ', '.join(sorted(set(g['Cod. Fiscal']))), len(g), g['k'].nunique(), float(g['Vlr.ICMS'].sum()),
                             f"=SUMIFS('Itens Divergências'!$L:$L,'Itens Divergências'!$S:$S,A{i},'Itens Divergências'!$A:$A,\"Depende da TES\")", None, None, f'=IF(UPPER(G{i})="S",F{i},0)'])
            mm = ('ICMS calculado (todos os itens)', 'ICMS em itens que dependem da TES', 'Crédito indevido confirmado')
            n = table(wt, HT, rows, [8, 26, 10, 8, 16, 18, 12, 12, 16], money=mm, text=('TES',), total=mm)
            for rr in range(2, n + 1):
                for cc in (7, 8):
                    c = wt.cell(rr, cc); c.fill = PatternFill('solid', fgColor='FFF2CC'); c.font = Font(name='Arial', size=10, color='0000FF')
            nota = 'SF4 não informada. Preencha as colunas amarelas (G: S se a TES credita ICMS, F4_CREDICM; H: livro, F4_LFICM). A coluna I soma o crédito indevido das TES marcadas com S.'
        c = wt.cell(n + 4, 1, nota); c.font = Font(name='Arial', size=9, italic=True); c.alignment = Alignment(wrap_text=True, vertical='top')
        wt.merge_cells(start_row=n + 4, start_column=1, end_row=n + 4, end_column=9); wt.row_dimensions[n + 4].height = 32
    # ---------------- Resumo
    wr = wb.create_sheet('Resumo', 0)
    for col, w in zip('ABCDE', (56, 15, 13, 18, 70)): wr.column_dimensions[col].width = w
    def hdr(row, vals):
        for j, v in enumerate(vals, 1):
            c = wr.cell(row, j, v); c.font = HF; c.fill = HFILL; c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        wr.row_dimensions[row].height = 30
    per = f"{MESES[R['ini'].month-1]}/{R['ini'].year}" if pd.notna(R['ini']) else ''
    wr['A1'] = f"Cruzamento SF1/SD1 (Protheus) × XML de NF-e e CT-e — Filial {R['filial']}, {per}"; wr['A1'].font = Font(name='Arial', size=14, bold=True, color='1F4E78')
    wr['A2'] = (f"CNPJ {R['cnpj']} ({R['uf']}). SF1 por data de recebimento ({R['ini']:%d/%m/%Y} a {R['fim']:%d/%m/%Y}); XML por data de emissão. "
                f"Casamento pela chave de acesso (NF-e modelo 55 e CT-e 57/67; chave errada é corrigida pelo XML de mesmo número e valor). Tolerância de R$ 0,05. {R.get('sf4_fonte', '')}. {R.get('sft_fonte', '')}"
                + (' ATENÇÃO: ' + ' '.join(R.get('sf4_avisos', [])) if R.get('sf4_avisos') else ''))
    wr['A2'].font = Font(name='Arial', size=9, italic=True); wr.merge_cells('A2:E2'); wr['A2'].alignment = Alignment(wrap_text=True); wr.row_dimensions[2].height = 28 if not R.get('sf4_avisos') else 56
    if R.get('sf4_avisos'): wr['A2'].font = Font(name='Arial', size=9, italic=True, bold=True, color='C00000')
    r = 4; hdr(r, ['Base (cabeçalho)', 'Notas', '', '', ''])
    base = [('Notas na SF1 (todas as espécies)', R['nsf1_all']), ('DANFE na SF1', R['nsf1']), ('XML de NF-e lidos', R['nx']), ('Casadas pela chave', R['nm']),
            ('Casadas sem nenhuma divergência', '=COUNTIF(Comparativo!A:A,"OK")'), ('CT-e na SF1', R.get('nct', 0)), ('XML de CT-e lidos', R.get('nctx', 0)), ('CT-e casados pela chave', R.get('nctm', 0)),
            ('Chaves digitadas erradas e corrigidas pelo XML', R.get('nfix', 0)), ('Só no XML (NF-e e CT-e)', "=COUNTA('Só no XML'!B:B)-1"), ('Só no SF1 (sem XML)', "=COUNTA('Só no SF1'!B:B)-1")]
    for k, (a, b) in enumerate(base, start=r + 1): wr.cell(k, 1, a).font = BF; wr.cell(k, 2, b).font = BOLD
    r += len(base) + 2
    def bloco(r, titulo, aba, divs, sumcol):
        hdr(r, [titulo, 'Severidade', 'Ocorrências', 'Diferença (Protheus − XML)', 'Leitura'])
        seen = []
        for d in divs:
            if (d['tipo'], d['sev']) not in seen: seen.append((d['tipo'], d['sev']))
        for k, (t, s) in enumerate(seen, start=r + 1):
            wr.cell(k, 1, t).font = BF; c = wr.cell(k, 2, s); c.font = BOLD; c.fill = PatternFill('solid', fgColor=SEVF[s])
            wr.cell(k, 3, f"=COUNTIFS('{aba}'!$B:$B,A{k},'{aba}'!$A:$A,B{k})").font = BF
            c = wr.cell(k, 4, f"=SUMIFS('{aba}'!${sumcol}:${sumcol},'{aba}'!$B:$B,A{k},'{aba}'!$A:$A,B{k})"); c.font = BF; c.number_format = MON
            c = wr.cell(k, 5, LEIT.get(t, '')); c.font = BF; c.alignment = Alignment(wrap_text=True, vertical='top')
        if not seen: wr.cell(r + 1, 1, 'Nenhuma ocorrência.').font = BF
        return r + max(len(seen), 1) + 2
    r = bloco(r, 'Ocorrência (cabeçalho)', 'Divergências', R['div'], 'K')
    def impactos(r, titulo, itens):
        hdr(r, [titulo, '', '', 'Valor (R$)', 'Como foi calculado'])
        for k, (a, f, c_) in enumerate(itens, start=r + 1):
            wr.cell(k, 1, a).font = BF; c = wr.cell(k, 4, f); c.font = BOLD; c.number_format = MON
            c = wr.cell(k, 5, c_); c.font = BF; c.alignment = Alignment(wrap_text=True, vertical='top')
        return r + len(itens) + 2
    r = impactos(r, 'Impacto financeiro (cabeçalho)', [
        ('Crédito de ICMS indevido (TES que creditam)', "=SUMIFS('Divergências'!$K:$K,'Divergências'!$A:$A,\"Alta\",'Divergências'!$H:$H,\"ICMS\")", 'ICMS acima do XML ou sem destaque em notas cuja TES credita.'),
        ('ICMS calculado que depende da TES (potencial)', "=SUMIFS('Divergências'!$K:$K,'Divergências'!$A:$A,\"Depende da TES\",'Divergências'!$H:$H,\"ICMS\")", 'Só existe quando não há SF4 ou SD1 para decidir.'),
        ('CT-e: crédito de ICMS indevido', "=SUMIFS('Divergências'!$K:$K,'Divergências'!$B:$B,\"CT-e: crédito de ICMS em frete sem direito\")+SUMIFS('Divergências'!$K:$K,'Divergências'!$B:$B,\"CT-e: crédito de ICMS acima do XML\")", 'Frete sem direito creditado ou crédito acima do CT-e.'),
        ('CT-e: crédito de ICMS não aproveitado', "=-SUMIFS('Divergências'!$K:$K,'Divergências'!$B:$B,\"CT-e: ICMS do frete não creditado\")-SUMIFS('Divergências'!$K:$K,'Divergências'!$B:$B,\"CT-e: crédito de ICMS abaixo do XML\")", 'Frete de venda ou de compra de insumo lançado sem crédito ou com crédito menor.'),
        ('IPI destacado e não escriturado', "=-SUMIFS('Divergências'!$K:$K,'Divergências'!$B:$B,\"IPI destacado no XML não escriturado\")", 'IPI do documento que não entrou no total do Protheus.'),
        ('ICMS em XML ainda não escriturados', "=SUMIFS('Só no XML'!N:N,'Só no XML'!A:A,\"Média\")", 'ICMS destacado nas notas de terceiros sem lançamento.')])
    if temitens:
        wr.cell(r, 1, 'Conferência item a item (SD1 × XML)').font = Font(name='Arial', size=12, bold=True, color='1F4E78'); r += 1
        M = R['meta']; hdr(r, ['Base (itens)', 'Itens', 'Notas', '', ''])
        base = [('Itens na SD1 da filial', M['nd1'], None), ('Excluídos (CT-e, serviço, NFCom, NF3e e outros não DANFE)', M['nex'], M['nexn']),
                ('Itens de DANFE', M['ndanfe'], M['nnotas']), ('Pareados item a item com o XML', M['npaired'], None),
                ('Em notas com itens agrupados (conferidos por nota)', sum(a['nsd1'] for a in R['agr']), len(R['agr'])),
                ('Sem XML no download (só coerência interna)', M['nsemx'], M['nsemxn']),
                ('Itens pareados sem nenhuma ocorrência', "=COUNTIF('Itens Comparativo'!A:A,\"OK\")", None)]
        for k, (a, b, c) in enumerate(base, start=r + 1):
            wr.cell(k, 1, a).font = BF; wr.cell(k, 2, b).font = BOLD
            if c is not None: wr.cell(k, 3, c).font = BF
        r += len(base) + 2
        r = bloco(r, 'Ocorrência (itens)', 'Itens Divergências', R['idiv'], 'N')
        ab = 'Itens Divergências'
        r = impactos(r, 'Impacto financeiro (itens)', [
            ('Crédito de ICMS indevido (TES ou livro que creditam)', f"=SUMIFS('{ab}'!$L:$L,'{ab}'!$A:$A,\"Alta\",'{ab}'!$K:$K,\"ICMS\")", 'ICMS creditado em uso e consumo, sem destaque ou com CST sem tributação. Com SFT, o valor é o do livro fiscal.'),
            ('Crédito de IPI indevido em uso e consumo', f"=SUMIFS('{ab}'!$L:$L,'{ab}'!$B:$B,\"Crédito de IPI em material de uso e consumo\")", 'IPI escriturado em TES de material de consumo que credita IPI.'),
            ('Crédito do Simples não aproveitado', f"=SUMIFS('{ab}'!$M:$M,'{ab}'!$B:$B,\"Crédito do Simples não aproveitado (TES sem crédito)\")", 'vCredICMSSN do XML em compra para industrialização/revenda em TES sem crédito.'),
            ('ICMS destacado não creditado em insumo/revenda', f"=SUMIFS('{ab}'!$M:$M,'{ab}'!$B:$B,\"ICMS destacado não creditado em insumo/revenda (TES sem crédito)\")", 'Crédito perdido.'),
            ('ICMS calculado que depende da TES (potencial)', f"=SUMIFS('{ab}'!$L:$L,'{ab}'!$A:$A,\"Depende da TES\")", 'Sem SF4, TES fora da SF4 ou TES com crédito e livro desencontrados (sem SFT).'),
            ('Crédito no livro fiscal fora da TES', f"=SUMIFS('{ab}'!$L:$L,'{ab}'!$B:$B,\"Crédito no livro fiscal em TES que não credita\")", 'Só com SFT: crédito no livro que a TES não prevê. Vai para a apuração.'),
            ('Crédito previsto na TES e fora do livro', f"=SUMIFS('{ab}'!$M:$M,'{ab}'!$B:$B,\"Crédito previsto na TES fora do livro fiscal\")", 'Só com SFT: crédito não aproveitado.')])
    else:
        c = wr.cell(r, 1, 'SD1 não informada: CFOP, CST e conferência item a item não foram feitos.'); c.font = Font(name='Arial', size=10, italic=True)
    if R.get('sup'):
        r += 1; hdr(r, ['Não apontado (regra da empresa: não vai para o SPED com a TES certa)', '', 'Ocorrências', '', ''])
        for k, (a, b) in enumerate(sorted(R['sup'].items()), start=r + 1):
            wr.cell(k, 1, a).font = BF; wr.cell(k, 3, b).font = BOLD
    wr.freeze_panes = 'A4'
    wb.save(out_path)
