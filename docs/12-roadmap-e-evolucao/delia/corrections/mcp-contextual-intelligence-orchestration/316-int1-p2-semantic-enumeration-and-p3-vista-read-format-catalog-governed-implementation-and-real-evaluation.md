# 316 — INT-1 P2 Semantic Enumeration and P3 VISTA Read-Only Format Catalog — Governed Implementation and Real Evaluation

**TASK_ID:** `DELIA-C3-T2-INT1-P2-SEMANTIC-ENUMERATION-AND-P3-VISTA-READ-FORMAT-CATALOG-IMPLEMENTATION-01`
**BASE_HEAD:** `7dbc50bb2df3d85cc1c89b48ad7351bb4e5e23f7` (`HEAD == origin/main`; WIP concorrente preservado)
**PHASE:** C3/T2 — INT-1 não encerrada · `INT1_STAGE_ACCEPTANCE=PENDING_COORDINATION_REVIEW`
**MODEL:** `qwen/qwen3-14b` via `openrouter_qwen` (shape OpenRouter)
**ESCOPO:** implementação autorizada das duas correções do Doc 315 — P2 (instrução de enumeração v2-3) e P3 (catálogo de formatos VISTA sob `TV_READ`). Não é auditoria geral, não é bateria completa.

---

## 1. Reancoragem e decisões congeladas

```text
HEAD:               7dbc50bb2df3d85cc1c89b48ad7351bb4e5e23f7
origin/main:        7dbc50bb2df3d85cc1c89b48ad7351bb4e5e23f7
REFERENCE_HEAD:     348140ec... — superseded por avanço concorrente; reancorado no HEAD real
PHASE_FROM_16:      C3/T2 · INT-1 pendente de revisão de coordenação
CP_RQ:              implementação bounded P2 (instrução) + P3 (owner VISTA read surface)
FROZEN_DECISIONS:   AGENT_COUNT=1 · PYDANTIC_AI_NATIVE=YES · MCP_TOOLSET_LIVE=YES ·
                    NEW_ROUTER=NO · NEW_PLANNER=NO · NEW_RESOLVER_ENGINE=NO ·
                    RBAC_MUTATION=NO · sem hardcode TÉO/process/"transformação"
WIP concorrente:    preservado (plugins/*, controllership, tv-dashboard-api/data)
```

---

## 2. P2 — evolução delimitada da instrução v2-2 → v2-3

### 2.1 Baseline causal (Doc 315)

```text
QUESTION:        "Quais processos de transformação estão cadastrados?"
DEFEITO PROVADO: MODEL ARGUMENT CONSTRUCTION — q:"transformação" model-authored
                 com contrato já corrigido entregue (descrição + filters_applied).
                 Não restava causa de código/schema/contrato no caminho.
```

### 2.2 Implementação (EXISTING_EQUIVALENT=YES · REUSE_DECISION=EXTEND)

`investigation_instructions.delpi.json` recebeu a versão
`generalist-semantic-v2-3-object-authz-continuity` (v2-2 + cláusula geral de
intenção de enumeração), registrada no mecanismo canônico — sem novo código
determinístico de roteamento, sem nouns hardcoded.

Regra introduzida (domínio- e provider-neutros):

1. distinguir enumeração ("quais/liste/cadastrados/disponíveis/todos/opções") de filtragem;
2. enumeração ⇒ usar a capability de list/search do owner **sem inventar termo de busca**;
3. não derivar `q`/nome/família/filtro livre de substantivo de domínio da pergunta;
4. preservar filtros explicitamente pedidos;
5. resultado vazio sob filtro (`FILTERED_SEARCH_EMPTY`) ≠ catálogo autorizado vazio;
6. alargar a consulta apenas quando justificado pelo objetivo/contrato/autorização;
7. respeitar paginação e autorização.

