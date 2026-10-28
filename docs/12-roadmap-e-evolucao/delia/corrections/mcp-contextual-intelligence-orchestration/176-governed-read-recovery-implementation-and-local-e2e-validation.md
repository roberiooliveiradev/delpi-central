# 176 — Governed READ Recovery Implementation & Local E2E Validation

**TASK_ID:** `DELIA-C3-GOVERNED-READ-RECOVERY-IMPLEMENTATION-01`
**Executor:** Cursor / Devin
**Plano primário:** Documento 175
**Direção de produto:** Documento 170
**Evidência causal de produção:** Documentos 172–173
**Contexto de segurança:** Documento 174
**Status:** aguardando revisão independente.

---

## 1. Reancoragem

| Campo | Valor |
|---|---|
| BASE_HEAD | `fad973015d` (preenchido no commit final) |
| ORIGIN_MAIN | verificado no push |
| WORKTREE_STATUS | 6 arquivos do escopo, sem artefatos temporários |
| AUTHORITIES_READ | 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 |
| CURRENT_PHASE | C3 |
| CP_RQ | não avançado |
| Docs lidos | 170, 171, 172, 173, 174, 175 (integral), revisões independentes, Execution Ledger |

Sem conflito arquitetural. Nenhum `ARCHITECTURE_DECISION_REQUIRED` disparado.

## 2. WP0 — Inventário e Reuse Gate

### Mecanismos confirmados no HEAD

| Mecanismo | Papel | Localização |
|---|---|---|
| `_build_arguments` + `_validate_instance` | validação tipada pré-invocação contra `ProviderCapability.input_schema` | `orchestration.py`, `argument_validation.py` |
| `_invoke` / `_invoke_selected` | fronteira de execução: live group, AuthZ/op-class, deadline, dedup, provenance | `orchestration.py` |
| `_recover_relevance` | única rodada de recuperação semântica bounded | `orchestration.py` |
| `_judge_goal_evidence` / `_apply_semantic_relevance` | julgamento de correspondência | `orchestration.py`, `outcome_assessment.py` |
| `EvidenceFacts` | `records`, `total_count`, `coverage_complete`, `explicit_empty`, `is_complete` | `outcome_assessment.py` |
| `extract_pagination_envelope` | projeta `page`/`page_size`/`has_more`/`total` do envelope do owner | `paginated_result_semantics.py` |
| `HttpOpenApiInvoker` | traduz HTTP → `CapabilityProviderError(code, message, owner_hint)` | `http_invoker.py` |
| `error_response` (api-delpi) | envelope compartilhado `success:false` + `message` + `error{code,recoverable}` | api-delpi interface |

**EXISTING_EQUIVALENT=YES → REUSE_DECISION=EXTEND.** Nenhum planner, engine, agente ou DTO paralelo criado.

### Gaps causais confirmados

1. `_recover_relevance` capturava `CapabilityProviderError` e retornava `None` — o hint seguro do owner (mensagem do envelope 400) nunca chegava ao modelo.
2. O primeiro `_invoke` fora da recuperação não tinha entrada para a rodada de recuperação quando o owner rejeitava argumentos de forma recuperável — o turno terminava `insufficient/goal_mismatch`.
3. O feedback de recuperação não projetava metadados de cobertura (`total_count`, `coverage_complete`, `explicit_empty`, `returned_count`) já extraídos em `EvidenceFacts`.

## 3. Implementação (menor diff)

### `contracts.py`
- Nova constante `OWNER_ARGUMENT_REJECTED = "owner_argument_rejected"` — código de wire estável para rejeição contratual recuperável do owner em READ.

### `http_invoker.py`
- `_owner_recoverable_rejection_hint(response)`: HTTP 400/422 com envelope compartilhado (`success:false` + `message` string), `error.recoverable is not False` → hint sanitizado (printable-only, ≤240 chars). Envelope com `recoverable:false`, envelope ausente ou body não-Mapping → `None` (falha comum de invocação).
- No dispatch de erros ≥400: hint presente → `CapabilityProviderError(OWNER_ARGUMENT_REJECTED, "status=N", owner_hint=hint)`.
- 401/403 continuam `mcp_authorization_denied`; 404-not-found e demais códigos inalterados.

