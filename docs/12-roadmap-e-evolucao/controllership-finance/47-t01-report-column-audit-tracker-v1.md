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
| R01 | Baixas a pagar | `_F190C` (NotebookLM derivado); `FINR190` (TÉO/doc) | Financeiro | `kp02_t01/kp02_st01` | PASS | PENDING | PENDING | PENDING | TEST_NOT_RUN | PENDING | Controladoria + owner da fonte |
| R02 | Baixas a receber | `_F190C` (NotebookLM derivado); `FINR190` (TÉO/doc) | Financeiro | `kp02_t01/kp02_st02` | PASS | PENDING | PENDING | PENDING | TEST_NOT_RUN | PENDING | Controladoria + owner da fonte |
| R03 | P7 padrão / Bloco H | MATR460 | Estoque | `kp04_t01_st01/st02` | PENDING | PENDING | PENDING | PENDING | TEST_NOT_RUN | PENDING | Controladoria + owner da fonte |
| R04 | Consumo por OP | MATR860 | Produção | `kp04_t02` | PENDING | PENDING | PENDING | PENDING | TEST_NOT_RUN | PENDING | Controladoria + owner da fonte |
| R05 | Entradas e Saídas / valor estoque | a confirmar | Estoque | `kp04_t03` | PENDING | PENDING | PENDING | PENDING | TEST_NOT_RUN | PENDING | Controladoria + owner da fonte |
| R06 | CPV / Kardex 01 | a confirmar | Estoque | `kp04_t04` | PENDING | PENDING | PENDING | PENDING | TEST_NOT_RUN | PENDING | Controladoria + owner da fonte |
| R07 | Inventários / Kardex 99 | a confirmar | Estoque | `kp04_t05` | PENDING | PENDING | PENDING | PENDING | TEST_NOT_RUN | PENDING | Controladoria + owner da fonte |
| R08 | Material em Processo / H02 | a confirmar | Produção | `kp04_t07` | PENDING | PENDING | PENDING | PENDING | TEST_NOT_RUN | PENDING | Controladoria + owner da fonte |
| R09 | Faturamento × MOD | a confirmar | Custos | `kp04_t06` | PENDING | PENDING | PENDING | PENDING | TEST_NOT_RUN | PENDING | Controladoria + owner da fonte |
| R10 | Notas por Centro de Custo | SD1 citado; a confirmar | Fiscal/Contábil | `kp04_t09` | PENDING | PENDING | PENDING | PENDING | TEST_NOT_RUN | PENDING | Controladoria + owner da fonte |
| R11 | NF venda 9035 / CPV zero | a confirmar | Fiscal | `checklist doc03` | PENDING | PENDING | PENDING | PENDING | TEST_NOT_RUN | PENDING | Controladoria + owner da fonte |
| R12 | Acompanha Custos / Reposição / Refaz Saldos | rotinas a conferir | Estoque | `kp04_t10/t11/t12` | PENDING | PENDING | PENDING | PENDING | TEST_NOT_RUN | PENDING | Controladoria + owner da fonte |
| R13 | Extratos e aplicações bancárias | externa | Bancos | `kp02_t02/t03` | PENDING | PENDING | PENDING | PENDING | TEST_NOT_RUN | PENDING | Controladoria + owner da fonte |
| R14 | Importação / SWIFT / câmbio / ACSI | mista | Importações | `kp03` | PENDING | PENDING | PENDING | PENDING | TEST_NOT_RUN | PENDING | Controladoria + owner da fonte |
| R15 | Cutoff / sacramentação / SB9 | SB9 candidato, sem aceite T03 | Estoque | `kp08_t03/t04` | PENDING | PENDING | PENDING | PENDING | TEST_NOT_RUN | PENDING | Controladoria + owner da fonte |

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

- A Joici teria usado `Shift+F6` para chamar a **rotina customizada `_F190C`**, e não a rotina padrão `FINR190`, por volta de `00:43:51–00:46:14`; a execução teria sido abortada por erro **"não tá compilado"**, com print para TI. **Nenhum download/arquivo de baixas foi visto na gravação**. A referência TÉO `kp02_t01` continua a mencionar FINR190, gerando **`ROUTINE_IDENTITY_DRIFT / TO_RECONCILE`**: investigar versionamento/customização, não corrigir retroativamente a fonte TÉO sem autoridade.
- Segundo fala **informada verbalmente** por Joici, uma execução normal produz **cinco arquivos**: Pagar Excel; Receber Excel; Receber PDF por data; Pagar PDF por data; Pagar PDF por natureza. São **cinco saídas de uma tentativa de execução da mesma rotina customizada**, não cinco rotinas demonstradas. Não houve arquivo gerado na gravação.
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
