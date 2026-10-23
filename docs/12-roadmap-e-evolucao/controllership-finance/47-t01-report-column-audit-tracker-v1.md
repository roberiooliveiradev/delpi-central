# 47 — T01 | Tracker de coleta, tabelas, colunas e paridade — PROC-0072

> **Criado em 20/10/2026.** Este documento é o **controle de execução do inventário**, derivado do [46 — catálogo de fontes](./46-t01-report-source-inventory-v1.md). **Não é prova de que os bindings físicos foram encontrados** e não autoriza código runtime, deploy, SQL write, migration ou consulta arbitrária. TÉO é autoridade AS-IS; GitHub é autoridade TARGET/runtime; DAVI disponibiliza apenas capabilities READ descobertas/autorizadas.

## 1. Regras de medição e anti-loop

**Denominador V1 congelado:** 15 itens (`R01–R15`) importados do documento 46. Alguns são **famílias/rotinas/documentos externos**, e não relatórios unitários: a próxima auditoria deve desdobrá-los em filhos (`R03.1`, `R03.2` etc.) sem apagar o pai, com `scope_change`, motivo, owner e commit. Atualizar o denominador de modo explícito ao incorporar filhos obrigatórios ou novos relatórios comprovados. Nunca ocultar trabalho via descontinuação silenciosa. Itens externos podem fechar com **evidência de externalidade + contrato de coleta**, sem exigir tabela SQL inexistente.

Para **cada item**, usar seis gates verificáveis, `0/1` cada: **G1** evidência da etapa e propósito; **G2** saída e campos/colunas exibidos no relatório com período e filtros; **G3** decisão sobre tipo de fonte (ERP / externo / misto) e owner; **G4** bindings físicos (tabelas, colunas, joins, filtros) **ou**, para fontes externas, contrato de coleta e owner validado; **G5** prova READ reproduzível/paridade de amostra (ou validação do artefato externo e integridade); **G6** aceite funcional da Controladoria/owner, com versão e evidência. O gate só recebe 1 com evidência registrada e revisada.

**Percentuais:**
- `PERCENTUAL_COLETA = soma(G1..G4 comprovados) / (4 × total de itens em escopo) × 100`.
- `PERCENTUAL_AUDITORIA = soma(G1..G6 comprovados) / (6 × total de itens em escopo) × 100`.
- `PERCENTUAL_RELATORIOS_CONCLUIDOS = itens com seis gates PASS / total × 100`.
- Arredondamento a uma casa decimal; todos os números devem mostrar `numerador/denominador` e commit/date da evidência.
- **Não atribuir PASS ao G1/G3 apenas porque este documento tem um nome/área preliminar.** Rótulos `SOURCE_DOCUMENTED` e `PARTIAL` indicam candidatos a validação, não gate validado.
- Estado inicial **auditado** deste tracker: `0/60 = 0,0% coleta`, `0/90 = 0,0% auditoria`, `0/15 = 0,0% concluídos`. Isso é **baseline conservador dos gates ainda não atestados**, não afirma que zero informação foi levantada: 15 itens e macroetapas já estão catalogados no doc 46. Quando G1 ou G3 forem demonstrados com citação/linhas verificáveis, pontuar sem repetição de coleta.
- Na revisão de cada rodada, reportar `itens novos`, `gates novos PASS`, `gates STALE`, `itens bloqueados`, `consultas DAVI executadas`, `amostras pareadas`, `tempo/retrabalho`, `next bounded batch`. Parar o lote se 2 tentativas independentes com a mesma hipótese não produzirem evidência nova; classificar bloqueio, owner e ação externa em vez de repetir busca.

`PASS | FAIL | PENDING | INCONCLUSIVE | TEST_NOT_RUN | STALE_EVIDENCE` são resultados; `PROVEN | TO_INVENTORY | PLANNED | TARGET` são classes de evidência. `EXECUTION_DRIFT` quando premissa canônica cair.

## 2. Registro mestre — campos operacionais

| ID | Relatório/atividade | Rotina candidata | Família | TÉO ref | G1 | G2 | G3 | G4 | G5 | G6 | Owner do próximo passo |
|---|---|---|---|---|---|---|---|---|---|---|---|
| R01 | Baixas a pagar | `FINR190` + `DLP06R01.prt`/`nat.prt` (vídeo menu + artefatos; `_F190C` NotebookLM = drift a reconciliar) | Financeiro | `kp02_t01/kp02_st01` | PASS | PASS | PASS | PASS | PASS | PENDING | Controladoria (G6 aceite) |
| R02 | Baixas a receber | `DLP06R01` custom (layout `.prt` compartilhado; FINR190 **descartado** pelo WHERE — doc 80 §17.D) | Financeiro | `kp02_t01/kp02_st02` | PASS | PASS | PASS | PENDING | PASS | PENDING | TI/ERP (fonte `DLP06R01`) + Controladoria (G6 aceite) |
| R03 | P7 padrão / Bloco H | "Registro de Inventário Modelo P7" (vídeo) / MATR460 (roster) | Estoque | `kp04_t01_st01/st02` | PASS | PASS | PASS | PENDING | PENDING | PENDING | Controladoria + owner da fonte |
| R04 | Consumo por OP | MATR860 | Produção | `kp04_t02` | PENDING | PENDING | PENDING | PENDING | TEST_NOT_RUN | PENDING | Controladoria + owner da fonte |
| R05 | Entradas e Saídas / valor estoque | `MATR320` (.prt no artefato) | Estoque | `kp04_t03` | PASS | PASS | PASS | PASS | PASS | PENDING | Controladoria + owner da fonte |
| R06 | CPV / Kardex 01 | `MATR910` (roster + artefato kardex) | Estoque | `kp04_t04` | PASS | PASS | PASS | PENDING | TEST_NOT_RUN | PENDING | Controladoria + owner da fonte |
| R07 | Inventários / Kardex 99 | `MATR910` (roster + artefato INVENT) | Estoque | `kp04_t05` | PASS | PASS | PASS | PENDING | TEST_NOT_RUN | PENDING | Controladoria + owner da fonte |
| R08 | Material em Processo / H02 | `MATR989` (roster + artefato 57k linhas) | Produção | `kp04_t07` | PASS | PASS | PASS | PENDING | TEST_NOT_RUN | PENDING | Controladoria + owner da fonte |
| R09 | Faturamento × MOD | `DLP204` (roster + artefato PA→MOD) | Custos | `kp04_t06` | PASS | PASS | PASS | PENDING | TEST_NOT_RUN | PENDING | Controladoria + owner da fonte |
| R10 | Notas por Centro de Custo | `EDAPP` → export SD1 (roster + vídeo + artefato) | Fiscal/Contábil | `kp04_t09` | PASS | PASS | PASS | PASS | TEST_NOT_RUN | PENDING | Controladoria (paridade G5) |
| R11 | NF venda 9035 / CPV zero | `EDAPP` → export SD2 (roster + artefato) | Fiscal | `checklist doc03` | PASS | PASS | PASS | PASS | TEST_NOT_RUN | PENDING | Controladoria (paridade G5) |
| R12 | Acompanha Custos / Reposição / Refaz Saldos | Acompanha Custo wizard (vídeo), Recálculo Reposição (vídeo), `DEL100` (fonte) | Estoque | `kp04_t10/t11/t12` | PASS | PASS | PASS | PENDING | TEST_NOT_RUN | PENDING | Controladoria + owner da fonte |
| R13 | Extratos e aplicações bancárias | externa (checklist envio) | Bancos | `kp02_t02/t03` | PASS | PENDING | PENDING | PENDING | TEST_NOT_RUN | PENDING | Controladoria + owner da fonte |
| R14 | Importação / SWIFT / câmbio / ACSI | mista | Importações | `kp03` | PENDING | PENDING | PENDING | PENDING | TEST_NOT_RUN | PENDING | Controladoria + owner da fonte |
| R15 | Cutoff / sacramentação / SB9 | fechamento wizard (execução observada vídeo) + SB9 candidato | Estoque | `kp08_t03/t04` | PASS | PASS | PENDING | PENDING | TEST_NOT_RUN | PENDING | Controladoria + owner da fonte |

**Cada alteração de gate exige referência a uma linha no detalhe (§3), link/ID de artefato, SHA ou versão e data de validação.** G4 SQL requer identificação da tabela e coluna a partir de metadados confirmados, não nome por convenção TOTVS.

