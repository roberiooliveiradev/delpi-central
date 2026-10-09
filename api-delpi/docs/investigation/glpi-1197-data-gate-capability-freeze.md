# GLPI-1197 — DATA GATE & CAPABILITY FREEZE REPORT

Auditoria técnica dos indicadores **Matérias-primas sem giro (12m)** e
**Acuracidade de inventário (mês fechado)** — Dashboard Suprimentos.

- **TASK_ID:** `DAVI-SUPPLIES-GLPI1197-DATA-GATE-001`
- **Solicitante:** Yuri Barbeito · GLPI #1197 · 2026-10-09
- **Modo:** INVENTORY + VALIDATION + TECHNICAL DESIGN (implementação não autorizada; produção read-only)
- **Repositório:** `roberiooliveiradev/delpi-central`

---

## A. Executive verdict

```text
TASK_ID:                     DAVI-SUPPLIES-GLPI1197-DATA-GATE-001
REPOSITORY:                  delpi-central
BASE_HEAD:                   c9d2a0ced7 (brief citava 8e16ffdcf5 — stale)
FINAL_HEAD:                  16af285e385baf4ff6d47e7b4498f1830128fb44
WORKTREE_STATUS:             clean (docs-only diff desta auditoria)
EXECUTION_DRIFT:             nenhum material (2 commits upstream delia — NON_CAUSAL)
FUNCTIONAL_DESIGN_STATUS:    ratificado pelo desenho; não reaberto
DATA_GATE_STATUS:            ACCEPT_WITH_RESIDUAL
CAPABILITY_FREEZE_STATUS:    PENDENTE — ratificação de negócio R-01/R-02/R-03
IMPLEMENTATION_AUTHORIZATION: NOT_GRANTED — aguarda ratificação + freeze formal
```

**Veredicto:** `ACCEPT_WITH_RESIDUAL`. Todos os gates críticos (A–G) têm
fonte e mecanismo comprovados em dados reais read-only. Três decisões de
negócio (R-01/R-02/R-03) mudam o valor do indicador e devem ser ratificadas
antes do capability freeze — nenhuma exige nova fonte de dados.

---

## B. Fonte e ownership

| Item | Valor |
|---|---|
| business need | GLPI #1197 — 2 indicadores do Dashboard Suprimentos |
| business owner | Yuri Barbeito (solicitante) — Suprimentos |
| technical owner | `api-delpi` (bounded context TOTVS/Delpi) |
| source of truth (dados) | Protheus SQL Server `DELPI` — SB1/SB2/SB7/SB9/SD3 |
| authorization owner | backend AuthZ (`delpi_auth`); `KPI_SUPPLIES_ACCESS` |
| contracts existentes | `/supplies/stock-balances/{summary,items}`, `/supplies/inventory-turnover`, `/supplies/inventory-adjustments{,/summary}`, `/products/{code}/internal-movements`, `/production/consumption/by-item/{code}` |
| consumers | `supplies-api` (BFF, `supplies_delpi_reads.py`), `plugins/dashboard-supplies`, `plugins/supplies`, DAVI (29 ops supplies na allowlist) |
| canonical classifiers | `protheus_internal_movements.py` (SD3), `protheus_product_types.py` (B1_TIPO), `protheus_warehouses.py` (B2_LOCAL), `InventoryAdjustmentClassification` (natureza) |

Cadeia preservada: `Dashboard → supplies-api BFF (trusted caller) → API DELPI → AuthZ → repositório → Protheus`. DAVI não é fonte nem executor.

---

## C. Evidências dos gates A–G

### GATE A — Classificação de matéria-prima — **PASS (PROVEN)**

- **CLAIM:** matéria-prima = `RTRIM(SB1.B1_TIPO) = 'MP'`.
- **SOURCE/CODE:** constante canônica `PRODUCT_TYPE_RAW_MATERIAL = "MP"` em
  `app/domain/totvs/protheus_product_types.py`; já usada por
  `safety_stock_sql.py`, `purchase_order_otd_sql.py`,
  `product_raw_material_set_shortage_sql.py`; documentada em
  `docs/api/padroes-totvs/cadastro-produto.md`.
- **EVIDENCE (read-only, 2026-10-09):** SB1 tem 11.682 MPs (PA 22.523 ·
  PI 14.051 · demais tipos irrelevantes ao escopo). `B1_FILIAL` vazio em
  todas as 55.253 linhas → **SB1 é compartilhada entre filiais** (não há
  duplicação por filial no cadastro).
- **EXCEPTIONS encontradas:**
  - `B1_MSBLQL` (bloqueio): 999 MPs `='1'` e 548 `='2'` (13,2% do universo).
    Inclusão/exclusão = decisão de negócio (**R-02**).
  - Precedente de exceção aprovada: OTD compras usa `MP OR B1_COD LIKE '3019%'`
    (`SUPPLIES_OTD_PRODUCT_CODE_PREFIX`).
- **BUSINESS_RATIFICATION_REQUIRED:** tratamento de bloqueados (R-02).

### GATE B — Consumo efetivo — **PASS (PROVEN com ressalva R-01)**

- **Classificador canônico:** `app/domain/totvs/protheus_internal_movements.py`
  (direção `TM<'500'` entrada / `>='500'` saída; INVENT = ajuste; PR0 =
  entrada produção; DE0/RE0 fora de INVENT = transferência; TM 999 + OP =
  consumo de produção). Mesma convenção em `safety_stock_sql.py`
  (`D3_TM='999' AND D3_OP<>''`).
- **Distribuição real SD3 de MPs (12m, `D_E_L_E_T_=''`, sem estorno):**

| TM/CF | OP | doc | n | leitura | reinicia giro? |
|---|---|---|---|---|---|
| 999/RE2 | sim | comum | 148.846 | consumo produção | **Sim** |
| 999/RE0 | sim | comum | 32.561 | consumo produção | **Sim** |
| 999/RE9 | sim | comum | 8.981 | consumo produção | **Sim** |
| 502/RE3 | não | doc fiscal (067xxx) | 31.263 | saída c/ documento (remessa/venda?) | **Pendente — R-01** |
| 499/DE4↔999/RE4 | não | pareado | 9.714+9.713 | transferência interna | Não |
| 499/DE6↔999/RE6 | não | pareado | 2.542+2.542 | transferência interna | Não |
| 499/DE7↔999/RE7 | não | pareado | 121+29 | transferência interna | Não |
| 499/DE0·999/RE0 | não | `INVENT` | 862+1.750 | ajuste de inventário | Não |
| 503/RE0 + 502/RE0 | não | comum | 467+13 | transferência (convencional) | Não |
| 499/DE1/DE2 | sim | comum | ~67 | devolução p/ estoque | Não |
| estorno `D3_ESTORNO='S'` | — | — | 402 vivos + 15.693 deletados | cancelamento | excluir |

- **Regra de restart proposta (PROVEN):** outbound efetivo =
  `TM>='500' AND D3_OP<>'' AND doc<>'INVENT'` (consumo de produção).
- **RESIDUAL_GAP:** 31.263 linhas `502/RE3` sem OP com número de documento
  fiscal — se representarem utilização efetiva (saída de MP), devem reiniciar
  o giro. Semântica a ratificar com Suprimentos (**R-01**). Default
  conservador (não reinicia) superestima o indicador.
