# 145 — DÉLIA governed knowledge consumption multi-especialista (DAVI/TÉO/VISTA) — implementação e release

**TASK_ID:** `DELIA-C3-GOVERNED-KNOWLEDGE-CONSUMPTION-AND-PRE-R4-CLOSURE-01`
**OWNER:** `delia-api` · **DATA:** 2026-10-24 · **SHA:** `becef562b9`
**STATUS:** `EXECUTED_AND_DEPLOYED` — aceite independente da coordenação pendente. `R4_AUTHORIZED=NO`.

## 1. Missão e reuse gate

Fechar a lacuna pré-R4: provar que a DÉLIA consome conhecimento técnico, metodológico e operacional publicado legitimamente pelos três especialistas (DAVI, TÉO, VISTA) pelo **mesmo** caminho canônico — seleção de grupo → seleção de capability → argumentos → invoke → candidato → julgamento → Outcome/CRI — sem planner novo, router por provider, adapter, registry ou knowledge engine.

`EXISTING_EQUIVALENT=YES_PARTIAL`; `REUSE_DECISION=EXTEND`; `NEW_PLANNERS=0`; `NEW_MCP_TOOLS=0`; `NEW_KNOWLEDGE_ENGINES=0`.

## 2. Gaps provados (causa-raiz, não sintoma)

A maquinaria completa já existia. Três descontinuidades pontuais impediam o consumo de conhecimento live:

1. **Admission bypass** — perguntas conceituais/metodológicas cujo assunto vive numa superfície owner eram classificadas `conversational/explanation` e respondidas de priors do modelo, sem consulta governada.
2. **Seleção/formulação** — `select_group` podia preferir busca de registros a guia/documento para perguntas de conceito; a query de discovery podia ranquear ação operacional (`code` obrigatório) à frente da ação documental.
3. **Miss sem recuperação** — um miss pós-consulta (candidato unusable/zero) encerrava `NOT_APPLICABLE` sem entrar na rodada única de recuperação já existente.
4. **Apresentação** — `MAX_FIELDS_PER_RECORD=4` + ordem do owner fazia linhas CRI exibirem `section/heading/line_start/line_end` e nunca `text`; a resposta mostrava citação, não conteúdo.

## 3. Diff bounded

- `config/orchestration_instructions.delpi.json` — recurso governado **v3→v4**:
  - `interaction_admission`: perguntas conceituais/how-to cujo sujeito vive em superfície owner (semântica de registros, features/métodos de produto owner, painéis operacionais) são `operational` → a superfície owner é consultada; teoria genérica permanece conversacional.
  - `select_group`: perguntas de significado/conceito/documentação preferem o grupo que anuncia READ de conhecimento/documentação.
  - `arguments`: pedidos de conceito/documento formulam a query de discovery em torno do artefato owner (guia/documentação/tópico).
  - `grounded_synthesis`: o campo de corpo do excerto (`text`/`content`/`excerpt`) é o conteúdo substantivo; headings/seções/linhas são metadados de citação.
- `app/infrastructure/config/cri_instruction_resource.py` — allowlist de versões `{1,2,3,4}` (fail-closed preservado: v4 rejeitada pela build antiga provado live).
- `app/application/capability_provision/orchestration.py` — miss pós-consulta entra na **mesma** rodada única de recuperação (`_recover_relevance`), sob flag compartilhada, dedup de argumentos idênticos, budget, revalidação de superfície live e classe resumable (DISCOVERY/READ/ANALYSIS; PREPARE/ACT nunca).
- `app/application/capability_provision/conversational_response.py` — `_PRESENTATION_CITATION_KEYS`: coordenadas de citação (line/page ranges, chunk ids, sanitized) ordenam abaixo de campos substantivos na linha bounded — ordenação apenas, nada removido silenciosamente.
- `tests/test_c3_governed_knowledge_consumption.py` — 11 testes (consumo DAVI doc/knowledge, TÉO guias, VISTA, indisponibilidade, candidato/AuthZ, injeção, rodada única, miss→recovery, apresentação de excerto).
- `tests/test_r1_instruction_resource.py` — snapshot governado atualizado (v4 + hashes).

## 4. Avaliação com modelo real (container isolado `delia-xcap-eval`, rede interna, env prod, CRI v5, kimi-k3 via OpenRouter, auth `user`+password grant — sem impersonation)