## 3. Fichas para preencher — uma por relatório e eventual filho

Preencher em `47a` (detalhes) ou abaixo, mantendo um registro por ID e sem eliminar históricos:

```text
ID / parent_id / version / source_sha:
STATUS: PENDING | INCONCLUSIVE | PASS | FAIL | STALE_EVIDENCE
PROCESS_STAGE (TÉO node + evidência):
RELATORIO/ROTINA / PROGRAMA / LAYOUT/VERSAO:
PURPOSE_AND_DECISIONS_SUPPORTED:
OUTPUT_FIELDS: [nome do campo exibido, significado, tipo, unidade monetária/quantidade]
OUTPUT_TOTALS_AND_GROUPINGS:
PARAMETERS: [competência, start_date, end_date, empresa, filial, armazém, CFOP, natureza, carteiras, outros]
OPERATIONAL_ACTIONS: [exporta XLS/PDF, transforma planilha, confere, corrige, reprocessa]
DELIVERY_DESTINATION / MANDATORY_CONDITION:
SOURCE_CLASS: ERP | EXTERNAL | MIXED | UNKNOWN
SOURCE_OWNER / VALIDATOR:
TABLE_BINDINGS: [database/sistema, tabela física, alias, owner, evidência metadata]
COLUMN_BINDINGS: [output field → tabela.coluna, tipo, chave, transformação justificada, evidência]
JOINS_KEYS: [join exato, cardinalidade, filtros de exclusão lógica, data de vigência]
TIME_AND_SCOPE: [competência, timezone, data referencial, código empresa/filial, unidade, armazém]
EXISTING_API_OR_DAVI_CAPABILITY: [path/action, payload, status REAL, SHA]
READ_QUERY_EVIDENCE: [SQL SELECT parametrizado / ação tipada autorizada, sem valores sensíveis]
PARITY_TEST: [mesma competência/filtros/layout; count, soma centavos, diferenças, amostra sanitizada]
FRESHNESS / NULLS / MISSING_PERIODS / ERRORS:
PRIVACY_AND_AUTHZ: [classification, resource_scope, consumer owner]
G1..G6: [status, evidence ref, reviewer, checked_at]
OPEN_BLOCKER / OWNER / NEXT_ACTION / DUE_CRITERION:
SCOPE_CHANGE / SUPERSEDES:
```

### Exemplo inicial preenchido apenas até onde existe documentação

`R03 — P7`: processo `kp04_t01_st01/st02`; rotina documentada `MATR460`; layouts `padrão` e `Bloco H` distintos; saída de estoque para conferência e Contabilidade conforme doc 03. `OUTPUT_FIELDS`, `TABLE_BINDINGS`, `COLUMN_BINDINGS`, `JOINS_KEYS`, `PARITY_TEST` = `TO_INVENTORY / TEST_NOT_RUN`. `MATR860 != P7`.

`R08 — H02`: processo `kp04_t07_st01`; material em processo; proxy SC2 citado no inventário anterior é **adjacente, não equivalente**. Não fechar G4 sem fonte correta.

`R15 — SB9`: usar `get_supplies_stock_value` / SB9 apenas como **candidato à evidência T03**, nunca declarar `STOCK_CLOSED` por inferência.

## 4. Backlog bounded de auditoria

| Lote | IDs | Critério de saída | Stop |
|---|---|---|---|
| L1 — delimitar relatórios | R01–R15 | G1/G2/G3 verificados com artefatos e filtros; desdobrar famílias | original inacessível → bloqueio com owner |
| L2 — estoque crítico | R03,R05,R08,R15 | bindings e paridade de P7/Entradas-Saídas/H02/SB9 | T03 sem owner → não inferir fechado |
| L3 — custos e consumo | R04,R06,R07,R09,R10,R11,R12 | bindings e campos comprovados | proxy adjacente sem equivalência |
| L4 — financeiro | R01,R02 | FINR190, layouts e filtros por data/natureza/carteira | divergência entre layouts |
| L5 — externos | R13,R14 | origem, ownership, exportação, verificações de integridade e regra por banco/importação | lista de bancos divergente |
| L6 — reconciliação | IDs pai/filhos pertinentes | paridade R$0,00 por competência/empresa/filial com evidência | divergência de centavo = FAIL |

**Gate para engenharia:** somente itens com G1..G5 `PASS` e owner definido podem candidatar-se a contrato de leitura `api-delpi`/BFF; G6 é aceite do negócio antes de declarar levantamento concluído. Novas routes/migrations/permissions continuam sem GO.

## 5. Registro de rodada (append-only)

| Data | Lote | Autor | IDs | Gates novos PASS | Denominador | % coleta | % auditoria | Bloqueio e próximo owner | SHA |
|---|---|---|---|---|---|---|---|---|---|
| 2026-10-20 | Setup | GPT (documental) | R01–R15 | 0 (sem ateste formal) | 15 | 0/60 = 0,0% | 0/90 = 0,0% | Coletar evidências artefato/vídeo/DAVI | `52dbbf45b671` |
| 2026-10-20 | L1.1 FINR190 | GPT/TÉO/DAVI/VISTA/GitHub | R01,R02 | G1 R01+R02 (2) | 15 | **2/60 = 3,3%** | **2/90 = 2,2%** | Exportações e layouts FINR190 pendentes; owner Controladoria/ERP | commit desta rodada |
| 2026-10-23 | CF-C2-FULL-EVIDENCE | Devin (pasta PO + vídeo + fontes + doc 80) | R01–R15 | 37 gates novos (detalhe §11; rework §11.1 reverteu G4 de R02) | 15 | **39/60 = 65,0%** | **39/90 = 43,3%** | G5 paridade + G4 bindings parciais + G6 aceite; owners conforme doc 82 | commit desta rodada |
| 2026-10-23 | CF-C2-PARITY-001 | Devin (paridade row-level artefatos × SELECT-only SE5/SE1/SE2/SB9) | R01,R02,R03,R05 | G5 R01+R02 (2) | 15 | **39/60 = 65,0%** | **41/90 = 45,6%** | G4 R02 (fonte DLP06R01), G4/G5 R03–R15, G6 todos — doc 84 | commit desta rodada |
| 2026-10-23 | CF-C2-STOCK-PARITY-001 | Devin (fonte `matr320.prx` + reconciliação coluna-a-coluna + TTAT/RECNO) | R03,R05 | 0 (evidência de G4 reforçada; nenhum gate promovido) | 15 | **39/60 = 65,0%** | **41/90 = 45,6%** | `as_of` do saldo R05 + parâmetros P7 (R03) + G6 — doc 80 §31, doc 84 §4.2-4.3, doc 85 §5 | commit desta rodada |
| 2026-10-23 | CF-C2-STOCK-RULES-CONSOLIDATION-002 | Devin (escopo completo 10 tipos × 13 colunas + ponte de drift por produto + binding P7 loc99) | R03,R05 | G4 R05 + G5 R05 (2) | 15 | **40/60 = 66,7%** | **43/90 = 47,8%** | parâmetros P7 + produtor `matr460.prx` (R03), G6 todos — doc 80 §33, doc 84 §4.3-4.4, doc 85 §3/§5 | commit desta rodada |

## 6. Rodada L1.1 — FINR190 (20/10/2026)

### R01 — Baixas a pagar — primeira análise

**G1 PASS / PROVEN:** decomposição AS-IS do TÉO `kp02_t01` ("Gerar relação de baixas no FINR190"), subtarefa `kp02_st01` ("Gerar relação de baixas a pagar") e `kp02_st03` (ordenações requeridas). Documento GitHub `03-evidencias-proveniencia-e-rastreabilidade.md`: pagar em Excel, PDF por natureza e PDF por data; procedimento usa primeiro/último dia do período. Finalidade: compor entregáveis financeiros e permitir conferência/envio no fechamento. **O PDF original e sua lista de colunas ainda não foram reabertos nesta rodada.**

**G2 PENDING:** parâmetros documentados = data inicial/final da competência, disposição por DATA/NATUREZA. Ainda faltam nomes/tipos exatos de todas as colunas, seleção por empresa/filial, natureza e critérios de ordenação/totalização realmente exibidos. **Não supor layout por conhecimento geral de FINR190.**

