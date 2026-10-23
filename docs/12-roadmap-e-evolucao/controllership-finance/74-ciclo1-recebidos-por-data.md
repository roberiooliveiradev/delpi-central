# 74 - Ciclo 1: recebimentos por data

Revisao documental de 23/10/2026. PROC-0072. Fonte PDF privado, nao versionado.

Relatorio `DLP06R01`, 36 paginas, com eventos de recebimento agrupados por data de baixa, subtotais diarios e total geral. Referencia setembro/2026. Campos funcionais: titulo/parcela, contraparte, natureza, vencimento, baixa, digitacao, valor original, componentes de juros e descontos, total liquidado, banco, motivo, origem e historico.

O layout inclui baixas normais e compensacoes de documentos de credito. Ha eventos com valor baixado distinto do original. O rodape separa baixas e compensacoes; total de baixa nao equivale automaticamente a entrada bancária. O arquivo exige analise de log de inconsistencias nao fornecido.

Nao confundir snapshot de recebiveis em aberto (doc 70) com fluxo de baixas; FINR190 e rotina candidata ainda nao mapeada ao producer; APIs R01/R02 nao tem paridade oficial demonstrada.

Ciclo 2: validar rotina e parametros, chaves de evento, codigos de baixa, compensacoes, parcialidades, fontes TOTVS, conciliacao de somatorios, log e revisao P2/P5.

Status: LAYOUT=PROVEN_DOCUMENT; LOG=TO_INVENTORY; FINR190=TO_INVENTORY; PARITY=TEST_NOT_RUN; RUNTIME=NO_GO.