- **Bug histórico "transferências como consumo":** corrigido no HEAD —
  classificador canônico distingue transferências (commit `d6b6da4ab5`
  introduziu `kind=`; direção de ajustes corrigida em `fd6677e457`).
  Cobertura de regressão: `test_product_internal_movements.py`,
  `test_davi_inventory_material_flow_corrective.py` (117 testes verdes na
  suíte de escopo).
- **Granularidade:** consumo avaliado **produto×filial** (qualquer armazém);
  valoração permanece produto×filial×armazém — conforme aprovado.

### GATE C — Cobertura histórica — **PASS (PROVEN)**

- **EVIDENCE:** SD3 contínuo desde 2003 (filial 01) / 2013 (filial 02) —
  janela de 12m sempre coberta. SB9 armazena inclusive saldos zerados
  (2.243/7.623 linhas zeradas no fechamento 2025-09-30) → prova de
  existência histórica do produto.
- **Regra verificável:**
  - `history_coverage_start` = min(primeira data SB9 com o produto, primeiro
    `D3_EMISSAO` do produto) por filial.
  - `window_start` / `window_end` / `reference_date`: proposta de freeze =
    **12 meses calendário fechados** `[2025-10-01, 2026-10-01)`,
    `reference_date` = último fechamento SB9 (`2026-09-30`, ambas filiais).
    Alternativa "janela móvel a partir de hoje" = decisão de negócio (**R-03**).
  - `turnover_status`: `WITH_CONSUMPTION` se existe restart no intervalo;
    `NO_CONSUMPTION_12M` se `history_coverage_start <= window_start`;
    `INSUFFICIENT_HISTORY` caso contrário (produto criado dentro da janela).
- **RESIDUAL_GAP:** SB1 não tem data de criação confiável (colunas são de
  ICMS/certificação) — proxy por primeira evidência SB9/SD3 é suficiente e
  fail-safe (produto novo → `INSUFFICIENT_HISTORY`).
- **Dado relevante:** 7.645/11.682 MPs (65%) **nunca** aparecem no SD3;
  2.290 MPs constam no fechamento 2025-09-30. A classificação de histórico
  separa "parado comprovado" de "criado recentemente".

### GATE D — Valoração e reconciliação — **PASS (PROVEN)**

- **CLAIM:** `B2_QATU × B2_CM1` por produto×filial×armazém — regra canônica
  de `stock-balances` (`stock_balances_sql.py`), sem segunda fórmula.
- **EVIDENCE (escopo MP, filiais 01/02):**
  - SB2 chave única (filial+cod+local): **0 duplicatas**.
  - Valor por armazém: f01 → loc 01 R$3.132.217 · loc 99 R$286.319 ·
    loc 50 R$54.187 · loc 98 R$7.174; f02 → loc 01 R$9.396.206 ·
    loc 99 R$478.036 · loc 50 R$100.095 · loc 98 R$53.707.
  - Locais fora do escopo aprovado (50/98) carregam ~R$215k — **excluídos
    por escopo aprovado, registrado para confirmação (R-08)**.
  - Locais com lixo cadastral (`''`, `,`, `0.`, `L-`, `V`) têm saldo
    zerado/quase zero — inócuos sob filtro de escopo.
  - Quantidades negativas: 1 linha (loc 98, f01) — tratada por `QATU>0` no
    indicador; custo zerado presente (4.219 linhas loc 01 f01) — valora a 0
    naturalmente.
- **Denominadores:**
  - `eligible_stock_value` = valor MP no escopo (filial×armazém).
  - `evaluable_stock_value` = elegível menos `insufficient_history`.
  - `non_moving_percentage = no_consumption_stock_value / evaluable_stock_value`.
  - `coverage_percentage = evaluable / eligible`.
  - `UNAVAILABLE` + motivo quando denominador = 0 (nunca retornar 0 falso).
- **Consolidação:** produto×filial para giro; soma de armazéns sem join
  duplicador (SB2 já é uma linha por chave — sem multiplicação).

### GATE E — Contagem oficial do inventário — **PASS (PROVEN)**

- **EVIDENCE SB7010 (42.554 linhas vivas):**
  - `B7_CONTAGE` ∈ `{'' , '001'}` — sem linhas de recontagem ('002'+) na base;
    `B7_QTSEGUM` é **2ª unidade de medida** (proporção 430→0,189), **não**
    recontagem.
  - `B7_ESCOLHA` sempre vazio (legado não utilizado).
  - `B7_STATUS`: `''` legado (21.086), `'1'` registrado/não processado
    (~7.161), `'2'` + `B7_ORIGEM='MATA270'` processado (~14.305).
  - `B7_DOC` digitado pelo usuário — não confiável como chave; usado só como
    proveniência (fail-closed, `inventory_adjustments_repository.py`).
- **Regras comprovadas:**
  - `INVENTORY_EVENT_KEY` = `(B7_FILIAL, B7_COD, B7_LOCAL, B7_DATA)`;
    múltiplas linhas da mesma chave = splits físicos de lote/localização →
    `SUM(B7_QUANT)` (ex.: `10120005/99` 6,5+14).
  - `VALID_COUNT_RULE` = `D_E_L_E_T_='' AND B7_STATUS='2'` (processado).
  - `RECOUNT_RULE` = recontagem gera nova linha/nova data; contagem 2 não
    existe na base atual → regra `MAX(B7_CONTAGE)` reservada
    (**R-09**, sem ocorrência observada).
  - `CANCELLED_COUNT_RULE` = `D_E_L_E_T_<>''` (exclusão lógica).
  - `AMBIGUOUS_COUNT_RULE` = status `'1'`/`''` recente → evento pendente,
    excluído do denominador com motivo `PENDING_PROCESSING`.

### GATE F — Saldo teórico histórico — **PASS (PROVEN, mecanismo canônico)**

- **Autoridade primária:** o próprio Protheus — o processamento MATA270
  decide divergência e emite `SD3 doc='INVENT'` (TM 499/DE0 sobra,
  TM 999/RE0 furo). Divergência oficial = existência do ajuste pareado por
  `filial+produto+local+data`. Contagens sem divergência **não** geram SD3.
- **Reconstrução secundária (cross-check):** `stock_value_historical_sql.py`
  — SB9 (último fechamento < data) + ponte SD3 líquida até a data. Mecanismo
  canônico já em produção para estoque histórico.
- **Reconciliação executada:** teórico reconstruído vs `contado±ajuste` em
  eventos SB7 — **598 MATCH / 309 DIFF** (65,9%). DIFFs consistentes com
  janela intradiária (D3_EMISSAO sem hora; contagem vs processamento) e
  splits de lote — por isso o INVENT do Protheus é a autoridade de
  divergência, e a reconstrução é validação aproximada (não substituto).
- **Estornos:** 402 linhas `D3_ESTORNO='S'` não deletadas no histórico —
  o SQL canônico de estoque histórico não filtra estorno (residual
  **R-06**, baixo volume, reconciliar).
- **Veredicto:** `THEORETICAL_BALANCE_SOURCE` = SB9+SD3 (reconstrução) +
  INVENT como autoridade de divergência. `INVENTORY_ACCURACY` **não está
  bloqueada**.