**DAVI executado, READ:** `discover_delpi_information` → `search_protheus_columns_by_description` com `description="baixa", page=1, limit=20`, retorno `status=ok`, `total_records=274`, `is_complete=false`, página 1/14. Nesta página o dicionário tipado trouxe **`FK2010` / descrição "Baixas a Pagar" / coluna `FK2_DATA` / descrição "Data Baixa"**. **É candidato de binding; não há prova de que FINR190 consulta FK2 ou de que a coluna representa cada campo do relatório.** Resultado da pesquisa também contém entidades não financeiras e é paginado — não promover descoberta de nome a equivalência.

**VISTA executada, READ discovery:** `search_data_routes("FINR190 baixas contas a pagar e receber relatório financeiro Protheus")` trouxe rotas financeiras **adjacentes**, incluindo `get_financeiro_inadimplencia_titulos` e `get_financeiro_despesas_centro_custo_lancamentos`; nenhuma delas é comprovadamente equivalente às baixas FINR190. Rota de títulos inadimplentes é receber em atraso, não relação de baixas a pagar. **Não declarar FINR190 exposto.**

**G3 PENDING:** ERP Protheus é fonte candidata do relatório, mas owner da semântica FINR190, origem dos layouts PDF/Excel e vinculação tabelas/colunas devem ser confirmados com ERP e Controladoria. **G4 PENDING**, `FK2010.FK2_DATA` candidato apenas; joins, filtros, colunas de valores, datas e exclusão lógica TO_INVENTORY. **G5 TEST_NOT_RUN:** nenhuma query de paridade realizada. **G6 PENDING:** sem aceite da Controladoria.

**Próxima evidência obrigatória para R01:** (1) amostra sanitizada FINR190 **Pagar Excel, Pagar PDF por DATA e por NATUREZA** para mesma competência; (2) cabeçalhos, filtros e totais; (3) dicionário das tabelas de baixas e dos títulos correlatos, com colunas, chaves e tipos; (4) prova de correspondência em ambiente READ autorizado; (5) alinhamento empresa/filial 01/03/04 versus 01/02 antes de comparar. Se consulta de metadados não retornar coluna/join suficiente, bloquear owner ERP em vez de inventar.

### R02 — Baixas a receber

**G1 PASS / PROVEN:** TÉO `kp02_st02` e `kp02_st03` comprovam geração de baixas a receber no FINR190; doc 03 prevê PDF/Excel e parâmetro "Da Carteira?" a confirmar contra procedimento original. **G2 PENDING** até layouts e campos. No mesmo resultado DAVI, `FK1010` ("Baixas a Receber") com `FK1_DATA` ("Data Baixa") foi identificado como **candidato**, não vínculo FINR190 comprovado. **G3/G4 PENDING, G5 TEST_NOT_RUN, G6 PENDING**.

### Controle desta rodada

- Gates formalmente promovidos: **somente G1 de R01 e G1 de R02**, após confrontar tarefa e finalidade em TÉO e doc 03. Todos os demais preservados pendentes.
- `COLETA = 2/60 = 3,3%`; `AUDITORIA = 2/90 = 2,2%`; `RELATORIOS_CONCLUIDOS = 0/15 = 0,0%`.
- DAVI `search_protheus_columns_by_description`: **uma operação tipada executada** (274 resultados totais, somente 20 observados). VISTA: **uma descoberta de rotas**, nenhuma execução. SQL e paridade: **TEST_NOT_RUN**.
- Próximo lote: buscar metadados de FK2/FK1 e as exportações originais, sem afirmar FINR190=FK2/FK1; vídeo `STALE_EVIDENCE` até reconciliação.

## 7. Rodada L1.2 — Evidência audiovisual indireta sobre `_F190C` (20/10/2026)

**Fonte desta rodada:** resposta do NotebookLM encaminhada pelo usuário, baseada em vídeo/transcrição PROC-0072. O vídeo binário e o timestamp **não foram verificados diretamente pelo GPT**; a divergência preexistente de duration/timecode no doc 03 continua `STALE_EVIDENCE / TO_RECONCILE`. Diferenciar `NOTEBOOKLM_REPORTED` de `DIRECT_VIDEO_PROVEN` e de `TÉO_AS_IS_DOCUMENTED`.

### Achados reportados pelo NotebookLM — sem promover a prova direta

- A <GESTORA-PROC> teria usado `Shift+F6` para chamar a **rotina customizada `_F190C`**, e não a rotina padrão `FINR190`, por volta de `00:43:51–00:46:14`; a execução teria sido abortada por erro **"não tá compilado"**, com print para TI. **Nenhum download/arquivo de baixas foi visto na gravação**. A referência TÉO `kp02_t01` continua a mencionar FINR190, gerando **`ROUTINE_IDENTITY_DRIFT / TO_RECONCILE`**: investigar versionamento/customização, não corrigir retroativamente a fonte TÉO sem autoridade.
- Segundo fala **informada verbalmente** por <GESTORA-PROC>, uma execução normal produz **cinco arquivos**: Pagar Excel; Receber Excel; Receber PDF por data; Pagar PDF por data; Pagar PDF por natureza. São **cinco saídas de uma tentativa de execução da mesma rotina customizada**, não cinco rotinas demonstradas. Não houve arquivo gerado na gravação.
- Os arquivos teriam informação financeira por fornecedor/cliente e CNPJ, para importação na Contabilidade Aliança; **nomes, campos, formatos efetivos e totais não foram observados**. Datas, empresas/filiais, natureza e opção "Da Carteira?" **não ficaram visíveis na tela de parâmetros**.
- **Títulos em aberto** (reportadamente exportados em outra atividade `ACT-15`) são **outra fonte e outra operação**, não baixas liquidadas. Demandam item próprio quando conferidos com fonte AS-IS e artefato; não misturar nos R01/R02.

### Impacto no tracker

- **R01:** `G1=PASS` para a *etapa/finalidade documentada no TÉO*, com complemento `NOTEBOOKLM_REPORTED` da tentativa fracassada; `G2=PENDING` (arquivos descritos, não vistos); `G3=PENDING` (ERP/customização/owner exato); `G4=PENDING`; `G5=TEST_NOT_RUN`; `G6=PENDING`.
- **R02:** mesmos gates. TÉO e doc 03 descrevem saída; NotebookLM **não observou geração física**. Não rebaixar existência documental a ausência de processo.
- **Candidatos `FK2010.FK2_DATA` e `FK1010.FK1_DATA` permanecem PROVEN somente no dicionário DAVI**, **NÃO** vinculados à rotina `_F190C`. Sem fonte/ADVPL da customização e amostra real, `G4` não avança.
- Métricas conservadas: **2/60 = 3,3% coleta; 2/90 = 2,2% auditoria; 0/15 concluídos**. Houve evidência de contexto, mas **nenhum gate novo homologado** nesta rodada.

### Pendências delimitadas / anti-loop

1. **TI/Protheus owner:** localizar fonte/cadastro e status de compilação da customização `_F190C`, se ela delega à `FINR190` e quais tabelas, colunas, filtros e layouts efetivamente lê (sem assumir FK1/FK2).
2. **Controladoria:** amostra sanitizada dos **cinco arquivos** exportados em **uma competência conhecida**; conferir cabeçalhos e totais, identificando Excel/PDF por data/natureza.
3. **TÉO/video:** confirmar visualmente `Shift+F6`, `_F190C`, erro, timestamp e contexto; reconciliar o timecode anômalo documentado.
4. **Títulos em aberto:** identificar rotina, layout e ACT-15 em evidência original antes de criar item filho/alterar denominador.

**STOP:** não preparar endpoint de baixas ou SQL de equivalência enquanto o owner não comprovar a semântica de `_F190C`. Novo desvio em relação ao relatório TÉO só autoriza `EXECUTION_DRIFT` quando confirmado pela fonte primária competente. `IMPLEMENTATION_AUTHORIZED=NO` para esses relatórios.

## 8. Pesquisa TOTVS oficial — mapeamento FINR190 → FINSV010 (20/10/2026)

**Referência:** [doc 46, seção L1.2](./46-t01-report-source-inventory-v1.md) com URLs públicas da TOTVS. O relatório Smart View `FINSV010` substitui `FINR190` nas releases de referência, mas **não confirma o comportamento da customização DELPI `_F190C`**. O NotebookLM reportou erro de compilação e nenhuma geração real de arquivo na gravação.