```text
P2_INSTRUCTION_BASELINE:    generalist-semantic-v2-2-object-authz-continuity fp 3692299dac74c26e
P2_INSTRUCTION_NEW_VERSION: generalist-semantic-v2-3-object-authz-continuity
P2_INSTRUCTION_FINGERPRINT: 95e265ee18cd5d66
```

### 2.3 Testes determinísticos

- `test_investigation_instruction_resource.py` / `test_int1_semantic_continuity_remediation.py` — versão/fingerprint atualizados (v2-2 preservada no registry).
- Novo `test_investigation_instruction_enumeration_intent.py` (E1–E6): texto da instrução exige enumeração-sem-filtro, preservação de filtro explícito, distinção filtered-empty vs catálogo-vazio, paginação, negação de autorização e ausência de termos hardcoded.
- **21 testes verdes.**

### 2.4 Avaliação real (`or-qwen14b-2ff9e302c874` / `or-qwen14b-1ab21b3ca278`)

Ambiente isolado: `delpi-teo-eval-int1` (`--root-path /apps/transformometro-api`) +
`delpi-vista-eval-int1` (`--root-path /apps/tv-dashboard-api`), código montado do
working tree; produção intacta (`PROD_CONTAINER_UNTOUCHED=YES`).

```text
P2 ORIGINAL ("Quais processos de transformação estão cadastrados?")
  CALL:   teo.read {entity:process, action:search} — SEM params (enumeração)
  OWNER:  total=109 · items 1..40 · filters_applied={}
  RESULT: GROUNDED · declared partial honesto (result_truncated,
          unmet_obligation pagination_continuation) · 4 exemplos citados
  ⇒ P2_ENUMERATION_INTENT=RECOGNIZED · UNREQUESTED_RESTRICTIVE_FILTER=NO
    P2_OBJECTIVE_SATISFIED=YES · SATISFIED_PROVEN_IN_SAMPLE

P2 CONTROL ("...contêm 'qualidade' no nome?") — filtro explícito
  CALLS:  search {q:"quality"}→0 · search {q:"qualidade",page:1,page_size:10}→1
          · get {id:PROC-0034}
  RESULT: filtro preservado, refinamento legítimo, resposta honesta
          (unmet_obligation busca_por_nome_exato declarado)
  ⇒ EXPLICIT_FILTER_REQUEST→FILTER_PRESERVED
  (1ª tentativa: turn_budget_limited, 0 tool calls — INCONCLUSIVA, não evidência)
```

---

## 3. P3 — catálogo de formatos VISTA sob `TV_READ`

### 3.1 Contrato implementado (EXISTING_EQUIVALENT=YES · REUSE_DECISION=EXTEND)

Nova entidade `display_format` + ação `list` no vocabulário READ existente
(`READ_ENTITY_ACTIONS`), gated por `TV_READ` — sem `TV_WRITE`, sem expor
`get_catalog()` administrativo. Projeção compõe as fontes canônicas existentes:

```text
OWNER:            tv-dashboard-api (VISTA)
OPERATION:        read {entity:"display_format", action:"list"}
FONTE CANÔNICA:   TvDataPresentationModesService (displayModes + blockTypeByMode)
                  + DATA_BLOCK_TYPES/DATA_VIEW_BLOCK_TYPES + block_type_vocabulary()
                  + DisplayFormatService.format_catalog_entries() (formatos de valor)
RESPONSE:         {displayModes{modes, blockTypeByMode}, dataBlockTypes,
                   blockTypeVocabulary, valueFormats} — projeção bounded, sem internals
ERRORS:           UNKNOWN_ENTITY/UNKNOWN_ACTION/VALIDATION_ERROR/AUTHORIZATION_DENIED
POSTCONDITION:    read-only, nada persiste; TV_WRITE continua exigido para catalog/write
```

### 3.2 Contrato model-visible

`vista.read` wire description (`server.py`) atualizada para anunciar
`display_format.list` + entidades já no vocabulário (sha `071279a8…`, len 666).
A docstring do `tool_bridge` foi alinhada — a primeira avaliação P3 provou que a
descrição efetiva vem de `add_tool(description=...)`, não do docstring.