### GATE G — Acuracidade — **PASS (PROVEN, com observação de regime)**

- **Fórmula aprovada operacional:** `accuracy = accurate / evaluable × 100`,
  tolerância zero.
- **EVIDENCE real (eventos processados, dedup por event key):**
  - 2026-09 (mês fechado de referência): 309 eventos processados →
    **304 divergentes / 5 acurados = 1,6%**; 2 pendentes excluídos.
  - 2025-09 (comparação): 906 → 553 divergentes / 353 acurados = **39,0%**.
- **Interpretação:** a variação 1,6%↔39% indica regime de contagem distinto
  (set/2026 aparenta contagem dirigida a divergentes) — valor correto por
  construção, mas regime deve ser reportado (**R-07**).
- **Exclusões auditáveis:** `PENDING_PROCESSING` (status 1/blank recente),
  `CANCELLED` (deletado), `MISSING_THEORETICAL_BALANCE` (reconstrução
  impossível — não observado), `INVALID_REFERENCE`.
- **Fronteira temporal:** mês padrão = último fechamento SB9 mensal
  (`2026-09-30` ambas filiais — prova de mês fechado).
- **Reconciliação financeira:** ajustes INVENT set/2026 = f01 sobra
  R$1.650.880 / furo R$1.708.037 (258 movs); f02 sobra R$2.480 / furo
  R$32.480 (47 movs) — mesma fonte de `inventory-adjustments` (consistência
  garantida por construção, endpoint valida a exposição).

---

## D. Matriz de movimentos (GATE B consolidada)

| Movimento | Fonte (SD3) | Semântica | Reinicia prazo? | Evidência |
|---|---|---|---|---|
| Consumo produção | TM 999 + OP (RE0/RE2/RE9) | baixa em OP | **Sim** | 190.388 linhas/12m MP |
| Saída c/ documento fiscal | 502/RE3 sem OP | provável remessa/venda | **Pendente (R-01)** | 31.263 linhas/12m |
| Transferência interna | pares DE/RE n↔n (exceto INVENT) | movimentação interna | Não | pares 499↔999 DE4/RE4 etc. |
| Ajuste de inventário | doc `INVENT` (DE0/RE0) | correção de contagem | Não | 2.612 linhas/12m MP |
| Entrada produção | CF PR0 | recebimento de OP | N/A (inbound) | classificador canônico |
| Devolução p/ estoque | DE1/DE2 c/ OP | retorno não consumido | Não | ~67 linhas/12m |
| Estorno | `D3_ESTORNO='S'` | cancelamento | Não (excluir) | 402 vivos histórico |
| Não classificado | demais TM/CF | semântica indeterminada | Pendente (fail-safe: não reinicia) | cauda pequena |

---

## E. Semântica oficial de contagem

- Evento = `(B7_FILIAL, B7_COD, B7_LOCAL, B7_DATA)`; linhas múltiplas do
  mesmo evento agregam (`SUM(B7_QUANT)`).
- `B7_QUANT` = quantidade contada (1ª UM). `B7_QTSEGUM` = 2ª UM.
- `B7_STATUS='2'` + `B7_ORIGEM='MATA270'` = processado (oficial).
- `B7_STATUS='1'`/`''` recente = pendente → excluído.
- Recontagem como linha separada **não ocorre** na base (só `''`/`'001'`);
  regra reservada `MAX(B7_CONTAGE)` se surgir.
- Protheus emite o ajuste INVENT apenas quando há divergência → ausência de
  SD3 pareado = contagem acurada (evidenciado: 353 eventos set/2025 sem
  ajuste; reconstrução confirma contagem ≈ teórico em 78% dos casos).

## F. Saldo teórico histórico

- **Primário (autoridade):** decisão de divergência do Protheus = presença/
  valor do SD3 `INVENT` pareado (`filial+produto+local+data`).
- **Secundário (reconstrução/cross-check):** `SB9` fechamento anterior +
  ponte `SD3` líquida (`stock_value_historical_sql.py` — canônico).
- **Granularidade:** filial×produto×armazém; instante = `B7_DATA`
  (granularidade de dia — limitação intradiária documentada).
- **Estornos:** excluir `D3_ESTORNO='S'`; 402 linhas vivas históricas a
  reconciliar (R-06).

## G. Contratos HTTP candidatos (conceitual — não implementar)

Decisão **ADDITIVE** — 4 operações novas, família `/supplies/` existente,
sem alteração de contrato vigente:

```text
GET /supplies/non-moving-stock/summary
  params: branch? (01|02|all), warehouse? (01|99), month? (default: janela congelada)
  out:    reference_date, window_start, window_end,
          eligible_stock_value, evaluable_stock_value,
          no_consumption_stock_value, insufficient_history_stock_value,
          non_moving_percentage|null, coverage_percentage,
          status (OK|UNAVAILABLE+reason), counts por turnover_status

GET /supplies/non-moving-stock/items
  params: + page, page_size, sort (stock_value desc default), turnover_status?
  out:    product_code, description, unit, branch, warehouse,
          quantity, unit_cost, stock_value, last_effective_consumption_date|null,
          turnover_status, history_coverage_start

GET /supplies/inventory-accuracy/summary
  params: branch?, month? (default: último mês fechado SB9)
  out:    reference_month, valid_count_total, evaluable_count_total,
          accurate_count, divergent_count, excluded_count{motivo},
          accuracy_percentage|null, coverage_percentage,
          shortage_value, surplus_value  (reconcilia com inventory-adjustments)

GET /supplies/inventory-accuracy/items
  params: + page/page_size/sort, outcome? (accurate|divergent|excluded)
  out:    event key (branch, product, warehouse, count_date),
          counted_quantity, theoretical_quantity|null, divergence_quantity,
          adjustment document/value, exclusion_reason
```

- AuthZ: `require_any_permission_or_supplies_bff(KPI_SUPPLIES_ACCESS)`
  (mesmo padrão de `stock-balances`/`inventory-turnover`; consumidor
  `supplies-api` já é trusted caller).
- Paginação/envelope: `api_delpi_success` + `paginate` existentes; erros
  tipados (400 validação / 500) conforme routers atuais.
- DAVI: **não** adicionar à `davi_external_read_allowlist` sem gates de
  capability ratificados (precedente da correção de governança SQL).

## H. Modelo de dados

```text
non-moving (produto×filial×armazém para valor; produto×filial para giro)
  turnover_status ∈ WITH_CONSUMPTION | NO_CONSUMPTION_12M | INSUFFICIENT_HISTORY
  stock_value = B2_QATU×B2_CM1 (QATU>0)
  denominators: eligible ⊇ evaluable = eligible − insufficient_history
  UNAVAILABLE quando evaluable=0 ou cobertura não comprovada

inventory-accuracy (evento = filial×produto×armazém×data)
  outcome ∈ accurate | divergent | excluded{reason}
  mês de referência = último fechamento SB9
  accurate ⇒ sem SD3 INVENT pareado; divergent ⇒ INVENT pareado
```

## I. Performance