| Papel | Tabela lógica do FINSV010 conforme TOTVS | Resultado na DELPI |
|---|---|---|
| Título receber | `SE1` | TO_INVENTORY |
| Título pagar | `SE2` | TO_INVENTORY |
| Natureza | `SED` | TO_INVENTORY |
| Motivo baixa | `F7G` | TO_INVENTORY |
| Evento de baixa receber | `FK1` | `FK1010.FK1_DATA` encontrado via DAVI; outros campos/joins pendentes |
| Evento de baixa pagar | `FK2` | `FK2010.FK2_DATA` encontrado via DAVI; outros campos/joins pendentes |
| Movimento bancário | `FK5` | TO_INVENTORY |
| Rastreio movimento | `FKA` | TO_INVENTORY |

O dicionário e docs demonstram *candidatos físicos* e *semântica genérica*; não comprovam paridade `_F190C`, parâmetros do relatório, layouts PDF/Excel, cliente/fornecedor+CNPJ efetivamente exportados, moeda, baixas parciais, natureza, chave e deduplicação.

**Próxima coleta delimitada:** inspecionar fonte `_F190C` no owner TI/ADVPL e metadados autorizados (DAVI) das oito famílias; obter os cinco arquivos sanitizados. Só então vincular `output_field → physical_column → join → filter → totals`. `G1 PASS` para R01/R02 se mantém; `G2/G3/G4 PENDING`; `G5 TEST_NOT_RUN`; `G6 PENDING`. **Progressos permanecem 2/60 coleta e 2/90 auditoria**, sem inflar percentuais por evidência adjacente.

## 9. Rodada L1.3 — DAVI: dicionário físico de oito famílias (20/10/2026)

**Ferramenta executada:** DAVI `discover_delpi_information` → `get_protheus_table` (8 consultas) e `list_protheus_table_columns` (8 consultas, página 1, limite 50). Todos os retornos `status=ok`. **Prova de entradas no dicionário SX2/SX3 acessível, não prova de linhas na base SQL, SELECT físico, join ou semântica da customização `_F190C`.** O retorno da lista inclui `X3_CAMPO, X3_DESCRIC, X3_TIPO, X3_TAMANHO, X3_DECIMAL`; o sufixo `010` foi validado apenas nessas entradas de catálogo, não inferido para outras empresas/filiais.

| Entrada dicionário | X2_NOME | Campos relevantes observados (descrições resumidas; não são bindings de output ainda) | SX3 observado |
|---|---|---|---|
| `SE1010` | Contas a Receber | `E1_FILIAL`, `E1_CLIENTE`, `E1_LOJA`, `E1_NOMCLI`, `E1_NUM`, `E1_PARCELA`, `E1_NATUREZ`, `E1_EMISSAO`, `E1_VENCTO`, `E1_VALOR`, `E1_SALDO`, `E1_BAIXA` | 50 de 274 (página 1) |
| `SE2010` | Contas a Pagar | `E2_FILIAL`, `E2_FORNECE`, `E2_LOJA`, `E2_NOMFOR`, `E2_NUM`, `E2_PARCELA`, `E2_NATUREZ`, `E2_EMISSAO`, `E2_VENCTO`, `E2_VALOR`, `E2_BAIXA` | 50 de 255 |
| `SED010` | Naturezas | `ED_FILIAL`, `ED_CODIGO`, `ED_DESCRIC` | 50 de 113 |
| `F7G010` | Motivos de Baixa | `F7G_FILIAL`, `F7G_SIGLA`, `F7G_DESCRI`, `F7G_CART`, `F7G_MOVBCO` | 10 de 10 |
| `FK1010` | Baixas a Receber | `FK1_FILIAL`, `FK1_IDFK1`, `FK1_DATA`, `FK1_VALOR`, `FK1_MOEDA`, `FK1_NATURE`, `FK1_VENCTO`, `FK1_HISTOR`, `FK1_MOTBX`, `FK1_IDDOC`, `FK1_IDPROC` | 35 de 35 |
| `FK2010` | Baixas a Pagar | `FK2_FILIAL`, `FK2_IDFK2`, `FK2_DATA`, `FK2_VALOR`, `FK2_MOEDA`, `FK2_NATURE`, `FK2_VENCTO`, `FK2_HISTOR`, `FK2_MOTBX`, `FK2_IDDOC`, `FK2_IDPROC` | 34 de 34 |
| `FK5010` | Movimentos Bancários | `FK5_FILIAL`, `FK5_IDMOV`, `FK5_DATA`, `FK5_VALOR`, `FK5_NATURE`, `FK5_BANCO`, `FK5_AGENCI`, `FK5_CONTA`, `FK5_DOC`, `FK5_SEQ` | 39 de 39 |
| `FKA010` | Rastreio de Movimentos | `FKA_FILIAL`, `FKA_IDFKA`, `FKA_IDPROC`, `FKA_IDORIG`, `FKA_TABORI` | 5 de 5 |

**Tipos efetivamente retornados (exemplos):** `FK2_DATA` tipo D, comprimento 8; `FK2_VALOR` tipo N, comprimento 16, 2 decimais; `FK2_FILIAL` tipo C, comprimento 2; `FK1_DATA` tipo D, comprimento 8; `FK1_VALOR` tipo N, comprimento 16, 2 decimais. São propriedades do catálogo Protheus, não validação SQL física.

**Correção de rigor:** `FK5_IDPROC` não está entre os campos confirmados no resumo desta rodada; não promover esse campo como PROVEN sem buscar página/metadata específica. A identidade de relacionamento `FK1/FK2 → FK5/FKA → SE1/SE2`, suas cardinalidades, exclusão lógica, filiais e campos de CNPJ permanecem **TO_INVENTORY**.

**Acesso às linhas:** `get_protheus_table` e `list_protheus_table_columns` retornam **metadados**, não `SELECT` nem contagens de lançamentos. Não foi executado SELECT de tabela financeira ou prova de amostra real. A disponibilidade de `get_financeiro_*` na VISTA é adjacente, não uma leitura equivalente da rotina `_F190C`.

**Gates R01/R02:** G1 PASS; G2 PENDING (colunas observadas no **dicionário**, não no output); G3 PENDING (owner local da customização), G4 PENDING (joins/bindings/filters incompletos), G5 TEST_NOT_RUN, G6 PENDING. **Percentuais inalterados:** 2/60 = 3,3% coleta; 2/90 = 2,2% auditoria; 0/15 concluídos. Novo ganho é inventário físico de metadados, sem gate inteiramente satisfeito.

**Próxima verificação bounded:** (1) obter source da rotina `_F190C` ou amostra dos cinco arquivos; (2) investigar estrutura de vínculos e chaves no dicionário e no código de leitura `api-delpi`; (3) consultar owner autorizado para execução de SELECT com datas/escopo parametrizados e dados sanitizados. Nenhuma migration/rota/API implementada neste gate.

## 10. Rodada L1.4 — SQL READ pós-deploy: 8 tabelas com registros (20/10/2026)

**Mecanismo efetivamente usado:** DAVI `discover_delpi_information` → `execute_readonly_sql`; execução das consultas SELECT pelo conector; sem escrita, sem dados pessoais/valores brutos registrados neste documento.

### Provas realizadas

- **8/8** consultas `SELECT TOP 1 1 AS PRESENT FROM [TABELA] WHERE D_E_L_E_T_ = ''` retornaram `status=ok` e **uma linha** por tabela, comprovando ao menos uma linha não excluída logicamente em cada tabela física `SE1010, SE2010, SED010, F7G010, FK1010, FK2010, FK5010, FKA010`.
- **8/8** consultas `SELECT TOP 1` de campos de negócio explícitos retornaram `status=ok`. Presença de dados não nulos/não vazios na linha inspecionada: `FK2010`: `FK2_DATA, FK2_VALOR, FK2_NATURE, FK2_IDFK2`; `FK1010`: `FK1_DATA, FK1_VALOR, FK1_NATURE, FK1_IDFK1`; `SE2010`: `E2_EMISSAO, E2_BAIXA, E2_FORNECE, E2_VALOR`; `SE1010`: `E1_EMISSAO, E1_BAIXA, E1_CLIENTE, E1_VALOR`; `SED010`: `ED_CODIGO, ED_DESCRIC`; `F7G010`: `F7G_SIGLA, F7G_DESCRI`; `FK5010`: `FK5_DATA, FK5_VALOR, FK5_IDMOV`; `FKA010`: `FKA_IDFKA, FKA_IDPROC, FKA_TABORI`.
- **Atenção a scope:** na única linha inspecionada de **cada** tabela, o campo `*_FILIAL` veio vazio. Isso pode representar semântica compartilhada no ERP; **não inferir** empresa/filial nem aplicar `*_FILIAL='01'` sem provar contrato de compartilhamento.
- **5/5** verificações de existência por período `>= '20260101'` retornaram `status=ok` e uma linha: `FK2_DATA, FK1_DATA, FK5_DATA, E2_BAIXA, E1_BAIXA`. Isso demonstra pelo menos um registro com campo data compatível com o filtro em cada tabela, **não** demonstra quantos eventos, total por competência ou se o período é completo. A data `E1_BAIXA/E2_BAIXA` é data do título, não substituir pela data/evento da FKx sem regra de semântica.

