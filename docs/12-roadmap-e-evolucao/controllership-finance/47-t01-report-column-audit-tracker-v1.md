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
| R01 | Baixas a pagar | FINR190 | Financeiro | `kp02_t01/kp02_st01` | PENDING | PENDING | PENDING | PENDING | TEST_NOT_RUN | PENDING | Controladoria + owner da fonte |
| R02 | Baixas a receber | FINR190 | Financeiro | `kp02_t01/kp02_st02` | PENDING | PENDING | PENDING | PENDING | TEST_NOT_RUN | PENDING | Controladoria + owner da fonte |
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
| 2026-10-20 | Setup | GPT (documental) | R01–R15 | 0 (sem ateste formal) | 15 | 0/60 = 0,0% | 0/90 = 0,0% | Coletar evidências artefato/vídeo/DAVI | commit de criação |