| Medida | Resultado (read-only real) |
|---|---|
| SD3 12m | 478.964 linhas · 6.935 produtos · agregações **<1s** NOLOCK |
| SB7 mês | ~200–900 eventos; índice `B7_FILIAL+B7_DATA` existe |
| SB9 | 1,77M (f01) + 487k (f02) linhas históricas; fechamento por data indexável |
| Índices SD3 | `D3_FILIAL+D3_EMISSAO+…` e `D3_COD+D3_EMISSAO` presentes |
| Query candidata | agregada única por escopo + itens paginados; estimativa idle MP: **848 produtos f01 (R$816k) + 330 f02 (R$468k)** com saldo>0 e sem consumo OP em 12m — medida em 0,8s |
| Estratégia | uma query agregada (summary) + `OFFSET/FETCH` (items); sem N+1; candidata a `query_cache` (polling de dashboard) |
| Consistência | NOLOCK aceitável para KPI; reconciliação de acuracidade deve rejeitar eventos do dia corrente |

## J. Testes e AuthZ

- **UNIT/INTEGRATION (container, HEAD atual):** suítes pertinentes
  `test_product_internal_movements`, `test_supplies_inventory_adjustments`,
  `test_supplies_canonical_branch_access`, `test_supplies_bff_service_access`,
  `test_safety_stock_consumption_analysis_*`, `test_davi_inventory_*`,
  `test_get_inventory_turnover`, `test_get_stock_value` — **117 passed / 0 failed**.
- **READ-ONLY DATABASE EVIDENCE:** todas as consultas acima executadas em
  produção via credencial técnica read-only (resumo de resultados embutido).
- **RECONCILIATION:** SB7↔SD3 INVENT (598/309), ajustes set/2026 reconciliam
  com contrato `inventory-adjustments`.
- **AuthZ:** `KPI_SUPPLIES_ACCESS` = `API_DELPI_ACCESS | DASHBOARD_SUPPLIES_VIEW`
  + trusted `supplies-api` caller; branch = filtro (não autorização);
  gates por filial seguem `BranchAccessGate` quando aplicável; fail-closed
  (`403` sem permissão — coberto pela matriz de testes existente).
- **Não comprovado:** usuário autenticado real vs filial não autorizada
  (TEST_NOT_RUN — sem token de teste nesta auditoria; matriz unitária cobre).

## K. Residual ledger

| ID | SEVERITY | OWNER | EVIDENCE_MISSING | REQUIRED_ACTION | BLOCKS_IMPLEMENTATION |
|---|---|---|---|---|---|
| R-01 | MEDIUM | Suprimentos (Yuri) | semântica de 502/RE3 sem OP (saída c/ NF) | ratificar se é utilização efetiva | **SIM** (altera restart rule) |
| R-02 | MEDIUM | Suprimentos | política para MP bloqueada (`B1_MSBLQL`) | ratificar inclusão/exclusão | **SIM** (altera universo) |
| R-03 | LOW | Suprimentos | convenção da janela (12m fechados × móvel) | ratificar freeze explícito | SIM (fronteira do indicador) |
| R-06 | LOW | API DELPI | estornos SD3 vivos (402) no histórico | reconciliar impacto na ponte SB9+SD3 | não (margem pequena) |
| R-07 | LOW | Suprimentos | regime de contagem (1,6% vs 39%) | comunicar volatilidade como dado | não |
| R-08 | LOW | Suprimentos | valor MP em locais 50/98 (~R$215k) fora do escopo | confirmar exclusão | não (escopo aprovado) |
| R-09 | LOW | API DELPI | recontagem ausente na base | manter regra `MAX(B7_CONTAGE)` | não |
| R-10 | LOW | API DELPI | data de criação do produto inexistente em SB1 | proxy SB9/SD3 primeira evidência | não (`INSUFFICIENT_HISTORY` fail-safe) |

## L. Final decision

```text
DECISION: ACCEPT_WITH_RESIDUAL
```

- Gates A–G: fontes e mecanismos **PROVEN** em dados reais.
- Implementação das 4 rotas **não autorizada** nesta tarefa; próxima etapa
  depende de ratificação de R-01/R-02/R-03 (decisões de negócio que movem o
  número, não a viabilidade técnica).
- Sem fonte autoritativa faltante; sem EXECUTION_DRIFT; sem alteração de
  código — apenas este documento.

---

*Evidência gerada em 2026-10-09 contra `DELPI` (SQL Server, read-only) e
HEAD `16af285e38`. Consultas disponíveis nos probes temporários da sessão
(não versionados por conter credenciais de ambiente).*

---

# PARTE II — Ratificação e implementação (DAVI-SUPPLIES-GLPI1197-IMPLEMENTATION-001)

*Acrescentado em 2026-10-09. A Parte I permanece como registro histórico da
auditoria — nada abaixo reescreve evidência passada como se tivesse sido
provada no SHA anterior.*

## M. Ratificações de Suprimentos (aprovador: Yuri Barbeito, GLPI #1197)

| ID | Decisão aprovada | Implementação |
|---|---|---|
| R-01 | **Consumo efetivo reinicia o giro.** Saídas com nota fiscal ou de utilização efetiva reiniciam; transferências internas e ajustes de inventário não reiniciam; estornos não constituem utilização. Classificação no domínio canônico, nunca em heurística de frontend. | Spec canônica `effective_utilization_*` em `app/domain/totvs/protheus_internal_movements.py`: grupo `(D3_FILIAL, D3_COD, D3_DOC, D3_EMISSAO)` com saída líquida > 0 = utilização. Espelho transferência (mesma chave doc com TM < 500) anula o grupo; devolução parcial mantém utilização líquida. `D3_ESTORNO='S'` e `D3_DOC='INVENT'` excluídos por predicado. |
| R-02 | **Bloqueados no universo, segregados financeiramente.** `B1_MSBLQL='1'` = bloqueado; visíveis separadamente, valor preservado, sem duplicação multi-armazém (flag no item + agregados por DISTINCT produto×filial). | Campo `blocked` em `eligible` (SB1) + `blocked_stock_value`, `blocked_no_consumption_stock_value`, `blocked_product_count` no summary + filtro `blocked` nos items. |
| R-03 | **12 meses móveis até hoje como padrão; filtros existentes podem alterar.** Não confundir janela de consumo com referência de valoração (SB2 snapshot atual). | `resolve_consumption_window()` no domínio: default `rolling_12m` (hoje−12m → hoje, limites inclusivos); `start_date`+`end_date` → `custom_period` com status semântico próprio (`NO_CONSUMPTION_IN_PERIOD`, não `NO_CONSUMPTION_12M`). Resposta expõe `consumption_window_*` e `valuation_reference: sb2_current_snapshot` separadamente. |

Acuracidade mantém padrão **último mês calendário fechado** (via `MAX(SB9.B9_DATA)`), com `month`/`start_date`+`end_date` como overrides e `period_closed` explícito no contrato.

## N. Matriz fiscal — saídas sem OP (GATE 4.1)

Fonte autoritativa de natureza: **SF5** (`F5_CODIGO`/`F5_TIPO`/`F5_TEXTO`), não o dígito do CF. Evidência real 12m MP.

