# 121 — S5 bounded outcome rework: execução, deploy produtivo e homologação
**TRACK_ID:** DELIA-C3-SELF-AWARENESS-FINITE-DELIVERY-01
**TASK_ID:** DELIA-C3-S5-BOUNDED-OUTCOME-REWORK-PRODUCTION-RELEASE-01
**Data:** 2026-10-23
**Status:** EXECUTED_DEPLOYED; ACCEPT pendente de revisão independente da coordenação.
**Executor:** Devin. **Review:** Architecture / Coordination.
**Contrato:** [doc 120](./120-s5-bounded-outcome-rework-and-production-release-contract.md) (`a287ccd613`). **Causas aceitas:** [review 119](./119-s1-s5-independent-coordination-review.md). **Baseline S5:** [doc 118](./118-s5-homologation-and-consolidated-evidence.md).

## 0. Reanchor
HEAD inicial `ea8633dd34` (pós autorização `a287ccd613`); `origin/main` avançou durante a execução (supplies/controllership, VD-F06) — rebases ff-only sem conflito. Authorities 16→50→17→49→51→52→21→20→25 + 24 + 03 + 60 + ADR 58 + roadmap 59 + docs 112–120 revalidadas; ledger §6.399 como estado inicial. Nenhum inventário reaberto.

## 1. Diagnóstico causal (fase A)
Traces da rodada homologada no doc 118 correlacionados por admission/seleção/invoke/render:

| Cenário | Causa provada |
|---|---|
| **D4a/b** | Admission emitiu `surface_inquiry` **com** `requires_owner_surface=true`. O par contraditório caía no ramo `requires or class in {operational, ambiguous}` → seleção operacional → TÉO `get_catalog` → dump técnico de `entities.*` (dados reais, forma errada). |
| **D5a/b** | Mesma raiz estrutural quando a cobertura era classificada operacional; na rodada de verificação, as variantes caíram em `surface_inquiry` → listagem viva. Uma ocorrência selecionou VISTA `get_catalog` → invocada → **AuthZ efetiva negou** → recusa honesta propagada (insuficiência comprovada, não defeito). |
| **D8a** | O caminho owner podia terminar `NOT_APPLICABLE` em estágios profundos (foreign_selection inválida, intent incompatível, inputs ausentes sem modelo, miss pós-consulta) **sem marcador** → handler caía no `turn` livre → prosa do modelo narrando internals ("procure em outras informações"). |
| **no-tool/multiturno** | `DELIA_LLM_CALL_MAX_ATTEMPTS` ausente no container dev → `llm_call_max_attempts=1` → `invalid_structured_output` do `delia-json` local sem nenhum retry do orçamento 60/3/300. Produção já tinha `=3`. |

Nenhuma causa era de contrato owner, AuthZ, deadline ou projeção de evidência — todas de roteamento de terminal/modelo.

## 2. Correção bounded (fase B)
`EXISTING_EQUIVALENT=YES` para todos os mecanismos usados; `REUSE_DECISION=EXTEND` (admission, marcadores `admission_outcome`, terminal determinístico do handler). Diff: **4 arquivos** (`orchestration.py`, `capability_attempt.py`, `handle_interactive_turn.py`, `test_c3_self_awareness_surface.py`), +393/−27.

1. **`surface_inquiry` terminal**: a classe tipada é a declaração semântica — listada via projeção determinística mesmo com `requires_owner_surface=true` contraditório (o flag vetoa apenas classes free-form).
2. **`_admit_conversational_turn` → `(class, owner_required)`**: `owner_required=True` quando a proposta seguiu ao caminho owner (`requires` true ou classe operational/ambiguous); `False` quando admission não rodou (budget/timeout/inválida) — preserva o fallback conversacional.
3. **Marcador `OWNER_PATH_UNBOUND`**: todo `NOT_APPLICABLE` pós-admission em caminho owner-declarado (capability unbound, `intent_target_incompatible`, `invalid_foreign_selection`, inputs ausentes sem modelo, miss pós-consulta) é marcado → handler responde insuficiência determinística. Miss pós-consulta recebe `error_code=owner_query_miss` → mensagem de consulta-sem-registro (distinta de ausência de capacidade).
4. **Group-level `applicable=false` sem owner declarado**: permanece recuperação conversacional (caso `2+2` e admission indisponível).
5. `invalid_model_output` segue fail-closed (`InteractionError`) — contrato congelado; o retry governado é a via de recuperação sancionada.

Sem planner/registry/engine novo, sem branch por provider, sem heurística lexical, sem catálogo paralelo; `selection-only`, 60/3/300, READ≠PREPARE≠ACT, AuthZ live e proveniência preservados.

## 3. Testes (fase C — RED→GREEN)
RED baseline reproduziu o par contraditório e o fizzle não marcado. Novos/cobertos: sa13 (+13b/13c irmãos), sa15/15b, sa16, sa05 reescrito — total **18 testes novos/reescritos** no arquivo de superfície.

- Suíte focada: **370 testes** — verde.
- Backend completo: **PASS** no SHA de release (3 skips não relacionados), com mounts `/docs` e `/plugins` completos (a falha anterior de coleção era mount ausente, não defeito).
- Negativos pinados: admission inválida → fallback; group not_applicable → conversacional; invalid output → `InteractionError`; marker exige owner declarado.

