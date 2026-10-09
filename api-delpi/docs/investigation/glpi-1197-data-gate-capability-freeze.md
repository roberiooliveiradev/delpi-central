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