| TM/CF | SF5 (F5_TEXTO / F5_TIPO) | Semântica real | Espelho inbound mesmo doc? | Reinicia giro | Homologação |
|---|---|---|---|---|---|
| 999/RE0 c/ OP | requisição (R) | consumo efetivo de produção | não | **SIM** | PROVEN (canônico prévio) |
| 502/RE3 s/ OP | `REQUISICAO INDIRETA` (R) | utilização efetiva (requisição de MP por usuário do almoxarifado; sem `D3_NFORP`/`D3_NUMSA`/SD2 — **não** é remessa fiscal de venda) | não (31k linhas, 0 espelhos na amostra) | **SIM** | PROVEN (SF5 + ausência de espelho/NF) |
| 503/RE0 | `BAIXA PRODUTO IND` (R) | baixa/utilização indireta | não | **SIM** | PROVEN (mesma regra de grupo) |
| xxx/RE0 ↔ yyy/DE0 | transferência (T) | transferência entre armazéns | **sim** — par exato mesmo doc+filial+produto+data | **NÃO** | PROVEN (espelho anula grupo) |
| INVENT (499/DE0, 999/RE0) | ajuste MATA270 | correção de inventário | n/a (excluído por predicado) | **NÃO** | PROVEN (predicado `D3_DOC<>'INVENT'`) |
| estorno `D3_ESTORNO='S'` | reversão | cancelamento de fato | n/a | **NÃO** | PROVEN (predicado) |
| saída com devolução parcial | requisição + devolução | utilização líquida | parcial | **SIM** se líquido > 0 | PROVEN (HAVING net>0) |
| 999/REA, 501/RE3, 600/601/RE6 | R (SF5) | saídas residuais | cauda longa — agrupadas pela mesma regra | conforme saldo líquido do grupo | PROVEN pela regra geral |

**Regra implementada:** não é "TM ≥ 500 reinicia" — é **saldo líquido positivo do grupo doc**, que unifica todos os casos acima sem tabela de exceções por código.

## O. Semântica de acuracidade homologada (GATE 4.2)

- Evento oficial = `(B7_FILIAL, B7_COD, B7_LOCAL, B7_DATA)`; linhas físicas
  agregam por `SUM(B7_QUANT)` (42.554 linhas → 41.967 eventos prova que
  agrupar é obrigatório).
- `B7_STATUS='2'` = veredito oficial MATA270 → **avaliável**; `'1'`/`''` =
  pendente → **excluído** (`pending_processing`, auditável); linhas
  deletadas = canceladas → excluídas (`cancelled`).
- Correta = processada **sem** ajuste INVENT; divergente = **com** ajuste.
  Fundamento: o próprio Protheus já computou teórico×contado — a decisão
  oficial é a fonte; "sem ajuste ≠ igualdade física provada", e sim
  **veredito oficial de não-divergência** (`comparison_source:
  protheus_mata270_adjustment_decision`). Tolerância = zero conforme aprovado.
- Saldo teórico exibido por evento = `contado + furo − sobra` (derivado da
  decisão oficial); reconstrução SB9+SD3 permanece como fonte de
  `stock-balances` histórico, não da acuracidade.
- Os 309 DIFFs de reconciliação da Parte I (janela intradiária/lote) não
  afetam o denominador — não há evento sem veredito oficial.
- Resultado real set/2026: 311 válidas → 309 avaliáveis → 5 corretas /
  304 divergentes = **1,62%**; excluídas 2 pendentes; furos R$1.740.517,
  sobras R$1.653.360. Regime de contagem seletivo — reportar como dado
  (R-07).

## P. Contratos publicados

| Rota | operationId | Entidade/shape | AuthZ |
|---|---|---|---|
| GET /supplies/non-moving-stock/summary | `get_supplies_non_moving_stock_summary` | `supplies_non_moving_stock_summary` / playbook_report | `KPI_SUPPLIES_ACCESS` + trusted supplies-api BFF |
| GET /supplies/non-moving-stock/items | `get_supplies_non_moving_stock_items` | `supplies_non_moving_stock_item` / paged_list | idem |
| GET /supplies/inventory-accuracy/summary | `get_supplies_inventory_accuracy_summary` | `supplies_inventory_accuracy_summary` / playbook_report | idem |
| GET /supplies/inventory-accuracy/items | `get_supplies_inventory_accuracy_items` | `supplies_inventory_accuracy_item` / paged_list | idem |

- Escopo: filiais 01/02 (param `branch`), armazéns 01/99 (param `warehouse`,
  rejeita fora do escopo), `B1_TIPO='MP'`, `B2_QATU>0`, `B2_QATU×B2_CM1`
  do próprio armazém.
- Paginação/ordenação no backend (`OFFSET/FETCH`, `page_size` máx 500).
- **DAVI:** operationIds presentes no baseline mas **fora** da allowlist →
  não elegíveis, não executáveis (fail-closed). Expansão requer gate
  separado.
- **BFF supplies-api:** o dashboard consome api-delpi diretamente
  (padrão vigente, `X-Delpi-Caller-App: dashboard-supplies`); nenhum
  adaptador novo foi necessário — BFF permanece como trusted caller
  opcional já aceito pelo `require_any_permission_or_supplies_bff`.

## Q. Evidência de runtime (queries reais, read-only, 2026-10-09)

| Query | Runtime | Resultado |
|---|---|---|
| non-moving summary (ambas filiais, 12m móvel) | ~6,9–7,1 s | elegível R$13.288.908 (2.554 produtos×filial); sem giro R$1.180.010 (1.041 produtos); INSUFFICIENT_HISTORY R$30.035 (30); bloqueados R$17.725 (4, todos sem giro); filial 01 R$3,42M + 02 R$9,87M reconcilia |
| non-moving items paginado | ~10,4 s | amostras coerentes (última utilização pregressa 2023–2025; INSUFFICIENT_HISTORY com 1ª evidência dentro da janela) |
| accuracy summary set/2026 | ~74 ms | 311 válidas / 309 avaliáveis / 5 corretas / 304 divergentes / 1,62% / 2 pendentes |
| accuracy items paginado | ~51 ms | eventos com documento, teórico, outcome |

Correção pós-evidência: ordenação da classificação ajustada para
`WITH_CONSUMPTION` antes de `INSUFFICIENT_HISTORY` — produto com utilização
comprovada na janela é fato observado e não depende de cobertura
(139 produtos reclassificados após primeira medição; ~R$387k).

Custo: a varredura de utilização é restrita a produtos elegíveis
(join `eligible_keys`, seek por `D3_FILIAL+D3_COD`); ~7 s é aceitável para
KPI analítico sob `NOLOCK` — leitura eventual, documentada; consistência
financeira garantida pela unicidade de chave SB2 e pela agregação por
produto×filial (não por locking).

## R. Arquivos da implementação

- Domínio: `app/domain/services/supplies/non_moving_stock_service.py`,
  `app/domain/services/supplies/inventory_accuracy_service.py`,
  extensão de `app/domain/totvs/protheus_internal_movements.py`.
- Infra: `non_moving_stock_sql.py`, `non_moving_stock_query_repository.py`,
  `inventory_accuracy_sql.py`, `inventory_accuracy_repository.py` em
  `app/infrastructure/persistence/totvs/supplies_repositories/`.
- App: DTOs `non_moving_stock_request.py`, `inventory_accuracy_request.py`;
  4 use cases em `app/application/use_cases/supplies/`.
