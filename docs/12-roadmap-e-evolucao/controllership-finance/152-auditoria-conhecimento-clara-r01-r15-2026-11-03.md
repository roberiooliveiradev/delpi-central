# 152 — Auditoria do conhecimento da CLARA, relatório a relatório (R01–R15)

**Data:** 03/11/2026 · **Base GitHub observada antes do registro:** `1e89b112f661b613ec673fb1a21f893cb59c8784` (HEAD remoto; git status local não acessível por este canal).
**Fonte efetivamente consultada:** ferramentas CLARA `get_context(topic=catalog)`, `knowledge(action=sources)` e `knowledge(action=search,query=R01..R15)`. **Corpus CLARA:** versão `5bebf07f-a66a-479f-aa2b-e7d0e6c7ea00`, publicada em 30/10/2026 11:16 -03, 2.186 itens, 88 fontes. Foram feitas pesquisas individuais para cada ID, com inspeção das respectivas seções de fichas. **Não foram executados aqui SQL completo, comparações exaustivas de producers nem consultas de dados de todos os R01–R15.** Este documento é triagem semântica da CLARA, não certificação de paridade oficial.

## Perguntas padronizadas da auditoria

Para cada relatório: (1) que problema resolve, momento do PROC-0072 e classificação REPORT/ERP_ROUTINE/DOCUMENT; (2) produtor oficial e origem canônica; (3) tabelas/joins/campos e grão; (4) filtros, datas, exclusões e parâmetros; (5) fórmulas, agregações e custo histórico; (6) exemplos reais, reconciliabilidade e divergências; (7) limitações/paridade/status; (8) citações verificáveis e versão da ficha comparada ao HEAD e contratos; (9) decisões/owners pendentes.

## Matriz por relatório: o que a CLARA efetivamente recuperou e o que melhorar

| ID | Natureza | Evidência de conhecimento CLARA encontrada | Lacuna ou revisão necessária | Triagem |
|---|---|---|---|---|
| R01 Baixas a pagar | Consulta financeira operacional / artefato FINR190 | BR-R01-001..011, população, estornos, valores, filial origem, SE5/SED e limites de equivalência | Conferir SQL/SE2/SE5 efetivo e catálogo versus paridade oficial; ficha ainda enfatiza emissão externa | VERIFY_RUNTIME |
| R02 Baixas a receber | Consulta financeira / DLP06R01 | Regras de valores, estornos, SE5×SE1×SED, diferenças entre pagar e receber | Fonte oficial ausente/parametrização geral incompleta; não apresentar paridade como fonte provada | SOURCE_GAP |
| R03 P7 | Snapshot de estoque; não rotina de execução | BR-R03-002..008, MATR989 em processo, estoque ex-99, recortes MP/PA/PI | Parâmetros oficiais, variante MATR460 e homologação por competência; identificar SQL atual | OFFICIAL_PARITY_PENDING |
| R04 Consumo por OP | Consulta operacional, NÃO equivalência MATR860 | **Ficha CLARA de 31/10 ainda afirma “não há operação Portal/CLARA”, “owner técnico nenhum”, “report_not_implemented”** | **STALE_EVIDENCE crítico:** produtor consumption-audit e BFF/CLARA/MFE publicados; atualizar ficha com SC2/SG1/SD4/SD3, distinção entre consumo auditado e MATR860, ordenação global G070, status administrativo C2_STATUS e ausência de centro escalar; confrontar regressão CLARA HTTP400 CF-UX-050 | P0_STALE |
| R05 Entradas e saídas | Consulta de movimentação | BR-R05-001..012, SD1/SD2/SD3/SB9, filtros, saldo inicial/final, TTAT as_of, reconciliação | Verificar SQL/versão atual, drift pós-emissão, paridade MATR320 não homologada | VERIFY_RUNTIME |
| R06 Kardex/CPV | Relatório MATR910 + medida gerencial distinta | Modelo UNION, filtros F4_ESTOQUE/D3_ESTORNO/ORIGLAN, SB9, TTAT, CalcEst, diferenciação CPV | Revisar custo as-of, parâmetros efetivos e código atual; homologação oficial segue distinta da reconstrução | VERIFY_RUNTIME |
| R07 Inventários | Recorte de ajustes do MATR910 | BR-R07-001..003, D3_DOC INVENT, entradas/saídas e reconciliação histórica 45/45 | Confrontar universo corrente (45 históricos vs contagem live diferente), filtros por filial/armazém; não inferir regressão só pelo total | RECONCILE |
| R08 Material em processo | Consulta MATR989 / H02 | BR-R08-001..006, SD3 RE*/DE*, OP ativa, saldo por par e armazém 99 | Conferir critérios de corte temporal, data de OP, valor as-of e paridade oficial | VERIFY_RUNTIME |
| R09 Faturamento × MOD | Consulta operacional DLP204 | Ficha possui BR-R09, expansão de PA, quantidades e fonte DLP204 | **STALE_EVIDENCE crítico:** ficha afirma “sem endpoint”, “CLARA não pode consultar”, “owner técnico nenhum”, “report_not_implemented”; já existe produtor/BFF/CLARA/MFE com operational_view, `source_missing` no custo SP e G042; atualizar com SHA/contratos e limites | P0_STALE |
| R10 Despesas por centro de custo | Consulta operacional/investigativa | 13 TES de exclusão, D1_DTDIGIT, MP fora, apuração ≠ investigação, divergência 12-vs-13 | Validar contra SQL atual e fechar semântica de classificação Direto/Ind/Adm e G6 | OWNER_RULE_PENDING |
| R11 NF a desconsiderar | Lista investigativa, sem exclusão automática | SD2/SF4, grupo 9035∩TES594, custo zero estrutural, não equivale erro | Decisão funcional E11a/E11b ainda aberta; não recomendar exclusão automática | OWNER_RULE_PENDING |
| R12 Estado de fechamento de custos | **ERP_ROUTINE** observada, Portal read-only | MATA320/MATA300/MATA330, B1_CUSTD, SB9/MV_ULMES, wizard e limites | Ficha `TARGET` e visão antiga; incorporar **novo design 151 / Gate 071** e ferramenta CLARA cost_closing_state, sem inferir execução/homologação | STALE_CONTEXT |
| R13 Extratos/aplicações | **DOCUMENT_EVIDENCE** externa | Origem externa, coleta Controladoria, DRE/Contabilidade; não há SQL TOTVS | Especificar inventário de instituições/tipos, checklist e upload P2/P5; não chamar relatório SQL bloqueado quando fluxo documental existe | DOC_CLASSIFICATION |
| R14 Importação/câmbio | **DOCUMENT_EVIDENCE** externa | Evidência de importação/câmbio/SWIFT/ACSI, origem externa | Aplicabilidade, owner e arquivo real, upload/competência; não criar produtor SQL | DOC_CLASSIFICATION |
| R15 Cutoff/virada | **ERP_ROUTINE / estado observado read-only** | MATA330/MATA280, SB9/MV_ULMES, timestamps e evidências de virada | Ficha `TARGET_ONLY` e sem referência suficiente à página read-only atual R12/R15; separar observação técnica de homologação e de execução | STALE_CONTEXT |

