#!/usr/bin/env python3
"""Gera V023__seed_audit_5s_catalog_v1.sql a partir do catálogo documentado."""

from __future__ import annotations

from pathlib import Path

CRITERIA: list[tuple[int, str, int, str]] = [
    (1, "U01", 1, "Há somente materiais, ferramentas, equipamentos, documentos e objetos necessários para a atividade da área."),
    (1, "U02", 2, "Não existem materiais obsoletos, danificados, vencidos, sem identificação ou sem previsão de uso."),
    (1, "U03", 3, "Os itens pessoais estão controlados e não interferem na organização, segurança ou aparência da área."),
    (1, "U04", 4, "Não há acúmulo de caixas, embalagens, papéis, sucatas, peças, amostras ou objetos sem finalidade definida."),
    (1, "U05", 5, "Materiais de uso eventual estão separados dos materiais de uso frequente."),
    (1, "U06", 6, "Produtos, materiais ou documentos retidos, segregados ou aguardando decisão estão identificados e em local adequado."),
    (1, "U07", 7, "A área não possui equipamentos, móveis ou dispositivos quebrados, inutilizados ou aguardando manutenção sem identificação."),
    (1, "U08", 8, "O espaço disponível é utilizado de forma adequada, sem ocupação desnecessária de corredores, bancadas, armários ou áreas de circulação."),
    (2, "O01", 1, "Materiais, ferramentas, equipamentos, documentos e objetos possuem local definido para armazenamento."),
    (2, "O02", 2, "Os itens estão armazenados nos locais corretos e de forma organizada."),
    (2, "O03", 3, "As identificações de armários, prateleiras, gavetas, caixas, áreas, bancadas ou posições estão visíveis e atualizadas."),
    (2, "O04", 4, "Os materiais de maior uso estão posicionados de forma acessível e prática para a rotina da área."),
    (2, "O05", 5, "Corredores, acessos, portas, extintores, painéis elétricos e rotas de fuga estão livres e desobstruídos."),
    (2, "O06", 6, "Há separação adequada entre materiais aprovados, reprovados, em análise, aguardando uso, descarte ou devolução."),
    (2, "O07", 7, "Documentos, registros, formulários e instruções de trabalho estão disponíveis, organizados e protegidos contra danos."),
    (2, "O08", 8, "A disposição dos itens favorece a segurança, o fluxo de trabalho e a produtividade."),
    (2, "O09", 9, "Não há mistura de materiais, ferramentas, documentos ou produtos de diferentes finalidades no mesmo local."),
    (2, "O10", 10, "As demarcações de piso, áreas de armazenamento, circulação, descarte ou segurança estão visíveis e sendo respeitadas."),
    (3, "L01", 1, "Piso, bancadas, mesas, prateleiras, armários, equipamentos e máquinas estão limpos."),
    (3, "L02", 2, "Não há acúmulo de poeira, resíduos, aparas, óleo, graxa, restos de materiais, alimentos ou sujeira visível."),
    (3, "L03", 3, "Lixeiras, coletores ou recipientes de descarte estão disponíveis, identificados e em boas condições de uso."),
    (3, "L04", 4, "Os resíduos são descartados corretamente, sem mistura indevida ou acúmulo fora dos locais determinados."),
    (3, "L05", 5, "A área não apresenta vazamentos, infiltrações, mau cheiro, presença de insetos, umidade excessiva ou sinais de deterioração."),
    (3, "L06", 6, "Equipamentos, instrumentos, máquinas ou ferramentas estão limpos e conservados após o uso."),
    (3, "L07", 7, "A limpeza da área não depende apenas de ações pontuais antes da auditoria, demonstrando manutenção contínua."),
    (3, "L08", 8, "Os materiais de limpeza, quando existentes na área, estão armazenados corretamente e identificados."),
    (3, "L09", 9, "Não há risco de contaminação, dano ao produto, dano a documentos ou comprometimento de equipamentos por falta de limpeza."),
    (3, "L10", 10, "A aparência geral da área transmite cuidado, conservação e zelo pelo ambiente de trabalho."),
    (4, "P01", 1, "Existem padrões visuais claros para organização, armazenamento, identificação e limpeza da área."),
    (4, "P02", 2, "As identificações, etiquetas, placas, sinalizações e demarcações estão padronizadas e legíveis."),
    (4, "P03", 3, "O padrão definido é seguido por todos os colaboradores da área, sem variações indevidas entre turnos ou pessoas."),
    (4, "P04", 4, "Há definição clara dos locais para materiais, ferramentas, documentos, produtos, resíduos, EPIs e objetos de uso comum."),
    (4, "P05", 5, "Procedimentos, instruções, quadros, formulários ou orientações aplicáveis estão disponíveis e atualizados."),
    (4, "P06", 6, "A área possui rotina definida para limpeza, organização, descarte ou inspeção dos itens críticos."),
    (4, "P07", 7, "Os padrões de segurança, qualidade, meio ambiente e organização estão integrados ao 5S da área."),
    (4, "P08", 8, "Os itens fora do padrão são facilmente identificáveis pelo auditor ou pelos colaboradores."),
    (4, "P09", 9, "As informações expostas em murais, quadros, placas ou documentos são necessárias, atuais e bem conservadas."),
    (4, "P10", 10, "O padrão da área contribui para evitar erros, perdas, retrabalhos, acidentes ou dificuldades na execução das atividades."),
    (5, "D01", 1, "Os colaboradores demonstram conhecimento básico sobre os padrões de 5S aplicáveis à sua área."),
    (5, "D02", 2, "A área mantém a organização durante a rotina normal de trabalho, e não apenas em momentos de auditoria."),
    (5, "D03", 3, "Os itens são devolvidos aos locais corretos após o uso."),
    (5, "D04", 4, "As regras de descarte, armazenamento, identificação, limpeza e segurança são respeitadas."),
    (5, "D05", 5, "Não há evidência de reincidência de problemas já apontados em auditorias anteriores."),
    (5, "D06", 6, "Os responsáveis pela área acompanham e cobram a manutenção dos padrões estabelecidos."),
    (5, "D07", 7, "As ações corretivas de auditorias anteriores foram tratadas dentro dos prazos definidos."),
    (5, "D08", 8, "Os colaboradores demonstram cuidado com o ambiente, equipamentos, materiais e áreas comuns."),
    (5, "D09", 9, "O comportamento da equipe contribui para manter a limpeza, organização, segurança e boa imagem da área."),
    (5, "D10", 10, "A área demonstra evolução em relação ao ciclo anterior do programa 5S."),
]


