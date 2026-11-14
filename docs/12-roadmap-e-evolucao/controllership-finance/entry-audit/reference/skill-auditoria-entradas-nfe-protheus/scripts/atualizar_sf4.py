#!/usr/bin/env python3
"""Grava uma SF4 (cadastro de TES) dentro da skill, para as auditorias seguintes não precisarem dela.

A SF4 é cadastro: só muda quando alguém cria ou edita uma TES. Por isso fica guardada em
references/sf4/ e o auditoria.py usa essa cópia quando --sf4 não é informado.

Uso (sempre numa CÓPIA gravável da skill, depois reempacotar):
  python atualizar_sf4.py <SF4.xlsx|csv> [--data AAAA-MM-DD] [--skill <pasta da skill>]

A data de extração vem, nesta ordem, de --data, da data de criação gravada no xlsx
(docProps/core.xml) ou do dia de hoje.
"""
import argparse, datetime as dt, json, os, re, sys, warnings, zipfile
warnings.filterwarnings('ignore')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from leitura import read_protheus, txt

OBRIG = ('Cod. do Tipo', 'Cred. ICMS ?', 'L.Fisc. ICMS', 'Credita IPI?')


def data_do_arquivo(path):
    try:
        with zipfile.ZipFile(path) as z:
            core = z.read('docProps/core.xml').decode('utf-8', 'ignore')
        m = re.search(r'<dcterms:created[^>]*>(\d{4}-\d{2}-\d{2})', core)
        return m.group(1) if m else None
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('sf4')
    ap.add_argument('--data', help='data de extração da SF4 (AAAA-MM-DD)')
    ap.add_argument('--skill', default=os.path.dirname(HERE), help='pasta raiz da skill (padrão: a desta cópia)')
    a = ap.parse_args()

    df = read_protheus(a.sf4)
    falta = [c for c in OBRIG if c not in df.columns]
    if falta: sys.exit(f'O arquivo não parece ser a SF4: faltam as colunas {falta}.')
    df = df[df['Cod. do Tipo'].map(txt) != ''].copy()

    data = a.data or data_do_arquivo(a.sf4) or dt.date.today().isoformat()
    dest = os.path.join(a.skill, 'references', 'sf4')
    os.makedirs(dest, exist_ok=True)
    df.to_csv(os.path.join(dest, 'SF4.csv'), sep=';', index=False, encoding='utf-8')
    ent = df[df.get('Tipo do TES', '').map(txt) == 'Entrada'] if 'Tipo do TES' in df.columns else df
    info = dict(data_extracao=data, total_tes=int(len(df)), tes_entrada=int(len(ent)),
                arquivo_origem=os.path.basename(a.sf4), gravado_em=dt.date.today().isoformat())
    json.dump(info, open(os.path.join(dest, 'sf4_info.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(f"SF4 gravada em {dest}: {info['total_tes']} TES ({info['tes_entrada']} de entrada), extraída em {data}.")


if __name__ == '__main__':
    main()