### Pertinência para as cinco saídas verbalmente relatadas da customização `_F190C`

| Tabela | Dados observados em registros reais | Relevância para R01/R02 | Limitação |
|---|---|---|---|
| `FK2010` | data, valor, natureza e identificador de baixa | **Forte candidata** a fatos de baixas a pagar | faltam joins ao título/fornecedor e paridade |
| `FK1010` | data, valor, natureza e identificador de baixa | **Forte candidata** a fatos de baixas a receber | faltam joins ao título/cliente e paridade |
| `SE2010` | data de emissão/baixa, código fornecedor, valor do título | dimensão de títulos a pagar | `E2_VALOR` não equivale automaticamente a cada baixa |
| `SE1010` | data de emissão/baixa, código cliente, valor do título | dimensão de títulos a receber | `E1_VALOR` não equivale automaticamente a cada baixa |
| `SED010` | código e descrição da natureza | rótulos para PDF pagar/natureza | vínculo FKx↔SED não confirmado |
| `F7G010` | sigla e descrição do motivo | motivo/classificação de baixas | uso efetivo pela `_F190C` a demonstrar |
| `FK5010` | data, valor e ID do movimento bancário | conciliação/contexto financeiro | inclui movimentos que podem não representar baixa de título |
| `FKA010` | IDs e tabela de origem de rastreabilidade | possível amarração entre eventos | cardinalidades e joins sem prova |

**Campos de CNPJ do cliente/fornecedor e chaves da customização:** não localizados nesta rodada; podem exigir cadastros `SA1/SA2` e vínculos adicionais, mas isso é **hipótese a auditar**, não contrato aprovado.

**Status do lote:** `SQL_READ=PASS` (8/8 tabelas); `RECENT_RECORD_EXISTS=PASS` (5/5 tabelas com campo data consultado); `ROW_SAMPLE_ONLY`; `JOIN_VALIDATION=TEST_NOT_RUN`; `OUTPUT_PARITY=TEST_NOT_RUN`; `ROUTINE_SOURCE=_F190C_TO_INVENTORY`. Sem validação de quantidade, total mensal, duplicidade, flags de exclusão para joins, divergência financeira ou comportamento de folha de resultados.

**Percentuais de aceite formal R01/R02:** G1 PASS, G2/G3/G4 PENDING, G5 TEST_NOT_RUN, G6 PENDING; **2/60 = 3,3% de coleta e 2/90 = 2,2% de auditoria**, já que tabelas com dados são apenas uma subparte de G4. Não contar `TOP 1` como relatório concluído.

**Próxima ação bounded:** inventariar chaves e relacionamento (dicionário `SIX/SX9` e código `_F190C`), filial compartilhada versus escopo da empresa, campos de identificação e CNPJ, depois comparar uma competência com exportação sanitizada. `IMPLEMENTATION_GATE=NO_GO`.

## 11. Rodada L1.5 — Teste de chaves, índices e natureza (20/10/2026)

**Origem:** DAVI `execute_readonly_sql`, consulta autorizada de SIX010/SX9010 e probes de dados reais. Consultas somente SELECT, sem exportar valores ou IDs de clientes/títulos.

### Índices PROVEN no dicionário SIX

- `FK1`: `FK1_FILIAL+FK1_IDFK1` (ordem 1), `FK1_FILIAL+FK1_IDDOC+FK1_SEQ` (ordem 2), `FK1_IDDOC+FK1_SEQ` (ordem 5).
- `FK2`: `FK2_FILIAL+FK2_IDFK2` (ordem 1), `FK2_FILIAL+FK2_IDDOC+FK2_SEQ` (ordem 2), `FK2_IDDOC+FK2_SEQ` (ordem 5).
- `FK5`: `FK5_FILIAL+FK5_IDMOV` (ordem 1), `FK5_IDDOC+FK5_SEQ` (ordem 6), `FK5_IDMOV` (ordem C).
- `FKA`: `FKA_FILIAL+FKA_IDFKA` (ordem 1), `FKA_FILIAL+FKA_IDPROC+FKA_IDORIG+FKA_TABORI` (ordem 2).
- `SE1`: `E1_FILIAL+E1_PREFIXO+E1_NUM+E1_PARCELA+E1_TIPO` (ordem 1).
- **Índice registrado não significa constraint única/PK declarada no SQL Server**; é chave de navegação Protheus. A consulta `TOP 30` não constitui catálogo completo dos índices das oito famílias.

### Relacionamentos declarados no SX9

`SED → FK1` e `SED → FK2` com expressão `ED_CODIGO`. Outros exemplos observados: `SA6 → FK5` pela expressão `A6_COD+A6_AGENCIA+A6_NUMCON`, `SE1 → ...`, `SE2 → ...`. **SX9 não comprovou, nesta rodada, vínculo direto `FK1/FK2 → SE1/SE2`**. Não inventar uma condição de join de título.

### Probes SQL (TEST RUN)

| Teste | Evidência | Resultado |
|---|---|---|
| `FK2_NATURE = SED.ED_CODIGO` | JOIN `FK2010 F` ↔ `SED010 N`, ambos `D_E_L_E_T_=''`, `TOP 1` | **PASS parcial**: ≥1 par encontrado; não mede cobertura |
| `FK1_NATURE = SED.ED_CODIGO` | JOIN `FK1010 F` ↔ `SED010 N`, ambos com filtro de exclusão | **PASS parcial**: ≥1 par encontrado; não mede cobertura |
| `FK2_IDFK2` duplicado | GROUP BY ID, HAVING COUNT(*)>1 | **Nenhum duplicado encontrado no conjunto não excluído** |
| `FK1_IDFK1` duplicado | GROUP BY ID, HAVING COUNT(*)>1 | **Nenhum duplicado encontrado no conjunto não excluído** |
| `FKA_IDFKA` duplicado | GROUP BY ID, HAVING COUNT(*)>1 | **Nenhum duplicado encontrado no conjunto não excluído** |

**Cautelas:** as probes de unicidade acima agrupam apenas o identificador e não demonstram outras chaves/cross-branch. As provas de join de natureza só demonstram existência de um par, não cardinalidade 1:1, ausência de duplicação, completude por competência/filial ou regra exata da `_F190C`. Filial vazia nas amostras anteriores exige validar convenção compartilhada antes de incluir filtro de filial. Não usar `FK2_DATA=E2_BAIXA` ou equivalência de `FK2_IDDOC=E2_*` sem fonte.

**Próximo teste delimitado:** cardinalidade/cobertura de `FK1/FK2 → SED` com `COUNT`/join protegidos e filtros por competência; inventariar os identificadores/relacionamentos de título via fonte `_F190C`, `FK7` e dicionário antes de tentar `FKx → SE1/SE2`. `JOIN_NATURE=PARTIAL_PASS`; `JOIN_TITLE=TEST_NOT_RUN`; `OUTPUT_PARITY=TEST_NOT_RUN`; **G4 permanece PENDING**. Métricas inalteradas: `2/60 = 3,3%` coleta; `2/90 = 2,2%` auditoria.

## 12. L1.6 — Validação SQL de FK7 / título / exceções (20/10/2026)

**Origem:** DAVI `execute_readonly_sql` com SQL SELECT parametrizado no texto, `D_E_L_E_T_=''` em tabelas de negócio, filtro `FK1_DATA/FK2_DATA >= '20260101'`. Este registro contém somente **agregados**, sem valores financeiros, identificadores individuais ou PII. **Representa o ambiente consultado em 20/10/2026, não snapshot imutável.**

### Descoberta do vínculo correto

