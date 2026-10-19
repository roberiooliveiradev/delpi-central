# 58 — ADR: ownership da decisão semântica do LLM e execução determinística governada

**DECISION_ID:** `DELIA-ADR-C3-SEMANTIC-DECISION-OWNERSHIP-01`
**Data:** 2026-10-19
**DECISION:** `APPROVED_PRODUCT_ARCHITECTURE_DIRECTION_WITH_GATES`
**Autoridade:** aprovação expressa do Product Master para redistribuir as responsabilidades entre LLM e execução determinística existente, sem redesenho silencioso de contratos congelados.
**Baseline canônico:** `origin/main=a28368dbdce3b47a6533c047d5a05132a78ec5df` antes desta persistência; código auditado `8fc45e2119f3cc7b1b34a0f79bca144e5f822516`, `orchestration.py` 10.592 linhas.
**Evidência de entrada:** [56](./56-orchestration-audit-semantic-ownership-checkpoint.md), [57](./57-orchestration-complete-second-pass-static-audit.md), revisão de `orchestration.py`, canônicas 16→50→17→49→51→52→21→20→25, product spec 24, spec 60 MCP/A2A, ledger §6.145/§6.167/§6.299 e regras `.cursor`.
**TYPE:** decisão de responsabilidade e direção arquitetural; **não** é aprovação de diff, deploy, avanço de fase, novo port/engine/planner, nem migração imediata de contratos públicos.
**Reanchor:** GitHub main confirmado; working tree local/git status **não disponíveis por esta integração** (sem checkout); implementação posterior deverá reancorar HEAD/status via Cursor.

## 1. Problema e decisão

O `OperationalCapabilityOrchestrator` mistura decisões semânticas que deveriam ser propostas pelo LLM com validação contratual/safety, helpers de apresentação, heurísticas lexicais, estado de continuidade e execução governada. Ao corrigir cada bug por regex, cluster ou fallback temático, o sistema se torna progressivamente um interpretador de linguagem concorrente do modelo. Isto causa generalização fraca, chamadas redundantes, perdas de contexto e respostas que não cumprem a tarefa (lista em lugar de comparação).

**APROVADO:** a DÉLIA deve confiar ao LLM existente a **interpretação semântica**; a camada determinística deve ser responsável por **admissibilidade, contratos, provenance, segurança, execução e verificação de outcome**, sem reinterpretar intenções por regex/ranking lexical. Esta distribuição é um **boundary**, não ausência de guardrails.

**NÃO APROVADO:** modelo como fonte de FACT, de autorização Core/Domain, de critérios formais de safety, de escolha de endpoints/UI/provider mechanics; criação de segundo planner, novo runtime de Chat, catalogue shadow, ou livre produção de textos factuais empresariais que superem contrato de síntese aceito.

## 2. Responsibility and decision-right matrix