### 3.3 Testes determinísticos

Novo `tests/test_vista_display_format_read.py` (10 casos): `TV_READ` consulta →
PASS; sem `TV_READ` → `AUTHORIZATION_DENIED`; `TV_WRITE` path admin preservado;
fonte canônica reutilizada; projeção bounded sem internals; não-persistência;
vocabulário/context reportam a entidade; MCP anuncia contrato.

```text
RED→GREEN: 1 passando → 10/10 verdes · adjacentes VISTA 130 + suites
           read/facade/conformance: 94 verdes (container)
```

### 3.4 Avaliação real (`or-qwen14b-393ea7510418`)

```text
P3 ("Quais formatos de visualização de dados estão disponíveis?")
  CALL:   vista.read {entity:display_format, action:list} — seleção semântica
          pura (zero regra DÉLIA forçando VISTA)
  OWNER:  catalog canônico — displayModes [auto,bar_chart,chart,kpi,line_chart,
          table] + blockTypeByMode + dataBlockTypes + valueFormats
  RESULT: GROUNDED · resposta apresenta modos, tipos de bloco e formatos de
          valor reais · truncamento declarado honestamente
  ⇒ P3_TV_READ_ALLOWED=YES · TV_WRITE_NOT_REQUIRED=YES ·
    FORMAT_CATALOG_AUTHORITATIVE=YES · P3_OBJECTIVE_SATISFIED=YES ·
    SATISFIED_PROVEN_IN_SAMPLE
```

Runs auxiliares: `or-qwen14b-2ff9e302c874` P3 respondeu via `knowledge`
(GUIDANCE) porque o wire ainda não anunciava a entidade — evidência do gap de
descoberta, corrigido no server.py; `or-qwen14b-1ab21b3ca278` P3
`model_unavailable` (falha ambiental provider, 0 model requests — não contada
como evidência de comportamento).

---

## 4. Orçamento e métricas

```text
TOTAL_REAL_INVESTIGATIONS: 6 (limite autorizado)
  válidas:  P2 ✓ · P2-ctrl ✓ · P3 ✓ · P3-conhecimento (diagnóstico) ✓
  ambiental: P3 model_unavailable (0 model requests)
  inconclusiva: P2-ctrl turn_budget_limited (0 tool calls)
MODEL_REQUESTS: 7 · TOOL_CALLS: 12 (P2=1; ctrl=3; P3=1; P3-conhecimento=5;
  dryruns não contados)
TOKEN_USAGE/COST: UNAVAILABLE (provider não reporta via harness)
LATENCY: P2 55.0s · ctrl 74.2s · P3 56.4s
TRACES: delia-api/.battery/int1-secure-decision-trace/or-qwen14b-{2ff9e302c874,
        1ab21b3ca278,393ea7510418}
PYDANTIC_AI_VERSION: 2.50.0 · agent_instructions_sha256 wire: 2fff53116c83…
```

---

## 5. Residuais e próxima decisão

```text
INT1_MATERIAL_BLOCKERS_REMAINING: nenhum material — P2 e P3 SATISFIED_PROVEN_IN_SAMPLE
NON_BLOCKING_RESIDUALS:         INT1-PROJECTION-BUDGET · attempt.status conflation ·
                                mcp_timeout teo.analyze · falhas baseline pré-existentes
EXTERNAL_OWNER_DEPENDENCIES:    gate R (bateria completa) = decisão de coordenação
FULL_BATTERY=NOT_RUN · PRODUCTION_DEPLOY=NOT_AUTHORIZED · PHASE_ADVANCEMENT=NO
```

**Recomendação:** `ACCEPT_WITH_RESIDUAL` para P2 e P3; INT-1 permanece
`PENDING_COORDINATION_REVIEW` — não autoaprovada.