def esc(value: str) -> str:
    return value.replace("'", "''")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    out = root / "migrations/plugins/quality/V023__seed_audit_5s_catalog_v1.sql"

    parts: list[str] = [
        "-- Seed catálogo Auditoria 5S v1 + sequências por filial\n",
        "INSERT INTO quality.audit_5s_sensos (sort_order, name)\nVALUES\n",
        "    (1, 'Utilização'),\n",
        "    (2, 'Ordenação'),\n",
        "    (3, 'Limpeza'),\n",
        "    (4, 'Padronização'),\n",
        "    (5, 'Disciplina')\n",
        "ON CONFLICT (sort_order) DO NOTHING;\n\n",
        "INSERT INTO quality.document_sequences (sequence_key, prefix, current_value, padding_length, active)\nVALUES\n",
        "    ('audit_5s_branch_01', '01', 0, 6, TRUE),\n",
        "    ('audit_5s_branch_02', '02', 0, 6, TRUE)\n",
        "ON CONFLICT (sequence_key) DO NOTHING;\n\n",
    ]

    for senso, code, order, description in CRITERIA:
        parts.append(
            "INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)\n"
            f"SELECT s.id, '{code}', '{esc(description)}', {order}, 1\n"
            f"FROM quality.audit_5s_sensos s WHERE s.sort_order = {senso}\n"
            "ON CONFLICT (code, catalog_version) DO NOTHING;\n\n"
        )

    out.write_text("".join(parts), encoding="utf-8")
    print(f"Generated {out} ({len(CRITERIA)} criteria)")


if __name__ == "__main__":
    main()