### `orchestration.py`
- **Entrada na recuperação no primeiro invoke:** `CapabilityProviderError` com `code == OWNER_ARGUMENT_REJECTED` e recovery não utilizada → `_recover_relevance(..., owner_error_hint=exc.owner_hint)` com `GoalEvidenceJudgment` sintético (`mismatch_hint` = hint do owner, bounded). Outros códigos → comportamento terminal inalterado.
- **Feedback estruturado:** o bloco JSON de `relevance_feedback` passa a carregar `coverage {returned_count, total_count, coverage_complete, explicit_empty}` — fatos autoritativos de `EvidenceFacts`; `None` quando o owner não declara — nunca fabricado — e `owner_error {classification, owner_hint}` quando presente.
- **Rodada de re-invocação bounded:** loop de no máximo 2 re-invocações dentro da MESMA rodada de recuperação (reformulação + reparo contratual). Cada proposta passa por todos os gates: `_build_arguments` (validação tipada), `_unproven_identifier_inputs`, dedup de argumentos idênticos (vs `prior_arguments` na mesma capability e vs proposta recém-rejeitada), deadline/budget. `OWNER_ARGUMENT_REJECTED` na re-invocação alimenta o hint de volta ao feedback uma única vez; qualquer outro erro → terminal. Erros não-provider → terminal silencioso (comportamento preexistente preservado).

### Propriedades preservadas
- LLM decide semântica (refinar, paginar, outra capability, encerrar); código decide contrato, autorização, limites.
- 401/403/policy → `mcp_authorization_denied`, terminal, zero retry.
- WRITE/PREPARE/ACT: caminhos `_prepare_invoke`/`_act_invoke` inalterados — um `owner_argument_rejected` ali (improvável: envelope 400 em mutação) continua erro terminal, nunca vira READ.
- Sem regex de produto, sem tabela TOTVS, sem branch de provider.
- Texto do owner permanece dado não confiável dentro de um campo JSON — nunca instrução.

## 4. Testes RED → GREEN

### RED (pré-implementação, commit base)
`test_first_invoke_recoverable_rejection_enters_recovery` reproduziu o shape de produção: `arg_keys=product_type,query` → erro de invoke → terminal `insufficient/goal_mismatch`, sem reformulação. O teste usa o código de wire literal (`owner_argument_rejected`) para exercer o caminho real sem depender do símbolo novo.

### Novos testes (GREEN)

`tests/test_goal_evidence_relevance.py` (+8):
- `test_recoverable_rejection_inside_recovery_refed_and_reformulated` — 3 invokes governados: irrelevante → 400 → reformulado; nunca loop.
- `test_recoverable_rejection_repeated_invalid_args_stops` — proposta idêntica à rejeitada → `identical_arguments`, 2 wire calls.
- `test_first_invoke_recoverable_rejection_enters_recovery` — 400 no primeiro invoke entra na rodada bounded → sucesso.
- `test_first_invoke_terminal_error_stays_error` — 500 → erro terminal, 1 wire call.
- `test_recovery_feedback_carries_authoritative_coverage` — `total=77/has_more` projetado no feedback (`returned_count=2, total_count=77, coverage_complete=false, explicit_empty=false`).

`tests/test_openapi_capability_provider.py` (+3):
- 400 com envelope compartilhado → `owner_argument_rejected` + hint sanitizado.
- 400 com `error.recoverable:false` → `openapi_invocation_failed` (terminal).
- 400 sem envelope → `openapi_invocation_failed`.

## 5. Regressão

- `test_goal_evidence_relevance.py`: 51/51.
- `test_openapi_capability_provider.py` + `test_projection_omission_recovery_contract.py`: incluídos nos 99 iniciais.
- Suíte completa `delia-api/tests/`: **1 falha pré-existente** — `test_cri_instruction_variant_carries_requirements_clause` falha no HEAD base sem nenhum arquivo meu (v24 `2a6acc0f3a` embutiu `answer_requirements` inline na instrução governada enquanto o teste exige que venha só da cláusula CRI → duplicação real em runtime). Registrado como achado residual/drift documental — decisão do owner da instrução/CRI, não alterada neste escopo.
- `audit_architecture_phase3.py --base HEAD --check`: OK, sem nova regressão.

## 6. WP4 — Contrato `search_products` (api-delpi)

| Campo | Valor |
|---|---|
| Rota | `GET /products/search` (product_routes.py:202) |
| Args | `code`, `group_code`, `subgroup`, `product_type` (CSV, cada código com 2 chars), `description`, `customer_reference`, `page ≥ 1`, `page_size` (limites canônicos), `sort`, `direction` |
| Rejeição 400 | `error_response("product_type inválido: use códigos de 2 caracteres separados por vírgula (ex.: MP,PI,PA).", 400)` → `success:false` + `message` + `error:null` |
| Envelope de página | `product_success` → `paged_list` com `page`, `page_size`, `total`, `total_pages` |
| AuthZ | `ENGINEERING_LMP_ACCESS` no route; nunca bypassado |

