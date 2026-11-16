# 123 — EVA EXECUTION REPORT: analyze(routing.line_balance) + knowledge(routing.balance_guide)

**TASK_ID:** `EVA-ENGINEERING-LINE-BALANCING-KNOWLEDGE-AND-ANALYSIS-01`
**DATA:** 2026-11-16
**STATUS:** `IMPLEMENTED — E2E autenticado real comprovado (stack canônica)`

```text
TASK_ID              EVA-ENGINEERING-LINE-BALANCING-KNOWLEDGE-AND-ANALYSIS-01
BASE_HEAD            dc7a252e945f23bcdd2cfd2476e8945df02856e6
STATUS               Implementado; E2E real na stack canônica local;
                     deploy conforme procedimento canônico
```

## Matriz de conhecimentos e fontes (Fase 2)

| Conceito | Tipo | Fonte | Status |
|---|---|---|---|
| Takt time, tempo de ciclo, conteúdo de trabalho, mínimo teórico de postos, eficiência, ociosidade, gargalo, precedência, amortização de setup | Engenharia Industrial geral | Método clássico (não é regra DELPI) | knowledge `routing.balance_guide` v1.0 |
| Mapeamento campo-oficial → conceito (standard_time_minutes_piece = tempo/peça OBSERVED; setup_hours = por lote; linha = produto×operação×componente; estágio = product_code×bom_level) | Semântica do contrato | api-delpi `/products/{code}/guide` + Doc 122 | knowledge v1.0 |
| Regras particulares DELPI de balanceamento (operadores/postos/layout) | Específico DELPI | **não existe fonte aprovada** — não inventado | declarado como limitação; SIMULATION exige revisão |

## Contrato proposto (implementado)

`analyze(analysis_type="routing.line_balance", parameters={...})`

- **Entradas** (vocabulário fechado — `BALANCE_INPUT_FIELDS`):
  `product_code` (obrigatório), `branch`, `max_depth`, `bom_levels[]`,
  `demand`, `available_minutes`, `batch_size`, `num_stations`.
- **Dados oficiais:** mesma fonte de `read(routing.steps)` —
  `fetch_product_guide` → api-delpi `/guide` (Bearer humano delegado,
  sem service token).
- **Saída:** `data_class` PARTIAL|CALCULATED; `parameters{}` rotulados
  PROVIDED|INVALID|UNKNOWN; por estágio: `work_content_minutes`,
  `takt_minutes`, `theoretical_min_stations`, `bottleneck_candidate`,
  `over_takt_operations`, `station_check`, `balance_scenario`
  (SIMULATION/FFD), `missing_parameters`, `invalid_parameters`,
  `limitations`; `operations[]` com `components[]` consolidados.
- **Estados:** forbidden→403, not_found→404, indisponível→502,
  vazio→`stages=[]` honesto, params desconhecidos→validation.

## RQ / AC

| RQ | AC | Resultado |
|---|---|---|
| RQ-01 tool analyze existente | AC-14 zero tools novas | PASS — 6 tools no `tools/list` real |
| RQ-02 mesma fonte delegada | AC-11 estados honestos | PASS — forbidden/timeout/not_found testados |
| RQ-03 cálculo determinístico | AC-16 referência independente | PASS — valores calculados à mão batem (0.84 takt, ceil→6, FFD 2 postos, setup 0.6/100) |
| RQ-04 dedupe por componente | AC-01 operações repetidas | PASS — 6 rows → 3 ops únicas (E2E real) |
| RQ-05 estágios separados | AC-02 multi-nível | PASS — L0 e L1 nunca somados |
| RQ-06 setup por lote | AC-06 só com batch_size | PASS — sem lote: reportado à parte; batch 100 → 0.012 min/peça (live) |
| RQ-07 análise parcial | AC-07 missing_parameters | PASS — PARTIAL + missing/invalid (live) |
| RQ-08 knowledge versionado | AC-15 tópico servido | PASS — `routing.balance_guide` v1.7, 9 orientações (live) |
| RQ-09 AuthZ humano | AC-12 service negado | PASS — principal service → erro |
| RQ-10 compatibilidade | regressão | PASS — suíte 1362 verdes, só 3 falhas pré-existentes de baseline |

## Implementação

- `engineering_app/domain/routing/line_balance.py` (novo) — domínio
  puro, sem framework: `group_routing` (dedupe por
  produto+operação+CT+recurso+nível; componentes anexados) e
  `compute_balance` (takt, conteúdo, mínimo teórico, gargalo,
  over-takt, amortização de setup, station_check, cenário FFD
  SIMULATION; precisão 6 casas; inválido/fornecido classificado).
- `semantic_registry.py` — `routing.line_balance` (analyze) +
  `routing.balance_guide` (knowledge).
- `semantic_bridge.py` — `_ANALYZE_KINDS`, dispatch,
  `_analyze_routing_line_balance` (vocabulário fechado, estados
  honestos, rotulagem completa).
- `server.py` — descrição da tool `analyze` menciona o novo tipo.
- `eva_engineering_knowledge.json` — v1.7, tópico
  `routing.balance_guide` (método IE geral × mapeamento DELPI;
  regras DELPI ausentes declaradas).
- `tests/test_line_balance.py` (10 testes de domínio com referência
  calculada à mão) + 12 testes semânticos em
  `test_eva_mcp_semantic.py`.

## Testes

- **UNIT:** 10/10 domínio — dedupe, estágios, takt, mínimo teórico,
  gargalo, setup c/ e s/ lote, missing/invalid, FFD, vazio.