- `FK7010` existe fisicamente e possui dados (SELECT TOP 1 PASS). SX3 expõe `FK7_IDDOC, FK7_ALIAS, FK7_FILTIT, FK7_PREFIX, FK7_NUM, FK7_PARCEL, FK7_TIPO, FK7_CLIFOR, FK7_LOJA, FK7_FILIAL, FK7_CHAVE, FK7_IDPAI`.
- SX9 aponta `FK7 → FK1` e `FK7 → FK2` via `FK7_IDDOC`; `SE1 → FK7` via `E1_FILIAL+E1_PREFIXO+E1_NUM+E1_PARCELA+E1_TIPO+E1_CLIENTE+E1_LOJA`; `SE2 → FK7` via `E2_FILIAL+E2_PREFIXO+E2_NUM+E2_PARCELA+E2_TIPO+E2_FORNECE+E2_LOJA`. Também há vínculo SX9 `SA1/SA2 → FK7` (cliente/fornecedor e loja) e `FKA → FK1/FK2/FK5` (rastreio).
- SIX `FK7`: índice 1 `FK7_FILIAL+FK7_IDDOC`, índice 3 chave título composta; índice 5 `FK7_IDDOC`. `SELECT TOP 1 ... GROUP BY FK7_IDDOC HAVING COUNT(*) > 1` não encontrou duplicado entre registros não excluídos. **Índices SX/SIX não constituem constraints DB, e singularidade observada não valida o join da customização `_F190C`.**

### Resultados por período — `>= 2026-01-01`

| Teste SQL READ | Resultado | Classificação |
|---|---:|---|
| Baixas `FK2010` no período | 8.969 | PROVEN no instante da consulta |
| `FK2_IDDOC` com par em `FK7010.FK7_IDDOC` | 8.911 | PASS para existência |
| FK2 sem FK7 correspondente | **58** | GAP a classificar |
| `FK2 → FK7 → SE2` por `FK7_ALIAS='SE2'` + prefixo/número/parcela/tipo/fornecedor/loja | 8.911 | PASS de existência; não paridade |
| Baixas `FK1010` no período | 5.578 | PROVEN no instante da consulta |
| FK1 sem FK7 correspondente | **0** | PASS |
| `FK1 → FK7 → SE1` por `FK7_ALIAS='SE1'` + prefixo/número/parcela/tipo/cliente/loja | 5.578 | PASS de existência |
| FK2 sem `SED` correspondente pela natureza | **49** | GAP a classificar |
| FK1 sem `SED` correspondente | **0** | PASS |
| `FK7_ALIAS='SE2'` com título SE2 encontrado (histórico sem filtro de data) | 96.454 de 96.454 | PASS de existência |
| `FK7_ALIAS='SE1'` com título SE1 encontrado (histórico sem filtro de data) | 114.615 de 114.627 | **12 gaps**, investigar |

**ATENÇÃO:** os números são relativos às condições SQL indicadas. `EXISTS` evita contar múltiplas linhas como uma única baixa repetida, mas não prova cardinalidade de todos os joins, diferenças entre filiais ou seleção efetiva da rotina. Os 12 gaps SE1 históricos não foram relacionados às 5.578 baixas de 2026.

### Classificação objetiva das exceções FK2 em 2026

`FK2` sem `FK7`, por `FK2_TPDOC` / `FK2_RECPAG`:
- `ES/R`: 29
- `BA/P`: 17
- `VL/P`: 9
- `CP/P`: 3

`FK2` sem correspondência SED (por tipo):
- `BA`: 48
- `ES`: 1

**Não atribuir significado de negócio aos códigos BA/ES/VL/CP sem consultar dicionário/owner.** A ausência do vínculo pode representar semântica legítima, customização ou inconsistência. `G4` fica **PENDING**, não FAIL, até validar o universo incluído no relatório da <GESTORA-PROC>.

### Próxima etapa e encerramento condicionado

1. Conferir política de filiais, ramo real `FK7_FILTIT` e join completo com `FK7_ALIAS`, inclusive possíveis documentos de origens distintas.
2. Inspecionar `_F190C` em ADVPL ou um conjunto representativo dos cinco arquivos, com filtros, layouts, fornecedor/cliente, CNPJ, valores, ordenações e tratamento das exceções.
3. Testar `FK1/FK2 → FKA → FK5` somente após identificar regra de rastreabilidade e cardinalidade sem multiplicar valor de baixa.
4. Executar paridade exata por competência/empresa/filial e obter aceite da Controladoria; sem isso **`_F190C` não está replicado/homologado**.

**Síntese:** `FK7_TABLE=PROVEN`; `FKx_TO_FK7_TO_TITLES=PASS_FOR_EXISTENCE`; `EXCEPTIONS=TO_CLASSIFY`; `_F190C_SOURCE=TO_INVENTORY`; `REPORT_PARITY=TEST_NOT_RUN`; `G4/G5/G6=PENDING`. Métricas do tracker **inalteradas** (2/60 coleta, 2/90 auditoria, 0/15 concluídos), porque o gate G4 também exige joins, escopo e semântica homologados.

### Complemento L1.6 — Rastreabilidade FKA

Consultas READ com EXISTS(FKA_IDORIG=FK2_IDFK2) encontraram **8.969/8.969** eventos FK2 em 2026; EXISTS(FKA_IDORIG=FK1_IDFK1) encontrou **5.578/5.578** eventos FK1. Também foi encontrado ao menos um par de IDs FKA_IDORIG=FK5_IDMOV em FK5.

**Cautela:** a FKA contém FKA_TABORI e FKA_IDPROC. As comparações acima NÃO filtram a tabela de origem nem provam que os registros dizem respeito ao mesmo processo. Coincidência de ID != join de negócio validado. Não somar ou deduplicar valores por esse join. Exigem-se fonte da customização _F190C, regras de origem/processo e amostras do relatório antes de homologação.

**Encerramento da rodada:** auditoria de chaves e existência em SQL realizada; R01/R02 G4 PENDING, G5 TEST_NOT_RUN, G6 PENDING. STOP para homologação por dependência de fonte ADVPL/owner TI e dos cinco arquivos originais/Controladoria. Sem implementação de API ou alteração de permissions.

### Complemento L1.7 — Auditoria D4: RECPAG, histórico e pareamento de estorno (20/10/2026)

Achados novos sobre coluna/relacionamento, obtidos por SQL READ em produção (09/2026 e 01–20/10/2026). Detalhes e matriz de decisão no doc 48 §16.

- **`FKx_RECPAG`**: evidência comportamental indica direção de caixa do próprio evento (estornos em FK2 saem `R`; em FK1 saem `P`), e não apenas o lado da tabela. Existem `VL/R` e `BA/R` em FK2 sem vínculo a estorno — hipótese «valor recebido de fornecedor» a homologar.
- **`FKx_HISTOR` discrimina subtipo dentro de `BA`**: «Baixa por Compensacao», «Bx.Emis.Fatura NNNN», «BAIXA IMP PCC DAC», «Compens. Autom. Adiantamento», «Valor pago s/ Titulo». O `FKx_TPDOC` sozinho não separa baixa bancária de compensação.
- **Padrão de estorno comprovado**: estorno de «valor pago s/ título» gera **par `ES/P` + `VL/R`** com mesmo `FKx_IDDOC`, valor e data (4/4 casos em FK2). Estorno de baixa com título gera `ES/R` único. Esse pareamento por `IDDOC`+valor+data é nível-documento, não ponteiro explícito — qualquer netting exato exige homologação.
- **`IDDOC` compartilhado por tipos distintos é real e parcial**: 6 docs Sep com `VL`+`CP` (compensação parcial + pagamento), 9 com `VL`+`BA`, 1 com `CP`+`BA`. Somar eventos por doc sem classificar tipo/direção duplica ou confunde.
- **`FK2` sem `FK7` (58 casos em 2026) parcialmente explicado**: `ES/R` sem link FK7 é compatível com estorno cujo documento de baixa não gera vínculo próprio; amostra confirmou ao menos 1 `ES` sem FK7 onde o `IDDOC` pertence à baixa original. Não fecha G4 — segue PENDING.
- **`FKB010` confirmado como catálogo canônico de `FKx_TPDOC`** (SX3 `X3_VALID = ExistCpo("FKB")`); ~45 códigos por filial; somente BA/VL/ES/CP presentes nos fatos do período.
- **`FKx_VALOR` sempre positivo** no período (FK1 e FK2) — o sentido não está no sinal do valor.
- Única moeda observada: `01`.

Sem mudança nas métricas do tracker; G4/G5/G6 permanecem PENDING/TEST_NOT_RUN por dependência de homologação do owner financeiro.



