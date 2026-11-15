"""Gera os catálogos TES-03 (entrada) e TES-04 (saída) a partir da extração da SF4.

Uso (na raiz do repositório):

    python3 docs/12-roadmap-e-evolucao/controllership-finance/fichas/tes/fonte/gerar_catalogo_tes.py \
        --csv docs/12-roadmap-e-evolucao/controllership-finance/fichas/tes/fonte/sf4-2026-11-09.csv \
        --data-extracao 09/11/2026

O CSV tem as 20 colunas de ``sf4-2026-11-09.csv`` (separador ``;``). Para
atualizar o catálogo, gere um CSV novo com as mesmas colunas a partir da SF4
vigente, rode este script e revise o diff de TES-03/TES-04. As fichas TES-00,
TES-01, TES-02 e TES-05 são escritas à mão: revise os números citados nelas
(``--resumo`` imprime as contagens).
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
FICHAS = HERE.parent
MAX_TABLE_CHARS = 4800  # o corpus corta seções acima de 6000 caracteres

# Família pela natureza do CFOP (três últimos dígitos). Ordem importa.
_COMMON = [
    ({"124", "125", "126"}, "industrializacao-encomenda"),
    ({"551", "552", "553", "554", "555", "604", "406"}, "ativo"),
    ({"556", "557", "407"}, "consumo"),
    ({"251", "252", "253", "254", "255", "256", "257"}, "energia"),
    ({"301", "302", "303", "304", "305", "306", "307"}, "comunicacao"),
    ({"351", "352", "353", "354", "355", "356", "357", "360", "932", "206"}, "frete"),
    ({"933"}, "servicos"),
    ({"151", "152", "153", "154", "155", "156", "408", "409"}, "transferencia"),
    ({"901", "902", "903", "904", "905", "906", "907", "924", "925"}, "industrializacao-remessa"),
    ({"915", "916"}, "conserto"),
    ({"920", "921"}, "vasilhame"),
    ({"908", "909", "910", "911", "912", "913", "914", "917", "918", "919"}, "bonificacao-amostra"),
    ({"922", "923"}, "entrega-futura"),
    ({"927"}, "baixa-perda"),
]
_ENTRY_PURCHASE = {"101", "102", "111", "116", "117", "118", "120", "121", "122",
                   "126", "127", "401", "403"}
_ENTRY_FUEL = {"651", "652", "653"}
_ENTRY_RETURN = {"201", "202", "203", "204", "208", "209", "410", "411"}
_EXIT_RETURN = {"201", "202", "208", "209", "210", "410", "411", "412", "413",
                "503", "553", "556", "660", "661", "662"}
_EXIT_SALE = {"101", "102", "103", "104", "105", "106", "107", "108", "109", "110",
              "111", "112", "113", "114", "115", "116", "117", "118", "119", "120",
              "122", "123", "401", "402", "403", "405", "501", "502", "651", "652",
              "653", "654", "655", "656", "667"}

FAMILIES = {
    "compras": ("Compras de insumo, matéria-prima e revenda",
                "Compra de matéria-prima, insumo e mercadoria para revenda (CFOP x101, x102, x401, x403). "
                "Em regra atualizam estoque e geram duplicata; creditam ICMS e IPI quando o fornecedor destaca e a operação dá direito. "
                "As que atualizam estoque entram no kardex (R06) e no R05 como compras. As TES 001 e 003 ficam fora da apuração de despesas do R10."),
    "industrializacao-encomenda": ("Industrialização por encomenda (x124/x125)",
                "Na entrada: industrialização feita por outra empresa para a Delpi. Na saída: industrialização que a Delpi fez para outra empresa "
                "(cobrança do serviço e dos insumos aplicados). A TES 510 é o item que carrega o custo; o par de faturamento da industrialização é a TES 594 (família Vendas)."),
    "ativo": ("Ativo imobilizado",
              "Compra, remessa, retorno, venda e transferência de bens do ativo, e lançamento do crédito de ICMS do ativo (CIAP, CFOP x604). "
              "Não atualizam o ativo fixo pela TES no cadastro desta extração (Atual.Ativo? = Não em todas)."),
    "consumo": ("Uso e consumo",
                "Material de uso e consumo (CFOP x556, x557, x407). Na regra geral não dão crédito de ICMS. "
                "Material de consumo com crédito de IPI é ponto de atenção da auditoria de entradas (regra «Crédito de IPI em material de uso e consumo»)."),
    "energia": ("Energia elétrica", "Aquisição de energia elétrica (CFOP x252/x253). A TES 020 fica fora da apuração de despesas do R10."),
    "comunicacao": ("Comunicação", "Serviços de comunicação (CFOP x302/x303). A TES 030 fica fora da apuração de despesas do R10."),
    "frete": ("Frete e transporte",
              "Conhecimentos de transporte (CT-e) e anulação de frete (CFOP x352, x353, x206, x932). "
              "O crédito de ICMS do frete depende do que foi transportado: frete de venda ou de insumo dá direito; frete de consumo ou ativo não. "
              "A auditoria de entradas identifica frete pelo CFOP terminado em 352 e lê o crédito na TES (ficha AE-05). A TES 040 fica fora da apuração de despesas do R10."),
    "servicos": ("Serviços tomados", "Serviços tributados pelo ISS (CFOP x933). A TES 046 aparece no R10 na exclusão da coparticipação de plano de saúde (parcela do colaborador)."),
    "transferencia": ("Transferências entre filiais",
                      "Transferência de produção, mercadoria ou insumo entre estabelecimentos da Delpi (CFOP x151, x152, x408, x409). Não geram duplicata. "
                      "A TES 204 (transferência de matéria-prima) fica fora da apuração de despesas do R10."),
    "industrializacao-remessa": ("Remessa e retorno para industrialização",
                "Material que vai ou volta de industrialização (CFOP x901, x902, x903). Em regra não geram duplicata e boa parte controla poder de terceiros "
                "(Remessa = o material sai ou entra sem mudar de dono; Devolução = retorno desse material). As TES 080, 085 e 159 ficam fora da apuração de despesas do R10."),
    "conserto": ("Conserto e reparo", "Remessa e retorno de bens para conserto (CFOP x915/x916). Não geram duplicata."),
    "vasilhame": ("Vasilhame e embalagem retornável",
                  "Vasilhame e embalagem retornável (CFOP x920/x921) — na Delpi, os carretéis dos cabos. A TES 083 fica fora da apuração de despesas do R10."),
    "bonificacao-amostra": ("Bonificação, amostra, demonstração, consignação e comodato",
                            "Bonificação (x910), amostra grátis (x911), demonstração (x912/x913), consignação (x917–x919) e comodato (x908/x909). Em regra não geram duplicata."),
    "entrega-futura": ("Entrega futura e conta e ordem", "Lançamento para entrega futura e venda à ordem (CFOP x922/x923)."),
    "baixa-perda": ("Baixa de estoque e perdas", "Baixa de estoque por perda, roubo ou deterioração (CFOP x927). Tiram do estoque sem gerar duplicata."),
    "combustivel": ("Combustíveis e lubrificantes", "Compra de combustível e lubrificante para consumo (CFOP x651/x652/x653)."),
    "devolucao-venda": ("Devolução de venda",
                        "Entrada da mercadoria que a Delpi vendeu e o cliente devolveu (CFOP x201, x202, x410, x411). "
                        "A TES 120 é a devolução de venda padrão e fica fora da apuração de despesas do R10."),
    "devolucao-compra": ("Devolução de compra",
                         "Saída da mercadoria comprada que a Delpi devolve ao fornecedor (CFOP x201, x202, x410, x411, x556). "
                         "No R05 entram como devolução de compra (tipo de nota D). Exemplos: 530 e 561 devolvem compras feitas nas TES 001 e 003."),
    "vendas": ("Vendas",
               "Venda de produção própria e de mercadoria de revenda (CFOP x101, x102, x401, x405). "
               "O CPV gerencial usa os CFOPs 5101, 5124, 6101 e 6124 com o custo do item (D2_CUSTO1). "
               "Atenção: o mesmo CFOP 5101 tem TES que baixam estoque e TES que não baixam (ex.: 614 baixa; 594 não baixa e tem custo zero)."),
    "importacao": ("Importação", "Entradas de importação (CFOP 3xxx), incluindo drawback e importação para industrialização com ICMS diferido."),
    "exportacao": ("Exportação", "Saídas para o exterior (CFOP 7xxx)."),
    "outras": ("Outras operações e estornos",
               "Outras entradas e saídas não especificadas (CFOP x949), estornos e ajustes. Descrição genérica: confira a finalidade da nota antes de concluir qualquer efeito."),
}
FAMILY_ORDER = ["compras", "importacao", "exportacao", "vendas", "industrializacao-encomenda",
                "industrializacao-remessa", "devolucao-venda", "devolucao-compra", "transferencia",
                "consumo", "combustivel", "ativo", "energia", "comunicacao", "frete", "servicos",
                "conserto", "vasilhame", "bonificacao-amostra", "entrega-futura", "baixa-perda", "outras"]


def family(row: dict) -> str:
    cf = row["cfop"]
    entry = row["tipo"] == "Entrada"
    if len(cf) != 4 or not cf.isdigit():
        return "outras"
    first, nature = cf[0], cf[1:]
    if first == "3":
        return "importacao"
    if first == "7":
        return "exportacao"
    if entry:
        if nature in _ENTRY_RETURN:
            return "devolucao-venda"
        if nature in _ENTRY_PURCHASE:
            return "compras"
        if nature in _ENTRY_FUEL:
            return "combustivel"
    else:
        if nature in _EXIT_RETURN:
            return "devolucao-compra"
        if nature in _EXIT_SALE:
            return "vendas"
    for natures, fam in _COMMON:
        if nature in natures:
            return fam
    return "outras"


def is_active(row: dict) -> bool:
    return row["bloqueado"] != "Sim"


def _yn(value: str) -> str:
    return {"Sim": "S", "Nao": "N", "Não": "N"}.get(value, value or "—")


def _book(value: str) -> str:
    return {"Tributado": "T", "Isento": "I", "Outros": "O", "Nao": "N"}.get(value, value or "—")


def _pis(row: dict) -> str:
    return {"Credita": "Cred", "Debita": "Deb", "Calcula": "Calc", "Nao Calcula": "—"}.get(
        row["credito_piscofins"], row["credito_piscofins"] or "—")


def _poder3(value: str) -> str:
    return {"Remessa": "R", "Devolucao": "D", "Nao Controla": "—"}.get(value, value or "—")


def _description(row: dict) -> str:
    text = row["texto"].replace("|", "/")
    fin = row["finalidade"].replace("|", "/")
    if fin and fin.upper() != text.upper():
        text = f"{text} ({fin})"
    return text


HEADER = ("| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro "
          "| PIS/COFINS | Poder 3º | Consumo | TES devol. |\n"
          "|---|---|---|---|---|---|---|---|---|---|---|")


def row_md(row: dict) -> str:
    icms = f"{_yn(row['calcula_icms'])}/{_yn(row['credita_icms'])}/{_book(row['livro_icms'])}"
    ipi = f"{_yn(row['calcula_ipi'])}/{_yn(row['credita_ipi'])}/{_book(row['livro_ipi'])}"
    return (f"| TES {row['codigo']} | {_description(row)} | {row['cfop']} | {_yn(row['estoque'])} "
            f"| {_yn(row['duplicata'])} | {icms} | {ipi} | {_pis(row)} | {_poder3(row['poder_terceiros'])} "
            f"| {_yn(row['material_consumo'])} | {row['tes_devolucao'] or '—'} |")


def chunk_rows(rows: list[str]) -> list[list[str]]:
    chunks, cur, size = [], [], 0
    for line in rows:
        if cur and size + len(line) > MAX_TABLE_CHARS:
            chunks.append(cur)
            cur, size = [], 0
        cur.append(line)
        size += len(line) + 1
    if cur:
        chunks.append(cur)
    return chunks


def summary(rows: list[dict]) -> str:
    n = len(rows)
    est = sum(r["estoque"] == "Sim" for r in rows)
    dup = sum(r["duplicata"] == "Sim" for r in rows)
    icm = sum(r["credita_icms"] == "Sim" for r in rows)
    p3 = sum(r["poder_terceiros"] in ("Remessa", "Devolucao") for r in rows)
    return (f"{n} TES; {est} atualizam estoque, {dup} geram duplicata, {icm} creditam ICMS"
            f"{f', {p3} controlam poder de terceiros' if p3 else ''}.")


def render(rows: list[dict], *, side: str, code: str, data_extracao: str) -> str:
    entry = side == "Entrada"
    title = "entrada" if entry else "saída"
    faixa = "001 a 416 (e o código alfanumérico 3A8)" if entry else "501 a 764"
    by_fam = defaultdict(list)
    for r in rows:
        by_fam[family(r)].append(r)
    active = sum(is_active(r) for r in rows)
    out = [
        f"# {code} — Catálogo das TES de {title}",
        "",
        f"Versão da ficha: 1.0 · gerada da extração da SF4 de {data_extracao}.",
        "",
        "## Identificação",
        "",
        f"- Código: **{code}** — catálogo das TES de {title} cadastradas na SF4 da Delpi.",
        "- Implementação: **IMPLEMENTED** (conhecimento citável; a CLARA não lê a SF4 ao vivo).",
        f"- Fonte: extração da SF4 fornecida pela Controladoria em {data_extracao} (a mesma cópia usada pela auditoria de entradas). OWNER_REPORTED_VIA_PO.",
        f"- Faixa de códigos de {title}: **{faixa}**. Total: **{len(rows)} TES**, das quais **{active} ativas** e **{len(rows) - active} bloqueadas**. PROVEN (cadastro de {data_extracao}).",
        "- O catálogo é foto do cadastro naquela data: TES criada ou editada depois não aparece aqui. Diga a data da extração ao citar.",
        "",
        "## Como ler a tabela",
        "",
        "- **Estoque** (`F4_ESTOQUE`): S = movimenta estoque e custo; N = não movimenta.",
        "- **Duplicata** (`F4_DUPLIC`): S = gera título no financeiro (a pagar na entrada, a receber na saída) e, na saída, conta como faturamento.",
        "- **ICMS calc/créd/livro**: calcula ICMS (`F4_ICM`) / credita ICMS (`F4_CREDICM`) / livro fiscal de ICMS (`F4_LFICM`: T = Tributado, I = Isento, O = Outros, N = Não).",
        "- **IPI calc/créd/livro**: o mesmo para IPI (`F4_IPI`, `F4_CREDIPI`, `F4_LFIPI`).",
        "- **PIS/COFINS**: Cred = credita; Deb = debita; Calc = só calcula; — = não calcula.",
        "- **Poder 3º** (`F4_PODER3`): R = Remessa, D = Devolução, — = não controla. Material em poder de terceiros não é estoque próprio.",
        "- **Consumo** (`F4_CONSUMO`): S = TES de material de uso e consumo.",
        "- **TES devol.**: TES que o Protheus sugere para devolver esta operação.",
        "- Famílias agrupadas pela natureza do CFOP (três últimos dígitos). A família ajuda a achar a TES; o comportamento real é o das colunas.",
        "",
    ]
    for fam in FAMILY_ORDER:
        frows = sorted(by_fam.get(fam, []), key=lambda r: r["codigo"])
        if not frows:
            continue
        name, text = FAMILIES[fam]
        act = [r for r in frows if is_active(r)]
        blk = [r for r in frows if not is_active(r)]
        out += [f"## {name} ({title})", "", text, "",
                f"- Ativas: {summary(act) if act else 'nenhuma.'}",
                f"- Bloqueadas: {len(blk)} TES." if blk else "- Bloqueadas: nenhuma.",
                f"- Códigos ativos: {', '.join(r['codigo'] for r in act) or '—'}.",
                ""]
        for label, group in (("ativas", act), ("bloqueadas", blk)):
            if not group:
                continue
            chunks = chunk_rows([row_md(r) for r in group])
            for i, chunk in enumerate(chunks, 1):
                part = f" (parte {i})" if len(chunks) > 1 else ""
                out += [f"### {name} — TES de {title} {label}{part}", "", HEADER, *chunk, ""]
    out += [
        "## Governança",
        "",
        "- Owner do cadastro: Controladoria e equipe fiscal. A CLARA não cria, edita nem bloqueia TES.",
        "- Bloqueada (`F4_MSBLQL`) = não pode ser usada em nota nova. Nota antiga pode ter TES hoje bloqueada: isso é normal e não é erro.",
        "- Configuração estranha no cadastro é ponto a verificar com o fiscal, nunca erro confirmado (ficha TES-02).",
        "- Atualização: nova extração da SF4 e republicação do catálogo (manutenção na ficha TES-05).",
        "",
    ]
    return "\n".join(out)


def _iso(date_br: str) -> str:
    d, m, y = date_br.split("/")
    return f"{y}-{m}-{d}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=str(HERE / "sf4-2026-11-09.csv"))
    ap.add_argument("--data-extracao", default="09/11/2026")
    ap.add_argument("--resumo", action="store_true")
    args = ap.parse_args()
    with open(args.csv, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh, delimiter=";"))
    entry = [r for r in rows if r["tipo"] == "Entrada"]
    exit_ = [r for r in rows if r["tipo"] == "Saida"]
    (FICHAS / "TES-03.md").write_text(
        render(entry, side="Entrada", code="TES-03", data_extracao=args.data_extracao), encoding="utf-8")
    (FICHAS / "TES-04.md").write_text(
        render(exit_, side="Saida", code="TES-04", data_extracao=args.data_extracao), encoding="utf-8")
    if args.resumo:
        for side, group in (("Entrada", entry), ("Saida", exit_)):
            c = Counter((family(r), is_active(r)) for r in group)
            print(side, len(group), "ativas", sum(is_active(r) for r in group))
            for fam in FAMILY_ORDER:
                a, b = c.get((fam, True), 0), c.get((fam, False), 0)
                if a or b:
                    print(f"  {FAMILIES[fam][0]}: {a} ativas / {b} bloqueadas")


if __name__ == "__main__":
    main()