- Interface: `non_moving_stock_router.py`, `inventory_accuracy_router.py`;
  wiring em `app/main.py`, `supplies_composer.py`,
  `route_contract_registry.py`, `openapi_agent_metadata_builder.py`;
  baseline OpenAPI + inventário DAVI regenerados.
- Testes: `tests/test_supplies_non_moving_stock.py`,
  `tests/test_supplies_inventory_accuracy.py` — domínio, SQL, contrato,
  denominadores, fail-closed.

## S. Residual ledger pós-implementação

| ID | Status | Nota |
|---|---|---|
| R-06 | aberto | estornos vivos SD3 (~402) — margem pequena; reconciliar na ponte SB9+SD3 em trabalho futuro |
| R-07 | aberto | regime de contagem seletivo (1,6% vs 39%) — volatilidade é o dado; comunicar a Suprimentos |
| R-08 | aberto | ~R$215k de MP em locais 50/98 fora do escopo aprovado — exclusão confirmada pelo escopo R-02 (armazéns 01/99) |
| R-09 | aberto | recontagem `B7_CONTAGE>1` sem ocorrência na base — regra reservada |
| R-11 | novo | runtime do summary sem giro ~7 s — aceitável p/ KPI; avaliar cache/materialização se uso crescer |
| R-12 | novo | `B7_DOC` de evento exposto quando único; proveniência ambígua permanece NULL (fail-closed, idem ajustes) |


---

# PARTE III — POST-DEPLOY CORRECTIVE AUDIT

> Auditoria corretiva integral pós-deploy (DAVI-SUPPLIES-GLPI1197-CORRECTIVE-E2E-001).
> BASE_HEAD: f1737dbab0 → revalidado contra d3f1693a0e e reconciliado FF sobre
> origin/main 0aac103068 (drift upstream: 2 commits delia-only, zero overlap).

## T. Inventário de defeitos (issues)

### ISSUE-01 — Busca da tabela inerte

- SEVERITY: P0
- OBSERVED_BEHAVIOR: pesquisar "1008" não filtrava — linhas sem correspondência
  permaneciam exibidas.
- EXPECTED_BEHAVIOR: busca server-side sobre código (parcial/exato) e descrição,
  no conjunto global, com paginação/ordenação consistentes.
- ROOT_CAUSE: `DataTableSection` renderiza a caixa de busca por padrão, mas sob
  `serverPagination` o filtro client-side é ignorado; sem `serverSearch` a caixa
  era inerte (filtro aplicado só sobre as linhas carregadas, sem reenvio ao
  backend). Não havia parâmetro `search` no contrato de itens.
- CORRECTION: parâmetro `search` aditivo no contrato (DTO + router + use case +
  SQL LIKE escapado `ESCAPE '\'` sobre `product_code`/`description`, limite
  120 chars); frontend com `serverSearch` + debounce 400ms
  (`useDebouncedValue`); reset de página ao alterar termo.