| Cenário | Resultado | Evidência |
|---|---|---|
| D1 "o que significam MP, PI e PA no cadastro" | **GROUNDED** | `mcp:davi` → `discover` → `execute` (candidate_token) → `product_master_sb1`, excerto `text` renderizado com citação; relevância `corresponds` |
| D2 "dois exemplos de terminal bala" | insuficiência honesta | `search_products` → `irrelevant` → recovery `reinvoke` args reformulados → `irrelevant` → honesto, sem balanças |
| D3 combinada conceito+registros | **GROUNDED** | conhecimento documental e coleção empresarial separados; vazio honesto |
| T1 mapear processo sem S/I/O | **GROUNDED** | `mcp:teo.get_methodology_guide` → SIPOC (finalidade, quando usar/não usar, inputs, perguntas) |
| T2 diagnóstico de retrabalho | **GROUNDED** | guia metodológico TÉO — Ishikawa + 5 Porquês |
| T3 revisão baseline Transformômetro | **GROUNDED** | `mcp:teo.get_product_guide` |
| V1 formatos/apresentações de painéis | **GROUNDED** | `mcp:vista.get_product_guide` → índice de tópicos + catálogo de formatos (`Authority: GUIDANCE_NOT_DOMAIN_TRUTH`) |
| V2 interpretar indicadores | clarificação honesta | capability exige `topic`; `index_select=no_match` → pergunta essencial ao usuário (não inventou) |
| V3 "qual painel para este processo" | **GROUNDED** | guia de produto com limite explícito "projeção analítica — não é a verdade primária do domínio" |
| G1 padrão único/3 fontes | PASS | mesmo caminho canônico em DAVI/TÉO/VISTA, zero roteador específico |
| G2 contexto ausente | PASS | READ legítimo direto ou degradação honesta (D2/V2) |
| G3 contraditório | PASS (teste) | contrato/AuthZ prevalecem; conteúdo owner permanece untrusted |
| G4 write/malicioso | PASS | "delete produto X" recusado NON_GROUNDED, **zero invocação** |
| G5 guidance desnecessário | PASS | "liste 5 produtos" → READ direto sem consulta a guias |

Variabilidade observada (residual honesto): D1 oscilou entre `capability_unbound`/`provider_invoke` transitório e GROUNDED em execuções distintas — nondeterminismo de seleção do modelo, reduzido pelas cláusulas de seleção, não determinismo garantido.

## 5. Gates determinísticos

- Focado: `test_c3_governed_knowledge_consumption` 11/11; `test_r1_instruction_resource` 28/28; CRI E3 apresentação 94/94.
- Full backend suite: **100% PASS** (exit 0, zero falhas no run registrado).
- `audit_platform_guardrails` 0 findings; `audit_backend_boundaries` 0; `audit_architecture_phase3` OK.
- Fail-closed live: build sem a nova allowlist rejeita resource v4 no boot.

## 6. Release produtivo

- Push ff-only: `2e3cec8633..becef562b9` (origin/main verificado).
- Deploy canônico `up-prod-sequential.sh --build delia-api`, dry-run `[1/1] delia-api` — terceiros intocados.
- `PREVIOUS_IMAGE=686d745b87f6` (rollback retido) → `NEW_IMAGE=513ee033b0c6`.
- Health 200; unauth 401; **1 turno autenticado D1 em produção**: admission→`mcp:davi`→discover→execute→relevância `corresponds`→CRI com excerto `text` — `outcome_assessment=answered`. `ROLLBACK_EXECUTED=NO`.

## 7. Estado do gate pré-R4 e O2

- `MCP_DOCUMENT_ACCESS=EXPOSED_VIA_CATALOG_ACTION_READ` confirmado live (catalog action + candidate flow).
- **Dependência MP/PI resolvida na fonte:** corpus V2 (`fc9f04988c`/`293423bb`, deploy `023c53efee`) publica `mp_description_standards` — norma MP completa com `TERM.` documentado e alias `terminal bala` — e `pi_intermediate_codes`, via `corpus_version=2`.
- `O2_RESOLVED=NO` / `DAVI_O2_OUTCOME=INCONCLUSIVE`: com a norma publicada, o caminho conhecimento→reformulação existe; nas execuções observadas o modelo sequenciou busca direta e não derivou `TERM.` dentro da rodada única — resultado permanece insuficiência honesta, sem falsa pertinência. Melhoria de sequenciamento é qualidade de modelo, não nova maquinaria; hardcode `terminal→TERM.` permanece proibido.
- Auth: todo o eval e smoke usaram `user`+password grant; zero impersonation. `AUTH_METHOD_POLICY_APPROVAL` segue item do owner Keycloak/Core conforme doc 144 §7.
- `CRI_OFF_LIVE=TEST_NOT_RUN`; `REAL_TOKEN_USAGE=NOT_AVAILABLE`; latência ~11–44s/turno.
- `COORDINATION_REVIEW_REQUIRED=YES`; `R4_AUTHORIZED=NO`.