| Decisão/atividade | LLM DÉLIA — proposal HYPOTHESIS | Determinístico / Owner legítimo — final gate |
|---|---|---|
| Interpretar intenção, referências anafóricas, escopo, negação, quantidades, comparações | **OWNER SEMÂNTICO** do significado em contexto/instruções | Validar formato e limites da proposta; não reclassificar palavras por regex |
| Distinguir conversa geral/hipótese de necessidade de fonte corporativa | Propõe `requires_owner` ou equivalente tipado, preservando contexto | Revalidar disponibilidade e autorização; dúvida segura não promove modelo a fonte empresarial |
| Selecionar capability/grupo semanticamente apropriado | Propõe sobre catálogo vivo elegível; pode declarar não aplicável | Conferir capability live, operação READ/PREPARE/ACT, owner, contrato e autorização efetiva |
| Escolher caminho operacional mínimo suficiente, discovery/resolver/composição | Propõe plano **semântico** reutilizando mecanismo existente | Validar plano bounded, owner, edges permitidos e custo; ACT fora do plano semântico |
| Mapear intenção para argumentos (inclusive paráfrases) | Propõe argumentos tipados contra contrato e evidências | Validar JSON Schema, tipos, enums, required, identificadores com proveniência verificável e limites; bloquear valores inventados |
| Perguntar esclarecimentos | Propõe dúvida específica quando materialmente necessária | Confirmar faltas reais por contrato/evidência; não inventar código/filtro/escopo; honest fail se timeout |
| Responder de forma conceitual/ilustrativa sem provider | LLM conversa e produz hipótese rotulada | Separar hipótese de FACT, aplicar conteúdo/política; não usar owner desnecessariamente |
| Escolher registros/atributos para síntese fundamentada | Seleção/organização **dentro do contrato `selection-only` vigente** | Owner fornece FACT; projeção factual determinística copia dados e preserva provenance/limitations |
| Comparar/analisar evidência anterior | Interpreta pedido e propõe seleção, atributos, relevância e limitação | Comparabilidade por contrato/units/grain/freshness; valida diferenças e epistemic status; uma lista copiada ≠ comparação |
| Autorizar leitura, escrita, confirmação e autonomia | Pode recomendar/explicar, **nunca autorizar** | Identidade Keycloak; Core live AuthZ; Domain owner rule; Policy/Decision; PREPARE/ACT/confirm/idempotência/audit |
| Executar tool, MCP/A2A, HTTP/OpenAPI, automatização | Sugere capability semântica, não protocolos | Adapter legítimo executa e impõe scope/timeout; resultado untrusted; Domain postcondition |
| Determinar se a tarefa foi concluída | Propõe avaliação semântica do objetivo; não declara business success como FACT | Outcome/Evidence/owner confirma postcondition; test eval mede task outcome, não só HTTP 200 |
| Salvar conhecimento/memória | Sugere candidate, não publica verdade | Owner/review/eval/version/publish; memória não autoriza |
| Operação física/OT | Não controla nem autoriza | Safety industrial específica; nenhuma execução física por LLM livre |

## 3. Destino dos 42 grupos de achados das auditorias

**D1 — APROVADA a substituição de classificação semântica por texto:** S01–S13, S15, S20–S22 e F27/F32/F40 onde houver interpretação por regex, cluster fixo, ordinal, ranking de palavras ou regra `if len(groups)==1` que substitua aplicabilidade. O LLM deve decidir por contratos tipados existentes, e código somente revalidar membership, owner, schema e policy. Manter parsing sintático e redaction que não interpretam intenção.

**D2 — APROVADO eliminar qualidade artificial por extensão/contagem/replay:** S14, S16, F30/F33. Interromper `recover_empty_selection` como substituto de comparação/análise. Um fallback de listagem pode sobreviver somente para **intenção comprovada de listar/extrair** e com dados/contexto admissíveis; nunca classificar SUCCESS de tarefa por mera reprodução de bullets. Parsing de texto anterior pode ajudar UX, mas não virar evidência autoritativa.

**D3 — APROVADA a consolidação gradual de decisões/model invocations:** S22, F31/F32/F37/F38. Reusar `InvokeModel`/`_propose`, `TurnDeadline`, seleção tipada existente e `CapabilityProviderPort`. Não introduzir novo planejamento/roteamento/registry; reduzir chamadas redundantes só com medição e preservação de recall, contratos, segurança e outcome. Invocação direta duplicada de candidatos exige inventário de consumidores e RED/green antes de consolidar.

**D4 — APROVADA a revisão do caminho de indexação e args, CONDICIONAL a contratos reais:** S18/S23/S24, F29/F36. `optional unconstrained string` + `{}` schema-valid **não prova** `omit→index`. Uma descoberta de índice só deve ocorrer sob contrato explícito owner ou proposta segura que o owner suporte; sem se tornar autoridade por heurística. Remover caminho opcional comprovadamente inalcançável na config atual após inventário de consumidores. Não aumentar timeout global para esconder latência.