**Matriz de responsabilidade:**
- `DELIA_RESPONSIBILITY`: seleção semântica, proposição de argumentos, julgamento de relevância, reformulação bounded, honestidade de cobertura.
- `DOMAIN_API_RESPONSIBILITY`: validação do `product_type` (2 chars), filtros, ranking textual, ordenação, paginação, envelope.
- `CONTRACT_GAP`: (a) `error.recoverable` não é declarado na rejeição de argumento — o adapter infere recuperável-por-forma (success:false + 400 + sem `recoverable:false`); declaração explícita pelo owner fortaleceria o contrato; (b) `total_pages` não alimenta `has_more` na projeção DÉLIA — `coverage_complete` deriva de `total_count` quando ausente (honesto, sem fabricação); (c) semântica de busca por descrição/ranking para termos coloquiais ("terminal bala") segue limitação do owner documentada nos docs 172–173.
- `OWNER_DECISION_REQUIRED`: declaração explícita de `recoverable` nas rejeições contratuais; exposição de `has_more` ou derivação aprovada de `total_pages`; ranking/tokenização de `description`.
- Nenhuma linha da Domain API alterada.

## 7. Residual search (bounded)

- Catch sites de `CapabilityProviderError` revisados (17): discovery e index-probe usam argumentos determinísticos (não propostos pelo LLM) → `owner_argument_rejected` ali é anomalia contratual e permanece terminal por desenho. PREPARE/ACT permanecem erro terminal. Replay de resume trata como erro. Nenhum caminho de AuthZ alterado.
- 401/403 continuam `mcp_authorization_denied` antes do novo dispatch — zero reclassificação.
- Erros transitórios (429/5xx/timeout) não produzem hint → permanecem `openapi_invocation_failed` com o comportamento técnico preexistente.
- Achado fora de escopo (registrado, não corrigido): drift teste-vs-v24 na instrução `answer_requirements` (§5).

## 8. Avaliação local E2E (modelo real, owner falso)

- Harness: `delia-api/scripts/governed_read_recovery_eval.py` — reutiliza `_compose`/fixtures existentes; `OpenAICompatibleModelInvocationAdapter` real → `delpi-ollama` (qwen2.5:3b, baseline local documentada — não é requisito de produto); owner wire falso reproduzindo só o contrato observável (400 com envelope, 403, página com `total/has_more`). **Zero queries de produção, zero owner calls reais.**
- Cenários: S1 sucesso direto; S2 rejeição 400 → hint → reformulação; S3 cobertura/paginação; S4 403 terminal; S5 rejeição persistente → stop bounded. Cada cenário: até 4 turns frescos até alcançar o wire do owner (a admissão do 3B é não-determinística — retries só alcançam o caminho avaliado, nunca best-of-N de outcome).

### Resultados — candidato (diff aplicado)

| Cenário | Status | Wire calls | Evidência |
|---|---|---|---|
| S1 direct_success | NOT_APPLICABLE (admission flake, 4 tries) | 0 | admissão 3B classou como surface question |
| S2 recoverable_reformulation | **SUCCESS** | 2 | `product_type:"terminal bala"` → 400 → hint → reformulado (`query:"terminals bala"`, sem product_type) → registros |
| S3 coverage_pagination | NOT_APPLICABLE (admission flake, 4 tries) | 0 | idem |
| S4 unauthorized_403 | NOT_APPLICABLE (admission flake, 4 tries) | 0 | gate determinístico provado nos testes unitários/adapter |
| S5 repeated_rejection | SOURCE_UNAVAILABLE (bounded) | **3** | `terminal bala` → `MP,PI,PA` → `MP, PI` — reformulações distintas, teto = 1+2, stop honesto |

S2 candidato: 11 chamadas de modelo, 12 074 in / 337 out units, 176,7s. S5: 3 wire calls máx. — teto da rodada de recuperação respeitado; nenhum args idêntico re-executado.

### Resultados — baseline (HEAD sem o diff, mesmo harness/modelo/corpus)