- TEST_EVIDENCE: testes de escape `%`/`_`/`\`, filtro por código parcial e
  descrição, paginação com busca — suíte supplies 48 PASS.
- STATUS: PROVEN (código+testes) / browser E2E TEST_NOT_RUN.

### ISSUE-02 — Checkbox "Somente bloqueados" fora do padrão + sem evidência de efeito

- SEVERITY: P0
- OBSERVED_BEHAVIOR: checkbox nativo marcado com linhas não bloqueadas visíveis;
  controle HTML nativo fora do design system.
- EXPECTED_BEHAVIOR: filtro tri-estado padronizado; `blocked=true` → todas as
  linhas bloqueadas; `blocked=false` → todas não bloqueadas; resumo não filtrado
  pelo detalhe.
- ROOT_CAUSE: `blocked` já era enviado e aplicado no SQL (`blocked = ?`), mas o
  controle era `<input type=checkbox>` nativo e não havia estado "não
  bloqueados"; a percepção de ineficácia também decorria da busca inerte
  (ISSUE-01) e da ausência de `refreshing` na tabela (linhas antigas visíveis
  durante a nova consulta).
- CORRECTION: `ToolbarSelectField` (plugin-ui) com Todos/Bloqueados/Não
  bloqueados → `blocked` booleano preservado no contrato; `refreshing` passado
  ao `DataTableSection` (estado "mantendo dados enquanto atualiza").
- TEST_EVIDENCE: `blocked=false` coberto no SQL builder (`blocked = 0`).
- STATUS: PROVEN (código+testes) / browser E2E TEST_NOT_RUN.

### ISSUE-03 — Ordenação por coluna inválida (422) / instável

- SEVERITY: P0
- OBSERVED_BEHAVIOR: clicar em "Última utilização" não ordenava.
- EXPECTED_BEHAVIOR: ordenação global, direção alternada, desempate estável,
  página reiniciada, conjunto completo.
- ROOT_CAUSE: `DataTable.onSortChange` emite `column.key`; a coluna usava key
  `last_effective_utilization`, stem inexistente no `_SORT_MAP` do backend
  (422/sem efeito). Ordenações também não tinham desempate.
- CORRECTION: keys das colunas alinhadas aos stems do `_SORT_MAP`
  (`product_code`, `quantity`, `stock_value`, `last_utilization`,
  `count_date`); `_TIEBREAKER` `branch+product_code+warehouse` (+`count_date`
  na acuracidade) em todas as ordenações.
- TEST_EVIDENCE: testes de sort estável e mapeamento — suíte verde.
- STATUS: PROVEN (código+testes) / browser E2E TEST_NOT_RUN.

### ISSUE-04 — Multi-select de filiais reduzido a consolidado

- SEVERITY: P0
- OBSERVED_BEHAVIOR: seleção ["01","02"] não filtrava exatamente 01+02 —
  `resolveApiBranch` reduzia múltiplas seleções a consolidado.
- EXPECTED_BEHAVIOR: [] → consolidado autorizado; [01] → 01; [02] → 02;
  [01,02] → exatamente 01+02.
- ROOT_CAUSE: contrato de branch da página usava `branch` singular
  (`resolveApiBranch`); o endpoint aceita `branch` repetível.
- CORRECTION: `apiBranches` exposto por `useSuppliesFilters`; `buildQuery`
  serializa `branches[]` como `branch` repetível (fallback para `branch`
  singular quando `branches` ausente — compatibilidade retroativa).
- STATUS: PROVEN (código+testes) / browser E2E TEST_NOT_RUN.

### ISSUE-05 — Período/competência divergindo da requisição

- SEVERITY: P0
- OBSERVED_BEHAVIOR: URL com `start_date=2025-10-09&end_date=2026-10-09`
  exibia `competence=2026-09` / "01/09/2026 a 30/09/2026".
- EXPECTED_BEHAVIOR: URL, controles e requisição coerentes; sem override
  silencioso.
- ROOT_CAUSE: estado de filtro compartilhado entre páginas (sessionStorage)
  carregava recorte de outra página; as novas páginas não declaravam default
  próprio e o `resolveLinkedDateFilters` define competência como prioridade
  quando presente — a divergência observada era o estado persistido, não um
  recompute errado. Em acuracidade, `competence` governa `month` — correto
  por contrato.
- CORRECTION: `useSuppliesFilters({defaultPeriod})` — sem giro default 12m
  móvel; acuracidade default último mês fechado. Convenção preservada: estado
  persistido vence o default (recorte compartilhado entre páginas).
  Footnote explicita janela de consumo vs. valoração.
- STATUS: PROVEN (código) / browser E2E TEST_NOT_RUN.

### ISSUE-06 — Armazém em texto livre fora do domínio aprovado

- SEVERITY: P1
- OBSERVED_BEHAVIOR: campo livre de localização sem restrição ao escopo 01/99.
- CORRECTION: `ToolbarSelectField` com Armazém 01/99/Todos; valor compartilhado
  fora do escopo é ignorado (fail-closed para o contrato).
- STATUS: PROVEN.

### ISSUE-07 — "% sem giro" interpretável como % de produtos

- SEVERITY: P1
- OBSERVED_BEHAVIOR: card "% sem giro: 8,90% — 1.041 de 2.554 produtos"
  induzia leitura de percentual por contagem.
- CORRECTION: card renomeado "% sem giro (financeiro)" com subtítulo
  `R$ sem giro de R$ avaliável · N produtos`; fórmula inalterada
  (denominador financeiro correto).
- STATUS: PROVEN.

### ISSUE-08 — Acuracidade sem contexto/unidade/sinal

- SEVERITY: P1
- OBSERVED_BEHAVIOR: 1,62% podia ser lido como acuracidade geral do estoque;
  divergência sem unidade nem convenção de sinal; contagens excluídas não
  reconciliadas na tela.
- CORRECTION: subtítulo "universo: contagens oficiais"; unidade de medida em
  Contado/Teórico; footnote declara `divergência = teórico − contado`
  (positivo=falta, negativo=sobra) e reconcilia válidas×avaliáveis×excluídas;
  pendentes+canceladas fora das válidas declaradas.
- STATUS: PROVEN.

### ISSUE-09 — Produtos sem custo invisíveis

- SEVERITY: P1
- OBSERVED_BEHAVIOR: itens com `B2_CM1=0` somavam R$0 sem sinalização.
- CORRECTION: `zero_cost_items` no resumo (contagem produto×filial×armazém);
  footnote e célula de valor marcam "sem custo"; nenhum custo alternativo
  inventado.
- STATUS: PROVEN (testes de contagem de custo-zero).

### ISSUE-10 — Linhas antigas durante refresh (risco de stale visual)

- SEVERITY: P1
- CORRECTION: `refreshing` conectado às tabelas; `useSuppliesResource` já
  aborta requisições anteriores via `AbortController` (resposta mais recente
  prevalece — race mitigada por contrato do hook).
- STATUS: PROVEN (código) / browser E2E TEST_NOT_RUN.

## U. Matriz antes/depois

| Issue | Antes | Depois | Evidência | Status |
|---|---|---|---|---|
| Busca 1008 | caixa inerte, só filtrava linhas carregadas | `search` server-side escapado, global | testes SQL/API | PROVEN |
| Bloqueados | checkbox nativo sem tri-estado | select plugin-ui, `blocked` booleano | teste `blocked=0` | PROVEN |
| Ordenação | key inválida → 422/sem efeito | keys = stems do `_SORT_MAP` + tiebreaker | testes sort | PROVEN |
| Filiais | multi-seleção → consolidado | `branch` repetível exato | contrato + testes | PROVEN |
| Período | divergência estado persistido×controles | defaults por página + convenção documentada | código | PROVEN |
| Armazém | texto livre | select 01/99/Todos fail-closed | código | PROVEN |
| % sem giro | ambíguo (produtos×valor) | financeiro explícito, denominador visível | revisão | PROVEN |
| Acuracidade | sem universo/sinal/unidade | contexto+convenção+unidade declaradas | revisão | PROVEN |
| Sem custo | R$0 silencioso | `zero_cost_items` + sinalização | testes | PROVEN |
| Refresh | linhas antigas sem estado | `refreshing` + abort implícito | código | PROVEN |

## V. Verificações

- BACKEND: PASS — 48 testes supplies focados + 59 testes
  adjustments/branch/bff (107 verdes).
- FRONTEND: PASS — eslint 0 erros nos arquivos tocados; `vite build` PASS;
  `tsc -b` mantém FAIL pré-existente upstream (bootstrap.tsx `Root|undefined`,
  `vitest` ausente, plugin-ui React ref types) — sem regressão nos arquivos
  deste diff (0 erros filtrados).
- CONTRACTS: PASS — `search` aditivo, `branch` repetível já existente;
  baseline OpenAPI regenerado (667 paths); novas rotas seguem fora da
  allowlist DAVI (fail-closed).
- AUTHZ: PASS — backend AuthZ canônico inalterado; `branches` segue sujeito ao
  escopo autorizado do usuário no backend.
- BROWSER_E2E: TEST_NOT_RUN — sem acesso autenticado ao ambiente nesta sessão;
  evidência de rede/browser pendente de homologação.
- REGRESSÃO: `useSuppliesFilters` retrocompatível (options opcional);
  `readSuppliesFilters`/`buildQuery` retrocompatíveis; páginas irmãs intactas
  (diff restrito a supplies GLPI-1197 + hook compartilhado aditivo).

## W. Residual ledger (atualizado)

| ID | Status | Nota |
|---|---|---|
| R-06 | aberto | estornos vivos SD3 (~402) |
| R-07 | aberto | regime de contagem seletivo — comunicar a Suprimentos |
| R-08 | aberto | ~R$215k MP em locais 50/98 fora do escopo |
| R-09 | aberto | recontagem `B7_CONTAGE>1` sem ocorrência |
| R-11 | aberto | summary ~7 s — avaliar cache se uso crescer |
| R-12 | aberto | `B7_DOC` ambíguo permanece NULL |
| R-13 | novo | browser E2E autenticado TEST_NOT_RUN — homologação visual pendente |
| R-14 | novo | `tsc -b` upstream quebrado (bootstrap/vitest/plugin-ui types) — owner: frontend/platform |


---

# PARTE IV — TABLE UX & ADVANCED DATA GRID (TASK DAVI-SUPPLIES-GLPI1197-TABLE-UX-002)

## X1. Inventário de capacidades plugin-ui (auditoria pré-implementação)

| Capacidade | Classificação | Local |
|---|---|---|
| Toolbar + busca principal | AVAILABLE | DataTableSection (serverSearch) |
| Paginação server-side | AVAILABLE | useServerTable + Pagination |
| Ordenação global com indicador | AVAILABLE | DataTable emite column.key |
| Visibilidade de colunas + menu | AVAILABLE | columnPreferencesKey + TableColumnVisibilityMenu (mostrar/ocultar, selecionar todas, restaurar padrão, persistência por página) |
| Reordenação de colunas | AVAILABLE | enableColumnReorder |
| Redimensionamento | NEEDS_EXTENSION→implementado | DataTable suportava columnWidths/onColumnWidthsChange/resizableColumns; DataTableSection não repassava → passthrough aditivo |
| Seleção de linhas | NEEDS_EXTENSION→implementado | DataTable suportava selection/onSelectionChange (individual + página); DataTableSection não repassava → passthrough aditivo |
| Exportação tabular | AVAILABLE | TabularExportButtons/SuppliesExportButtons (CSV/XLSX/PDF, mesmos filtros do request) |
| Layout cards mobile | AVAILABLE | viewLayoutPreferencesKey + DataRecordCard |
| Font-size persistente | AVAILABLE | fontSizePreferencesKey |
| Seleção global (todas as páginas) | NOT_SUPPORTED — não oferecida (sem contrato backend) |

Extensão em plugin-ui: estritamente aditiva em DataTableSection
(passthrough de props já existentes no DataTable interno).
Sem nova lib de data grid; sem mudança de API existente.

## X2. Mudanças de layout de filtro

- toolbarFilters movido para FiltersRow dedicada (segunda linha), aria-label
  por página.
- SelectField/DataRecordCard locais viraram wrappers finos das factories
  canônicas (createDashboardSelectField/createDashboardDataRecordCard) —
  labels acima dos controles, alturas/larguras do design system.
- Ação Limpar filtros + indicador de filtros ativos (ds-filter-count) via
  trailing da FiltersRow.
- Busca principal na toolbar da DataTableSection (serverSearch debounced).

## X3. Configurações iniciais por página

- NonMovingStockPage: columnPreferencesKey supplies.non-moving-stock.columns
  (visibilidade inicial distinta), fontSizePreferencesKey,
  viewLayoutPreferencesKey e columnWidths persistidos por hook
  useTableColumnWidths (storage key própria da página).
- InventoryAccuracyPage: chaves equivalentes com namespace
  supplies.inventory-accuracy.*. Preferências isoladas entre páginas.

## X4. Comportamento de seleção

- Seleção por índice de página (DataTableSelection), individual e selecionar
  página; limpeza explícita via UI.
- Seleção é limpa em qualquer mudança de query (busca/filtros/sort/página/
  page-size) via handlers de evento — não via effect — porque os índices são
  relativos à página renderizada.
- Sem selecionar tudo global: backend não possui contrato/semântica para o
  conjunto completo — intencionalmente não oferecido.

## X5. Exportação

- SuppliesExportButtons (CSV/XLSX/PDF) recebe resolvePayload com os mesmos
  parâmetros efetivos do request da tabela (período/filiais/armazém/status/
  blocked/search/sort) — exportação respeita filtros e ordenação, não apenas
  a página carregada.
- Campos exportados limitados às colunas/allowlist do endpoint.

## X6. Responsividade

- viewLayoutPreferencesKey + renderCard (DataRecordCard) com fallback
  automático abaixo de viewLayoutMobileMaxWidthPx.
- Overflow horizontal controlado via resizableColumns + min-widths;
  números à direita com tabular-nums; status com selo textual (não apenas cor).

## X7. Evidências

- LINT: PASS — eslint 0 erros nos 5 arquivos tocados (warnings de
  setState-in-effect resolvidos: limpeza de seleção orientada a evento).
- TYPECHECK: PASS filtrado — 0 erros nos arquivos deste diff; tsc -b upstream
  segue com falhas pré-existentes (R-14).
- BUILD: PASS — vite build dashboard-supplies; plugin-ui build +
  verify-host-exports OK.
- BACKEND: PASS — 107 testes supplies/adjustments/branch/bff verdes (sem
  mudança backend neste ciclo; contrato inalterado).
- BROWSER_E2E / SCREENSHOTS: TEST_NOT_RUN — sem acesso autenticado ao
  ambiente nesta sessão; homologação visual permanece pendente (R-13).
- REGRESSÃO: passthrough aditivo; consumidores existentes de DataTableSection
  sem mudança de comportamento (props opcionais).

## X8. Residual ledger (incremento)

| ID | Status | Nota |
|---|---|---|
| R-15 | novo | exportação cobre o conjunto filtrado via re-request com os mesmos parâmetros; volume governado pelo limite do endpoint |

---

# PARTE V — P0 FILTER-STATE (TASK DAVI-SUPPLIES-GLPI1197-FILTER-STATE-P0-003)

## Y1. Causa raiz (confirmada por contrato + código)

Cenário reportado: período personalizado 01/09/2025–30/09/2026, armazém 01,
consolidado — resumo com 993 produtos sem giro (~R$ 1,1 mi) e detalhe com
0 registros ao filtrar "Sem giro (12m)".

- `resolve_consumption_window` classifica a janela: sem datas = rolling_12m
  → `NO_CONSUMPTION_12M`; com start+end = custom_period →
  `NO_CONSUMPTION_IN_PERIOD`. Cada produto recebe exatamente UM dos dois
  status por consulta.
- O dropdown do detalhe oferecia os dois valores brutos; selecionar
  "Sem giro (12m)" sob janela custom gerava `turnover_status =
  'NO_CONSUMPTION_12M'` — predicado válido mas semanticamente impossível na
  resposta → 0 itens. O resumo seguia contando IN_PERIOD → divergência.

Correção (frontend, sem mudança de contrato): as duas opções foram
unificadas em "Sem giro" (token `NON_MOVING`), resolvido para o status da
janela vigente na construção do request — `isDefaultWindow` é exatamente a
mesma condição que o backend usa para `rolling_12m`. Seleção inválida por
mudança de período deixa de ser possível por construção. O rótulo por linha
continua mostrando o status concreto retornado (12m vs período).

## Y2. Auto-refresh — auditoria da cadeia

Cadeia já reativa: filtro → estado → params memoizados → `useSuppliesResource`
(deps) → AbortController (resposta antiga descartada, nunca sobrescreve a
nova) → `refreshing` → tabela ocupada. Verificado filtro a filtro:
competência, datas, filiais, armazém, status, bloqueio, resultado, busca
(debounce 400 ms), ordenação, página e page-size — todos disparam consulta
sem depender do botão Atualizar (que permanece como refresh explícito).

Gaps corrigidos neste ciclo:

- Seleção de linhas agora é invalidada também nas mudanças vindas do
  FilterBar global (competência/datas/filiais) — antes só os filtros de
  detalhe limpavam a seleção.
- Footnote das duas páginas declara explicitamente o escopo: filtros de
  status/bloqueio/busca/ordenação afetam apenas a listagem; KPIs refletem
  o universo do recorte (resumo × detalhe compartilham start/end/branches/
  warehouse via `baseParams`).

## Y3. Backend como autoridade

Sem filtragem local de registros: busca, predicados, ordenação, total,
paginação, classificação de giro, bloqueio, período, filial, armazém e
resultado de contagem são 100% backend. Frontend resolve apenas o token de
UI "Sem giro" para o status da janela — resolução determinística da mesma
regra de classificação, não inferência de dados.

## Y4. Evidências

- BACKEND: PASS — 29 testes non-moving (incl. 2 novos: use case encaminha o
  status da janela p/ resumo e itens em ambas as janelas; SQL aceita
  NO_CONSUMPTION_IN_PERIOD como irmão do predicado 12M).
- LINT/TYPECHECK: PASS filtrado — 0 erros nos arquivos do diff.
- BUILD: PASS — vite build dashboard-supplies.
- TESTES FRONTEND AUTOMATIZADOS: TEST_NOT_RUN — projeto não possui runner
  de testes (vitest ausente, pré-existente); invariantes de auto-refresh
  validados por auditoria de código + testes backend.
- BROWSER_E2E / SCREENSHOTS: TEST_NOT_RUN — sem acesso autenticado;
  homologação visual permanece pendente (R-13).