**D5 — REPLACEMENT_DESIGN_REQUIRED, não remover sem substituição fail-closed:** S17/S19 e F34, referente a `_free_string_grounded_in_user_input`, checagens por substring/stemming de argumentos e identificadores. Trocar afirmação falsa de provenance lexical por refs/origens verificáveis ou proposta exploratória READ declarada como **interpretação**, nunca ID/atributo factual. Se contratos existentes não suportarem refs tipados suficientes, voltar ao coordination gate `ARCHITECTURE_DECISION_REQUIRED`; não aceitar LLM self-attestation como prova.

**D6 — PRESERVAR contratos congelados até decisão separada:** S25/F26/F30/F41/F42. A decisão de `§6.145` (synthesis `items:[{record_index,fields}]`, ZERO model-authored factual prose) continua **FROZEN / NOT_SUPERSEDED**. A aprovação aqui **não autoriza** abrir canal de prosa factual livre, mesmo que uma comparação pareça textual demais. Se quiser evoluir para modelo que redige com citações tipadas, criar ADR específico com invariantes, ameaça, provas negativas, fallback, generalização e aceite do Product Master. Comparação `context_fields` vazio versus gate determinístico exige reconciliação explícita com owner e contrato, sem relaxar proteção silenciosamente.

**D7 — RELOCATION_ONLY_AFTER_REUSE_GATE:** funções de projection/rendering, guidance key aliasing, personal ticket scope/pagination and owner response normalization (F27/F28/F39 e candidatos listados em 56/57). Não criar novos serviços locais por conveniência; se houver owner/formato/renderer legítimo reutilizável, adaptar por boundary. Manter contagem exata, páginas versus total, identidade delegada, suspensão fail-closed, redaction e source limitations.

**D8 — PRESERVE_UNCHANGED_BY_THIS_ADR:** Core/domain permissions and delegated AuthN, provider live discovery, MCP/A2A untrusted boundary, schema validation, PREPARE/ACT split, idempotency, explicit confirmation, auditable hashes/handles, postconditions, true Evidence/Outcome, TurnDeadline, data minimization, credentials protection, OT/safety constraints. No categorical removal of `re.compile`: credentials/JWT/format sanitization regexes are legitimate.

## 4. Reuse and abstraction gate

| Boundary | EXISTING_EQUIVALENT | REUSE_DECISION | Rule |
|---|---|---|---|
| Semantic goal/selection | YES — `InvokeModel`, `_propose`, existing goal/capability typed proposals | **EXTEND** (consolidate in place) | Do not create a new planner or classifier engine |
| Provider interop | YES — `CapabilityProviderPort` + current adapters | **REUSE** | No DAVI/TÉO/VISTA/HTTP special case |
| Deadline/telemetry | YES — `TurnDeadline` + logs/activity | **REUSE** | 30s global stays unchanged |
| Evidence/Outcome | YES — DÉLIA evidence + authoritative owner results | **EXTEND ONLY IF CONTRACT LEGITIMATE** | Not provenance from response text |
| Precise typed argument provenance | TO_INVENTORY for required representation and consumer | **PENDING** | No new DTO/port until owner/contract/reuse proven |
| Rich factual prose synthesis | EXISTING CONTRACT=YES, selection-only FROZEN | **PRESERVE**, not superseded | Separate Product Master ADR required |

## 5. Mandatory execution gates and measurable acceptance

This ADR approves **architecture direction only**. For every bounded implementation step: live `git status/HEAD/origin/main`; canonical reanchor `.cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → technical architecture → 24 product spec → 60 thematic applicable → ledger`; enumerate code consumers and tests. Prove `EXISTING_EQUIVALENT`/`REUSE_DECISION`. RED test old failure, smallest correct diff, full backend tests, independent code diff review, safe rollback.