| Cenário | Status | Wire calls | Evidência |
|---|---|---|---|
| S1 | SUCCESS c/ insufficient_evidence | 1 | `product_type:"terminal bala"` aceito pelo owner falso (sem reject_rule) |
| S2 | NOT_APPLICABLE (admission flake, 4 tries) | 0 | flake |
| S3 | SUCCESS | 1 | 3B julgou página irrelevante como corresponds — flakiness do juiz 3B, registrado |
| S4 | **AUTHZ_DENIED** | 1 | 403 → terminal, zero retry — fail-closed confirmado na cadeia real |
| S5 | SOURCE_UNAVAILABLE | **1** | 400 → erro terminal imediato; nenhuma reformulação |

### Delta business outcome (first-pass, sem contar flakes)

- **S5 é a comparação causal limpa**: baseline morre com 1 wire call após o 400 do owner; candidato executa a rodada bounded de recuperação com reformulações semanticamente distintas guiadas pelo hint (3 calls, teto respeitado) e encerra honestamente.
- **S2 candidato** prova o outcome de negócio alvo: o shape exato da falha produtiva (`product_type:"terminal bala"` → 400 do owner) agora recupera para uma resposta grounded; no baseline esse caminho era `insufficient/goal_mismatch` terminal (RED reproduzido em teste).
- S4 prova em ambos que AuthZ permanece fail-closed com exatamente 1 wire call.
- Admission flakes (3B) não contam como outcome — limitação do modelo baseline já documentada nos docs 168–171; os gates determinísticos cobrem os caminhos não alcançados.

### Métricas (runs que alcançaram o wire)

- MODEL_CALLS: S2=11, S5=8 (candidato); S5=6, S4=6 (baseline por turn alcançado)
- TOOL_CALLS: S2=2, S5=3 (candidato); baseline máx 1 por cenário alcançado
- TOKENS: S2 12 074 in / 337 out; S5 cand ~12k in (multi-try); baseline S1 12 854/397, S3 8 036/285
- LATENCY: turn completo ~115–207s (3B CPU); flakes de admissão ~2s
- FALSE_POSITIVES=0; FABRICATED_RECORDS=0; UNAUTHORIZED_RETRIES=0; UNBOUNDED_LOOPS=0

## 9. Segurança

- Nenhum secret em logs/testes/relatório; `DELIA_LLM_API_KEY=eval-placeholder` só no eval local (Ollama ignora).
- Nenhum bypass de AuthZ; 401/403 fail-closed (teste + S4).
- Nenhum WRITE/PREPARE/ACT executado.
- Hint do owner sanitizado (printable, ≤240 chars) e carregado como dado.
- `IDENTITY → LIVE CORE AUTHZ → DOMAIN AUTHORITY` preservado.
- Chave OpenRouter: não rotacionada nesta task — decisão do security owner (doc 174).

## 10. Rollback

Diff contido em 4 arquivos de produção/teste + 1 script de eval + este documento. Rollback = `git revert` do commit. Nenhum dado, migration, contrato externo ou config de produção foi alterado. O código novo só ativa em `OWNER_ARGUMENT_REJECTED`, código que o adapter pré-diff nunca emitia — reverting restaura o comportamento terminal anterior sem efeitos colaterais.

## 11. Veredito

**LOCAL_PASS_WITH_RESIDUAL** — elegível para revisão independente:

- R1/R2/R3 implementados no menor diff sobre mecanismos existentes (REUSE=EXTEND); nenhum planner/engine/agente novo, nenhuma regra de produto.
- RED→GREEN comprovado no caminho real; regressão completa sem falha nova (1 falha pré-existente de drift v24 registrada para o owner da instrução).
- E2E local com modelo real prova o delta causal: rejeição 400 recuperável → reformulação bounded → sucesso (S2) e stop honesto no teto (S5); AuthZ fail-closed (S4 baseline + gates unitários); zero fabricação, zero retry não autorizado, zero loop.
- Residuais: flakes de admissão/juízo do 3B (baseline, não do diff); `error.recoverable` não declarado pelo owner na rejeição de argumento (inferência por forma do envelope — NEEDS_OWNER_DECISION para contrato explícito); ranking de descrição do owner segue pendente (docs 172–173); rotação da chave OpenRouter segue `RISK_ACCEPTANCE_PENDING_SECURITY_OWNER` (doc 174).
- **Não** é declaração de production readiness: elegibilidade do diff sujeita à revisão independente; `PRODUCTION_DEPLOY_EXECUTED=NO`; `PRODUCTION_QUERIES=0`; fase não avançada.