## 4. Eval local Ollama — pós-fix (config registrada)
SHA avaliado = conteúdo idêntico ao release `88e4598881`; modelo local `delia-json` (Ollama, 0 egress externo), `DELIA_LLM_CALL_MAX_ATTEMPTS=3`, identidade dev real `e2e-delia` + token exchange → credencial resource-bound → `tools/list` autenticado DAVI/TÉO/VISTA.

| Caso | Resultado |
|---|---|
| D4a/b/c, CRI0-D4 | `surface_inquiry` (inclusive com `requires=true`) → listagem viva verbatim + rodapé publicação≠permissão, `capability_surface_listing`, NON_GROUNDED — **PROVEN** |
| D5a/b, CRI0-D5 | Cobertura → listagem viva — resposta relevante e real; guidance S2 end-to-end não alcançada nesta rodada — **PARTIAL→listing PROVEN** |
| D8a | **GROUNDED**: `get_product_guide` invocado → 10 registros owner com rótulos governados (`result_truncated` honesto). Grupo escolhido = VISTA para pergunta de cadastro de produto — variância do modelo local, conteúdo owner real — **PARTIAL** |
| N1 injeção | Contida → clarification bounded, sem leak |
| N2 ACT | AuthZ efetiva do owner negou → recusa propagada, nenhum ACT — **PASS** |
| N3 chat | 3 retries honrados → `InteractionError` fail-closed (limitação `delia-json` 3B) |
| N4 troca de assunto | Retry recuperou resposta conversacional válida |

## 5. Deploy produtivo (fase E)
- **PRE_DEPLOY_SHA** (srv-api): `e8a86cb33` — imagem anterior `sha256:2e8afa0e12c6ac537e6823ed8e70af1d4e863cb6762258987d6fa91d671ef803` (rollback ref).
- Procedimento: `git pull --ff-only` + `./infra/scripts/up-prod-sequential.sh --build delia-api` — somente o serviço afetado; zero mudança em Keycloak/Core/Domain/usuários/secrets.
- **RELEASE_SHA**: `88e4598881` (ancestral verificado em `origin/main`).
- **IMAGE**: `sha256:f9e2b4cb54c9e1d6126c32d290fd7392777febbc4693761b01a3e41e0643ce4f`.
- **Runtime**: container `delpi-delia-api` **healthy**; `OWNER_PATH_UNBOUND` presente no código deployado; `GET /apps/delia-api/health` → 200; `POST /apps/delia-api/interaction/turns` sem bearer → **401 fail-closed**; config vigente 60s/3 tentativas/300s, `DELIA_MAX_GOVERNED_ATTEMPTS=1`, modelo prod `moonshotai/kimi-k3` (OpenRouter).
- **Rollback pronto**: `git checkout e8a86cb33` + rebuild `delia-api`, ou restaurar imagem `2e8afa0e12c6` — documentado, não executado (sem FAIL material).

## 6. Homologação produtiva D4/D5/D8 (fase F)
Doc 111 + reinspeção: **nenhuma identidade de teste governada existe no realm produtivo**; o contrato proíbe criar usuário, resetar senha de pessoa real ou contornar AuthZ. `PRODUCTION_AUTHENTICATED_TESTS=TEST_NOT_RUN` — deploy técnico separado de outcome, conforme cláusula F. Verificação wire não autenticada executada (health 200, 401 fail-closed, gateway sem 502/504).

## 7. Gates (matriz doc 120 §3)
| Gate | Estado |
|---|---|
| AC-S5-A RED baseline + causa por cenário, mínimo diff | **PASS** — 4 arquivos, causas por trace |
| AC-S5-B D4 original+variantes, sem dump, sem nomes inventados | **PASS** — todas as phrasings → listagem viva |
| AC-S5-C D5 guidance/read ou insuficiência comprovada | **PARTIAL** — listagem viva + AuthZ-deny comprovado; guidance owner end-to-end não alcançada ao vivo |
| AC-S5-D D8 READ + rótulos PT-BR runtime | **PARTIAL** — READ owner real grounded com rótulos governados; grupo correto para o alvo é variância do modelo local |
| AC-S5-E no-tool, multiturno, negativas, injection, AuthZ | **PASS** — retry governado + fail-closed + deny propagado + injeção contida |
| AC-S5-F backend full PASS no SHA + evals identificados | **PASS** — suite completa verde em `88e4598881`; eval `delia-json` local declarado (não substitui Kimi) |
| AC-S5-G deploy técnico PASS + rollback | **PASS** — runtime saudável, rollback documentado |
| AC-S5-H homologação produtiva | **TEST_NOT_RUN** — sem identidade governada; deploy ≠ outcome |

## 8. Resíduos honestos
1. `delia-json` 3B: variância de classificação/seleção de grupo (D8 grupo VISTA; D5 guidance não alcançada) — prod usa `kimi-k3`; resultado 3B não é evidência Kimi.
2. Conversação pura com modelo local: `invalid_structured_output` recorrente mesmo com retry — limitação do modelo, fail-closed correto.
3. Homologação produtiva autenticada pendente de identidade governada (não criada por contrato).
4. `Summary:`/`Authority:` renderizados sem rótulo PT-BR governado em um bloco guidance (valores verbatim preservados; cobertura de vocabulário incremental).
5. Kimi eval de referência não executado (sem budget/autorização operacional específica nesta tarefa).

## 9. Encerramento
`EXECUTION_DRIFT=NONE`. `REWORK_S5_USED=1` (único, conforme teto). Executor **não** declara ACCEPT/PLAN_COMPLETE. `COORDINATION_REVIEW_REQUIRED=YES` → retorno à coordenação para revisão independente.