**Evaluations cross provider and no provider**:
- DAVI: catalog/discovery, registered products, follow-up subset, field-grounded comparison, owner no-match;
- TÉO: methodology orientation, multi-turn guidance, GLPI personal count only with authentic DÉLIA-linked subject (else TEST_NOT_RUN);
- VISTA: formats, dashboard guidance/discovery, follow-up and C02 budget regression;
- legitimate OpenAPI/HTTP **non-MCP** and renamed equivalent semantic provider;
- conversation without owner/tool: greetings, SIPOC, hypothetical examples, changing topic, follow-up explanations;
- adversarial: injected tool descriptions, invented IDs/sensitive qualifiers, word-overlap false provenance, prompt injection, provider outages, pagination/total, schema errors, read/write confusion, compare-vs-list, prior false FACT, concurrent requests and timeouts.

**Outcome ACs:** (1) goal interpretation generalizes across paraphrases/number context and owners; (2) no regex/keyword owner-intent veto; (3) typed valid and source-grounded args; (4) no extra permission from model/context/MCP; (5) selected capability exists live; (6) task-specific comparison vs list verified; (7) no 504 for bounded reference turns, strict global 30s; (8) realistic negative/holdout and repeated cold/warm samples; (9) provider-neutral same semantics MCP/non-MCP; (10) no-tool conversation works; (11) material ACT=0 for read/nonwrite scenarios; (12) no invented business FACT or leaked secrets; (13) regression suite incl. C3 I01-I04, R1–R5 and SEMARG; (14) evaluated SHA/config and owner outcomes recorded. Independent live SSH eval not performed for this ADR.

## 6. Alternatives and consequences

- **Reject**: one more regex/fallback per failure, which accumulates implicit language engine and couples to known phrases.
- **Reject**: "LLM decides everything", which would silently dissolve Core/Domain authority, material-write gates and evidence.
- **Reject**: a second general-purpose planner, external agent runtime or generic provider catalog mirror.
- **Approve**: fewer semantic decisions, reuse existing typed proposal contract, strong deterministic governable boundaries; tradeoff is explicit typed semantic/context contracts and high-quality evals rather than rapid string patches.

**Rollback/migration:** no runtime code change in this ADR. Future bounded refactors must be reversible, deployed with SHA/config and compared to existing accepted behaviors, with owner write gates and phase frozen.

## 7. Binding decision and stop-lines

```text
DECISION_ID=DELIA-ADR-C3-SEMANTIC-DECISION-OWNERSHIP-01
ARCHITECTURE_DIRECTION=APPROVED
LLM_SEMANTIC_DECISION_OWNERSHIP=APPROVED_HYPOTHESIS_WITH_TYPED_CONTRACTS
DETERMINISTIC_EXECUTION_POLICY_AND_AUTHORITY=REQUIRED_UNCHANGED
REUSE_EXISTING_ORCHESTRATOR=MANDATORY
NEW_PLANNER_OR_ENGINE=NOT_AUTHORIZED
PROVIDER_NAME_BRANCHES=FORBIDDEN
LEXICAL_INTENT_DECISION_ENGINE=DEPRECATED_AS_TARGET
SELECTION_ONLY_GROUNDED_SYNTHESIS=FROZEN_PRESERVED
MODEL_AUTHORED_BUSINESS_FACTS=FORBIDDEN
TYPED_PROVENANCE_CHANGE=ARCHITECTURE_DECISION_REQUIRED_IF_CONTRACT_NEW
RICH_FACTUAL_PROSE=SEPARATE_ADR_REQUIRED
DELETION_OR_CODE_REWORK_AUTO_AUTHORIZATION=NO
RUNTIME_DIFF=NONE
REGRESSION_TESTS=TEST_NOT_RUN
LIVE_PRODUCTION_EVAL=TEST_NOT_RUN
I04_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT=BOUNDED_SEMANTIC_INTERPRETATION_CONSOLIDATION_EXECUTION_BRIEF_AFTER_CONSUMER_CONTRACT_INVENTORY
```

This decision **supersedes no frozen contract**; documents 56/57 remain the audit baseline, not a mass-delete list. A later architecture or runtime conflict invokes STOP → `EXECUTION_DRIFT` or `ARCHITECTURE_DECISION_REQUIRED` instead of silent redesign.