## Achados transversais fundamentados

1. **P0 documentação desatualizada:** R04 e R09 contradizem entregas registradas posteriormente a 31/10. Não remover cautela oficial MATR860 nem inventar SP DLP204 ao atualizar.
2. **R12/R15:** descrições de rotina do ERP devem explicar a página operacional read-only implementada, com semântica de evidência (3/5 não é fechamento 60% concluído). Atualizar para linguagem de negócio do doc 151 sem apagar rastreabilidade técnica.
3. **Separação essencial:** R13/R14 são documentos externos (P2/P5), não SQL; R12/R15 são rotinas/processos executados no TOTVS e visualização de estados, não relatórios financeiros a reimplementar.
4. **Conhecimento ≠ SQL do HEAD:** a busca CLARA retorna fontes e snippets; não foi provado que cada ficha reflita a query/joins do produtor em produção ou a versão deployed. Exigir revisão de código/produtor + testes antes de chamar regra `PROVEN_IN_RUNTIME`.
5. **R02, R03 e homologação oficial:** preservar estados `SOURCE_MISSING`/`PENDING` e evitar confundir reconstrução operacional com emissão oficial.
6. **Busca CLARA:** consultas excessivamente detalhadas combinadas com `report_id` retornaram `items:[]`, enquanto consultas simples `query="MATR910"`, `query="R04"` retornaram fontes. Resultado vazio **não** significa ausência de conhecimento; revisar lógica de busca/ranking e cobertura de perguntas sem inferir.
7. **Governança:** recomenda-se versão/publicação incremental das 15 fichas, com source SHA, owner, evidence class, último teste positivo, contrato produtor e data do corpus; usar GitHub como authority TARGET e TÉO como authority AS-IS.

## Backlog de correção proposto — sem implementação autorizada nesta auditoria

- **CLARA-KNOW-001 (P0):** corrigir fichas R04 e R09 e republicar corpus; validar consulta/resposta de conhecimento, owner e SHA.
- **CLARA-KNOW-002 (P1):** atualizar fichas R12/R15 e distinguir rotina TOTVS de visão de acompanhamento read-only atual; documentar limitações de estado e aprovação humana.
- **CLARA-KNOW-003 (P1):** matriz source-to-SQL-to-contract para R01–R11, com grão, filtros, fórmulas, colunas, datas, costs as_of, joins, producers/consumers, teste e SHA; executar auditoria um a um no HEAD antes de afirmar paridade.
- **CLARA-KNOW-004 (P1):** fechar cobertura documental R13/R14 (instituições, aplicabilidade, owner, fluxo P2/P5), sem tratar como relatórios TOTVS.
- **CLARA-KNOW-005 (P1):** testar qualidade do mecanismo de busca CLARA, fonte, ranking e citações; distinguir miss real vs consulta restritiva.
- **CLARA-KNOW-006 (P1):** regressão da CLARA R04 HTTP400 (CF-UX-050) é problema operacional separado; o corpus não conserta gateway/contrato e não deve mascará-lo.

**Status final deste documento:** `AUDIT_INVENTORY_COMPLETE` das fichas CLARA para os 15 IDs; `INCONCLUSIVE` para garantia de conhecimento de SQL real em todos os produtores; sem alteracão de código ou runtime. Próximo gate deve fechar matriz fonte→SQL→contrato por relatório e atualizar corpus com provas.