- **CONTRACT/SEMANTIC:** 12 novos — cadeia completa via adapter
  delegado (args: code/branch/max_depth/page=None), PARTIAL,
  parâmetro desconhecido, product_code ausente, roteiro vazio
  honesto, forbidden 403, not_found 404, unavailable 502, escopo
  `bom_levels`, principal service negado, parâmetros inválidos
  rotulados INVALID, tópico knowledge.
- **REGRESSION:** suíte engineering-api — 1362 pass, 21 skip,
  3 falhas pré-existentes de baseline (comprovadas em HEAD anterior,
  domínios PRC/drawing/OCR não tocados).
- **GATES:** `audit_architecture_phase3 --check` 0 regressões;
  `audit_platform_guardrails --check` 0 findings.
- **E2E REAL (stack canônica, 2026-11-16):** token real
  ti_delpi→delia-api→mcp-engineering:
  - `analyze(routing.line_balance, 90264302, demand=500,
    available_minutes=420)` → CALCULATED; 6 linhas → 3 operações
    únicas; 3 estágios (L0 produto + L1 por componente); takt 0.84;
    gargalo op 01; cenário SIMULATION;
  - `knowledge(routing.balance_guide)` → v1.7, 9 orientações;
  - sem demand → PARTIAL + `missing_parameters`;
  - `demand=0` → PARTIAL + `invalid_parameters` + rótulo INVALID;
  - `batch_size=100` → setup amortizado 0.012 min/peça;
  - parâmetro desconhecido → validation;
  - `tools/list` → exatamente 6 tools.

## Verificação independente (rodada 1)

Motor oficial delpi-verifier indisponível (devin CLI sem auth).
Subagente independente (contexto limpo, read-only, adversarial):
**`ACCEPT_WITH_RESIDUAL`**. Verificou as 7 claims no código com
aritmética conferida à mão; tentou falsificar div-zero, mutação de
ops, colisão de estágio, double-count por componente — sem quebra.

Resíduos do verificador (rodada 1) e disposição:
- R1 rótulos top-level × inválidos → **CORRIGIDO** (INVALID +
  invalid_parameters; teste novo).
- R2 takt→0.0 divisão por zero → **CORRIGIDO** (guardas `takt`
  truthy + `or None`).
- R3 `bom_level` não numérico → **CORRIGIDO** (`_num`).
- R4 batch/num_stations=0 silencioso → **CORRIGIDO**
  (`invalid_parameters` + limitation).
- R5 `setup_hours_total` (todas as ops) × amortizado (timed ops):
  semântica intencional — total é fato do roteiro; amortização só
  onde há tempo/peça. Registrado.
- R6 `demand` fracionária <1 → **CORRIGIDO** (`_positive_int`
  retorna None → invalid/missing coerente).
- R7 `official_rows`/`unique_operations` pré-filtro vs stages
  escopados → divulgado em `filters_applied` (info).
- R8 branch whitespace → **CORRIGIDO** (strip antes do envio).
- R9 componentes duplicados → **CORRIGIDO** (dedupe por código).
- R10/R11 info — descrição `analyze`/`read` omite tipos antigos
  (pré-existente); vocabulário fechado duplicado registry×domain
  (mesmo padrão das ações existentes).

## Deploy

```text
COMMIT_SHA         fe45768bba35b87e454f7e60205b0f42b7ecd279
PUSH_VERIFIED      origin/main == fe45768bba (ff-only)
DEPLOY_ENVIRONMENT PROD srv-api — up-prod-sequential.sh --build
                   engineering-api
DEPLOY_SHA         fe45768bba
DEPLOY_STATUS      SUCCESS — delpi-engineering-api healthy; código
                   conferido no container (registry 341/507, domain/
                   routing/, knowledge v1.7); MCP unauth → 401
RUNTIME_POSTCONDITION 6 tools; analyze/knowledge novos tipos;
                   boundaries 401 sem auth
ROLLBACK_READINESS git revert + mesmo script
```

## Limitações declaradas da capability

- Precedência, operadores, layout e disponibilidade não constam no
  contrato do roteiro — cenários FFD são SIMULATION e ignoram
  precedência; revisão de Engenharia obrigatória.
- `setup_hours` sem `batch_size` fica fora do tempo por peça.
- Operações sem `standard_time_minutes_piece` excluídas do conteúdo
  e listadas em `operations_missing_time`.
- Demanda/capacidade: não há fonte oficial DELPI consultável nesta
  task — são parâmetros fornecidos pelo solicitante (PROVIDED).

## FRONTEND_HANDOFF

- A visualização de balanceamento consome `analyze` via MCP
  (host EVA/ChatGPT). Se o Portal quiser superfície REST dedicada,
  é decisão separada — hoje o BFF expõe apenas
  `/v1/products/{code}/routing` (dados brutos).
- Renderizar por estágio (product_code × bom_level), nunca uma
  linha única multi-nível; exibir rótulos
  OBSERVED/PROVIDED/CALCULATED/SIMULATION; destacar
  `operations_missing_time`, `missing_parameters` e limitações;
  cenário FFD marcado como simulação.

## NEXT_BOUNDED_STEP

1. Confirmação do owner em sessão EVA/ChatGPT (pergunta-canônica:
   "Analise o balanceamento do produto 90264135 considerando
   demanda de 500 peças por turno e 420 minutos disponíveis.").
2. Fonte oficial de demanda/capacidade (sales/open-orders existem na
   api-delpi — integração como PROVIDER separado se aprovado).
3. Precedência oficial (SH6/SH8 ou artefato de processo) para
   cenários de realocação com restrições reais.
4. Follow-up plataforma: classificação de 4xx de validação upstream
   (residual transversal já registrado no Doc 122).