## 11. Rodada CF-C2-FULL-EVIDENCE-RECONCILIATION-001 — Pasta de evidências do PO (23/10/2026)

**Fontes desta rodada:** pasta `fechamento` do PO (1 vídeo 54:44 + 6 PDFs + 10 XLSB + 3 XLSX, competência 09/2026); roster `Contabilidade liberações.xlsx`; frames full-res do vídeo (timecodes no doc 83 §3); fontes `FINR190_DLP.PRX`, `DEL100.PRW` (acervo); rodadas 1–13 (doc 80). **Crosswalk completo em `83-ciclo2-crosswalk-evidencias-r01-r15.md`.** Artefatos privados não versionados; evidências sanitizadas.

### Gates promovidos — evidência por item

| Item | Gate | Evidência exata (artefato / timecode) | Data |
|---|---|---|---|
| R01 | G2,G3,G4 | `Pagos por dt.pdf` = `SIGA/DLP06R01.prt/v.12`; `Pagos por nat.pdf` = `nat.prt`; `pagos 09 26.xlsb` "Relacao de Baixas" 974 linhas; menu "Relação de Baixas DLP" (vídeo 13:00); roster FINR190; fonte `FINR190_DLP.PRX` (commit `0df96daafe`, blob `92bcae1c`) com `TRCell`→`E5_*` e WHERE que reproduz população oficial 948 + motivo 5/5 (doc 80 §17.B/C) — detalhe §11.1 | 2026-10-23 |
| R02 | G2,G3 | `Recebidos.pdf` = `DLP06R01.prt` (layout compartilhado); `Recebidos.xlsb` 686 linhas; roster FINR190 + menu; **G4 revisto → PENDING**: WHERE do FINR190 (649/690) **não** reproduz o artefato 657 (doc 80 §17.D) — produtor = `DLP06R01` custom, fonte ausente do acervo (`BLOCKED`); binding SE5'R'×SE1 provado só em nível de população | 2026-10-23 |
| R03 | G1,G2,G3 | vídeo 35:00/37:00 previews "Registro de Inventário Modelo P7" (MATRIZ, 30/09/2026, totais 3.776.994,69 / ~2.756.1xx); `Estoque.pdf` 3.946.431,87 e `Resumo Estoque.pdf` 2.976.967,56 (escopo MP/PA/PI); roster MATR460; SPEDFISCAL→Bloco H | 2026-10-23 |
| R05 | G1,G2,G3 | `Entradas e saidas.pdf` = `SIGA/MATR320.prt/v.12` período 01–30/09/2026 MATRIZ, layout por tipo (**promovido G4/G5 na rodada CF-C2-STOCK-RULES-CONSOLIDATION-002 — §11.2**) | 2026-10-23 |
| R06 | G1,G2,G3 | `cpv 09 26 matriz.xlsb` "Kardex Fisico-Financeiro" 14.382 linhas; roster MATR910 | 2026-10-23 |
| R07 | G1,G2,G3 | `Invent.xlsb` kardex docs "INVENT" TES 999/499; roster MATR910 | 2026-10-23 |
| R08 | G1,G2,G3 | `Material em processo.xlsb` "Saldo em Processo" 57.359 linhas c/ ORDEM PRODUCAO; roster MATR989 | 2026-10-23 |
| R09 | G1,G2,G3 | `Fat x MOD.xlsb` abas Fl01/Fl02 PA→MOD + Horas + Custo Unit; roster DLP204 | 2026-10-23 |
| R10 | G1,G2,G3,G4 | `CC matriz.xlsb` = export **SD1** (sheet `SCAGQGA0.XML`; linha 0 = literal `SD1`, headers = títulos SX3 `D1_*` — binding 1:1 monotabela); vídeo 47:00 mesma operação EDAPP (`SCAGPOU0.XML`); roster EDAPP "Faturamento e CC" — detalhe §11.1 | 2026-10-23 |
| R11 | G1,G2,G3,G4 | `NF a desconsiderar.xlsb` = export **SD2** (linha 0 = literal `SD2`, headers SX3 `D2_*`; Tipo Saida 594, CF 5101); roster EDAPP "NF à desconsiderar" — detalhe §11.1 | 2026-10-23 |
| R12 | G1,G2,G3 | vídeo 04:00 "Recálculo do Custo de Reposição" (parâmetros íntegros) + 14:47 "Acompanha Custo → Novo fechamento de custo" (execução real); `DEL100.PRW` fonte | 2026-10-23 |
| R13 | G1 | `Arquivos de envio` checklist: Extratos/XP/BB/Aplicações — externalidade confirmada | 2026-10-23 |
| R15 | G1,G2 | vídeo 14:47 wizard "Novo fechamento de custo" executado (JOICI, Matriz); SB9 snapshot PROVEN (doc 80 §21) | 2026-10-23 |

**Não promovidos:** G4 de R02 (produtor custom `DLP06R01` sem fonte no acervo — §11.1), R03/R06–R09/R12/R15 (bindings físicos não comprovados — candidatos SB9/SD3 documentados como tal); G5 de todos exceto R01/R02/R05 (paridade monetária integral pendente); G6 de todos (exige aceite humano).

**Resoluções desta rodada:** `DLP06R01.prt`/`nat.prt` = **layouts** do relatório de baixas (pagos **e** recebidos) — o mesmo `.prt` é usado por rotinas distintas; para pagar, produtor = FINR190 com fonte+WHERE provados; para receber, produtor = custom `DLP06R01` **sem fonte no acervo** (FINR190 descartado pelo WHERE, doc 80 §17.D); P7 = "Registro de Inventário Modelo P7"/MATR460 com artefatos e duas emissões/escopos (E2 estreitado); execução do fechamento observada (E5 estreitado); doc 71 candidato→confirmado; docs 76/77 paths resolvidos (CC matriz=SD1, Analise=variação CM).

**Métricas (após rework §11.1 + paridade §11.2):** `COLETA = 39/60 = 65,0%`; `AUDITORIA = 41/90 = 45,6%`; `RELATORIOS_CONCLUIDOS = 0/15 = 0,0%`.

**Residuais por owner** (doc 83 §5, doc 82 §2, doc 84): fonte do relatório de receber `DLP06R01` custom (R02 G4, TI/ERP); subconjunto do log de inconsistências dos relatórios de baixas e versão RPO do FINR190 (TI/ERP); parâmetros efetivos por emissão P7 + fonte `matr460.prx`/produtor (R03 — binding de totalização provado rodada 15); artefato de consumo por OP (R04, Controladoria); bindings físicos R06–R09/R12 (G4); prova de qual passo grava SB9 (R15); DDL views + jobs/SPs (DBA E3/E4); importação (R14); aceite funcional G6 de todos os itens (Controladoria). ~~Residual MP ~R$950~~ **eliminado** — ponte por produto fecha 100% do Δ +8.631,73 (doc 80 §33.B).

### 11.1 — Rework de gates (revisão G4 R01/R02/R10/R11, 2026-10-23)

Definição canônica: G4 exige **bindings físicos (tabelas, colunas, joins, filtros)** — não basta identificar rotina/layout/artefato. Resultado da revisão por item:

**R01 — G4 mantido.** Vínculo explícito no fonte `FINR190_DLP.PRX` (`docs/13-fontes-totvs-protheus/06. Financeiro/FINR190/`, commit `0df96daafe`, blob `92bcae1c0487a390a91796365be361add9f011a8`):

- Colunas exibidas (TRCell) → campos físicos: `Prf`→`SE5.E5_PREFIXO`; `Numero`→`E5_NUMERO`; `Prc`→`E5_PARCELA`; `TP`→`E5_TIPODOC`; `Cli/For`→`E5_CLIFOR`; `Natureza`→`E5_NATUREZ` (+descrição `SED.ED_DESCRIC` via `TRPosition SED ← E5_NATUREZ`); `Vencto`→`E5_VENCTO`; `Historico`→`E5_HISTOR`; `Dt Baixa`→`E5_DATA`; `Valor Original`→`E5_VALOR`; `Jur/Multa`→`E5_VLJUROS`; `Correcao`→`E5_VLCORRE`; `Descontos`→`E5_VLDESCO`; `Total Baixado`→`E5_VALORPG`; `Bco`→`E5_BANCO`; `Dt Dig`→`E5_DTDIGIT`; `Mot`→`E5_MOTBX`; `Orig`→`E5_FILORIG`.
- Joins: SE5→SE2 via `MsSeek(FwXFilial("SE2")+prefixo+num+parcela+tipo+fornece+loja)`; FK1/FK2/FK6 para valor movido/estorno; SED por `E5_NATUREZ`.
- Filtros: `E5_RECPAG='P'`, faixa `MV_PAR` (datas de baixa, SX1 params 01–02), exclusões fixas de `E5_TIPODOC` no código, `Da/Até Filial Origem` (SX1 33–34 → `E5_FILORIG`).
- Escopo: competência 09/2026, filial Matriz (01).
- Verificação: WHERE do fonte reproduz população oficial **948** e motivo 5/5 (doc 80 §17.B/C). Residual fora do G4: versão compilada no RPO não confirmada; paridade monetária/por registro = G5.

**R02 — G4 revertido para PENDING.** Mesmo layout `DLP06R01.prt` no artefato, mas o WHERE do FINR190 ('R', exclusões fixas) gera **649/690 ≠ 657** oficial (doc 80 §17.D, PROVEN): o artefato inclui linhas JR/MT/VL/DC e 1 cancelada que o FINR190 removeria. Produtor = custom **`DLP06R01`** (nome da rotina e fonte ausentes do acervo; `DLP06P01/F01/F02/F03` verificados = utilitários não relacionados). Binding provado apenas em nível de fonte de dados (`SE5 'R'×SE1` = 657 row-level). Falta para G4: fonte do `DLP06R01` com mapeamento coluna→campo e filtros. Owner: TI/ERP (doc 82 E1).

**R10 — G4 mantido.** `CC matriz.xlsb`, sheet `SCAGQGA0.XML`: linha 0 = literal **`SD1`**, headers = títulos SX3 das colunas `D1_*` (`Filial`, `Item NF`, `Produto`, `Tipo Entrada`, `Tp.Oper`, `Vlr.Unitario`, `Vlr.Total`, `C Custo`, `C Contabil`, …). Binding 1:1, **monotabela, sem join** — o item é uma consulta genérica EDAPP, não relatório com filtro fixo; o filtro é a consulta parametrizada pelo usuário (escopo observado nos dados: filial `01`). Vídeo 47:00 mostra a mesma operação EDAPP exportando SD1 (`SCAGPOU0.XML`). Fonte: rotina EDAPP padrão TOTVS (sem fonte custom exigido para o binding físico).

**R11 — G4 mantido.** `NF a desconsiderar.xlsb`, sheet `Planilha2`: linha 0 = literal **`SD2`**, headers = títulos SX3 `D2_*` (`Tipo Saida`→`D2_TIPO`/`594`, `Cod. Fiscal`→`D2_CF`/`5101`, MD5/UUID = campos de auditoria). Mesmo raciocínio de R10: export direto da tabela via consulta genérica.

**Recontagem:** 37 gates novos (R02 G4 revertido); `COLETA = 39/60 = 65,0%`; `AUDITORIA = 39/90 = 43,3%`. R05 reclassificado: rotina `MATR320` + artefato identificados (G1–G3), **G4–G6 abertos** — não é item "concluído" *(estado na data do rework; G4/G5 promovidos na rodada seguinte — §11.2)*.


### 11.2 — Paridade monetária row-level (CF-C2-PARITY-001, 2026-10-23)

Definição canônica: G5 exige prova READ reproduzível/paridade. Executada reconciliação linha-a-linha (multiset de chaves + valores por registro) entre artefatos oficiais e SE5/SE1/SE2/SB9 via SELECT-only, competência 09/2026. Detalhe integral: **doc 84**; catálogo de regras de negócio derivadas (BR-Rxx-NNN, handoff e matriz de testes): **doc 85**.

**R01 — G5 PASS.** População 948/948 (chaves idênticas; WHERE fiel ao FINR190_DLP.PRX incl. chave exata do par de estorno `ES`); `Total Baixado` = `E5_VALOR` 948/948 sem divergência; Jur/Multa 244,07, Correção −39.365,10, Descontos 0,01 exatos; resumos impressos exatos (Baixados = Σ não-CMP/FAT, Compens. = lado CP, Bx.Fatura = FAT); `Orig` = `E5_FILORIG` 532/416 exato; `Valor Original` = `E2_VALOR` 942/948 + 5 INV aglutinados (VO = `E5_VALOR`) + 1 grupo NF+TX UNIAO (VO = 1.029,52) — 100% explicado. PDF = xlsb − log de inconsistências (ΔTB 387.629,64 = total impresso — **paridade do artefato integral: 948/948 no XLSB**; o subconjunto do log **não foi reconstruído linha-a-linha**: total do log reconstruído em agregado, identidade das linhas é residual). Residual: identidade do subconjunto do log + versão RPO. Data: 2026-10-23.

**R02 — G5 PASS (G4 permanece PENDING).** Artefato 657 linhas = 649 chaves SE5×SE1 idênticas + 8 movimentos `PA` sem título (`FINA750`, confirmados na SE5); 8 linhas de decomposição `MT`/`JR`/`DC` excluídas pelo produtor (valores embutidos no `E5_VALOR` do `VL` principal); `Total Baixado` = `E5_VALOR` exato; `Valor Original` = `E1_VALOR` 649/649 + valor da **provisão `'P'` espelhada** (MATA121/FINA050, mesmo numero/clifor) 8/8 — **Δ R$0,00** (rework: o "residual de R$1,00" era erro de soma na consolidação manual, não divergência de dado — errata no doc 80 §30); Jur/Multa 44,16 exato; resumos exatos (Baixados = Σ não-CMP, Compens. = lado CP); PDF = xlsb − log (ΔTB 40.431,46 = total impresso). Reproduzidos integralmente: os 657 registros. Hipóteses não demonstradas (escopo G4): regra geral do sem-título (3 excluídos identificados: `<RECEBIMENTO-SEM-TITULO-A>`/`<RECEBIMENTO-SEM-TITULO-B>`/`<RECEBIMENTO-SEM-TITULO-C>`), regra de supressão das decomposições e subconjunto do log — fonte `DLP06R01` (E1/TI-ERP). Data: 2026-10-23; rework de paridade 2026-10-23 (doc 84 §2).

**R03 — G4/G5 PENDING (rodada 15: binding de totalização provado, parametrização pendente).** EM PROCESSO = `Material em processo.xlsb` exato (355.240,51; MP 354.938,50 + PI 254,44); EM ESTOQUE PA/PI = MATR320 exato; `EM ESTOQUE + EM PROCESSO = TOTAL P7` exato ao centavo. **Novo (doc 80 §33.D):** EM ESTOQUE da emissão completa = saldo físico excluindo `MV_LOCPROC='99'` no `as_of` da emissão — prova centesimal (3.884.464,444 − 293.273,084 = 3.591.191,36; loc99_emissão reconstruído 293.273,088). EM PROCESSO = MATR989 (medida por OP, ≠ estoque físico de loc 99). **Pendentes:** parâmetros efetivos por emissão (E2), fonte `matr460.prx`/produtor, binding por produto/armazém, `as_of` da emissão resumida — por isso G4/G5 **mantidos PENDING**; G6 exige aceite.

**R05 — G4/G5 PASS (rodada CF-C2-STOCK-RULES-CONSOLIDATION-002).** Fonte `matr320.prx` (execução via SP `MAT056`; variante `DLPR320` descartada). **G4 PASS**: relações, fórmulas e filtros demonstrados para o escopo completo — reconciliação expandida a **10 tipos × 13 colunas, 120/120 colunas de fluxo exatas ao centavo** em estado de emissão (doc 84 §4.4, doc 80 §33.C); regras gerais SD1(`D1_DTDIGIT`)/SD2(`D2_EMISSAO`)/SD3(CF/OP/TM) + SF4 poder3/estoque. **G5 PASS**: paridade oficial incluindo temporalidade e precisão monetária — MovInt residual 0,48 resolvido (artefato de sobre-reversão; corte TTAT por timestamp de emissão — doc 80 §33.A); divergência MP +8.631,73 **integralmente decomposta por produto** (5 produtos, revalorização de custo médio da onda retificadora 20-21/10 — doc 80 §33.B, doc 84 §4.3); SA impresso = `as_of` da emissão. **G6 PENDING**: aceite funcional do owner.

**Recontagem:** 2 gates novos (G5 R01+R02); `COLETA = 39/60 = 65,0%`; `AUDITORIA = 41/90 = 45,6%`; `CONCLUÍDOS = 0/15`.
