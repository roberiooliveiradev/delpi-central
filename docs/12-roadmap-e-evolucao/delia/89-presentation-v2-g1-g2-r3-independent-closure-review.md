# 89 — Independent Closure Review — Markdown B2 G1/G2 R3

**Status:** `INDEPENDENT_VERDICT=ACCEPT_WITH_RESIDUAL`  
**Task:** `DELIA-UX-CONVERSATION-MARKDOWN-B2-G1-G2-R3-INDEPENDENT-CLOSURE-01`  
**Reviewed delivery:** `444e03d7d2e1502c922d015d319f63cd3612a283` (R3 executor)  
**BASE_HEAD / REVIEWED_SHA (reanchor):** `08f0bd104161106c09e0ec74ce7ebd6978993543` (= `origin/main` no início da revisão)  
**CP:** `CP-333` — permanece `PLANNED_NOT_PASS`  
**Tipo:** revisão independente (código + testes + SSH read-only + docs). **Sem** novo deploy. **Sem** implementação de `presentation.v2` / `ConversationMarkdown` / links navegáveis.

> Trilha Markdown B2 / CP-333 ≠ `C3-STAGE-02-B2` (PREPARE/ACT). O commit posterior `08f0bd1041` (Stage 02 live SSH evidence, doc 26) **não** altera o sanitizer nem os contratos B2.

## 1. Reanchor

| Check | Resultado |
|---|---|
| Branch | `main` |
| `444e03d7d2` ancestral de `origin/main` | YES |
| Commits posteriores a R3 | 1 — Stage 02 docs only (`08f0bd1041`) |
| Diff R3→HEAD em sanitizer/testes B2 | EMPTY — sem EXECUTION_DRIFT |
| WIP concorrente | `transformometro-api/*` modificado — **preservado**, fora do stage |

Authorities lidas (mínimo material): protocolo DÉLIA, docs 16/20/25/82–88, schema proposal, ledger §6.192–§6.198, owner `capability_provision/orchestration.py`, `presentation.ts` v1, `mural_acessos/link_url.py`, `_TRANSPORT_FORBIDDEN`.

## 2. Escopo do commit R3

Arquivos do commit (confirmados via `git show`):

| Path | Classificação |
|---|---|
| `delia-api/.../orchestration.py` | `IN_SCOPE` — +`"token"` |
| `tests/test_render_specialist_outcome_fidelity.py` | `IN_SCOPE` |
| `tests/test_specialist_capability_orchestration.py` | `IN_SCOPE` |
| `tests/test_presentation_v2_proposal.py` | `IN_SCOPE` |
| docs 20/83/84/87/88 + ledger | `IN_SCOPE` |
| Runtime Markdown / Domain API / Portal / AuthZ / ACT | **ausente** |

Diff runtime mínimo: **1 linha** no frozenset canônico. Sem componente Markdown novo. Sem mudança de Policy/Core/ACT.

## 3. R3-01 — Segurança `token`

```text
R3_01_TOKEN_FIX: CONFIRMED — "token" ∈ _SENSITIVE_KEY_NAMES (L1863 HEAD)
R3_01_OWNER_CONFIRMED: capability_provision/orchestration.py (único _SENSITIVE_KEY_NAMES)
R3_01_RED_GREEN_EVIDENCE: test_bare_token_key_is_redacted PASS (0 xfail) em 08f0bd1041
R3_01_NESTED_CASES: PASS (sanitize nested list + render_specialist_outcome e2e)
R3_01_BUSINESS_DATA_PRESERVED: PASS (token_count / token_value / IDs / qtd / un)
R3_01_REGRESSION: access_token/refresh_token/client_secret/password + restantes intactos
R3_01_VERDICT: ACCEPT
```

Normalização: `_canonical_key` = lower + strip non-alnum → `Token`/`TOKEN` cobertos; matching **exato** (não substring) preserva `token_count`/`token_value`. Consumers: `_sanitize_renderable` → `render_specialist_outcome` e demais call-sites no mesmo módulo. Sem sanitizador paralelo.

## 4. R3-02 — Link L1

```text
R3_02_L1_DECISION: PRESERVED — L1_APPROVED_CONDITIONAL
R3_02_OWNER_CONTRACT: mural_acessos.normalize_link_url = CONTRACT_REAL (api-delpi)
R3_02_BINDING_EVIDENCE: ZERO em delia-api (rg mural_acessos = 0 hits)
R3_02_AUTHZ: Core/Domain no destino; link ≠ permission
R3_02_NAVIGATION: política documentada; emissão BLOCKED
R3_02_UNTRUSTED_URL_GUARD: _TRANSPORT_FORBIDDEN inclui "url"; SourceRef/EntityRef URL-free
R3_02_VERDICT: ACCEPT (estado TO_INVENTORY é correto — não fabricar binding)
```

```text
LINK_L1_CONTRACT = SPECIFIED
LINK_L1_CAPABILITY_BINDINGS = TO_INVENTORY
NAVIGABLE_LINK_EMISSION = BLOCKED
```

## 5. R3-03 — Fallback

```text
R3_03_SCHEMA_CONSISTENCY: PASS — §2.5 ≡ §2.9 ≡ §6 (sem “fallback legado” residual)
R3_03_UNKNOWN_VERSION: render_legacy se legado seguro; senão neutral_error
R3_03_INVALID_V2: neutral_error (incl. additionalProperties)
R3_03_INERT_FALLBACK: admitted markdown_safe parse fail → inert_text
R3_03_NEUTRAL_ERROR: schema-reject / legado inseguro
R3_03_LEGACY_VALIDATION: content string bounded antes de render_legacy
R3_03_VERDICT: ACCEPT
```

Probe independente: `extra_prop_policy=neutral_error` (jsonschema + `resolve_presentation`). Runtime `parsePresentation` permanece v1-only — **não** ativado.

## 6. G1 / G2 (contrato e reuse)

| Dimensão | Veredito |
|---|---|
| Envelope/discriminator/bounds/schema proposal | Suficiente para brief futuro **textual** |
| Producer seam | EXTEND `render_specialist_outcome` — correto |
| Links navegáveis | **Bloqueados** por L1 bindings |
| Reuse `marked.lexer` | REUSE justificado (probes ≠ renderer PASS) |
| NEW `ConversationMarkdown` | Ainda **proposta**; não implementado |
| Threat model / allowlist | Design aceito; segurança do renderer = `TEST_NOT_RUN` |

```text
G1_CONTRACT_VERDICT: ACCEPT_WITH_RESIDUAL
G2_SECURITY_REUSE_VERDICT: ACCEPT_WITH_RESIDUAL
G3_READINESS: BLOCKED
```

Aceitar G1/G2 como **candidatos revisados** ≠ autorizar G3/runtime B2 ≠ marcar CP-333 PASS.

## 7. Testes (reexecução independente — SHA `08f0bd1041`)

| Suíte | Resultado |
|---|---|
| Targeted (fidelity+proposal+orchestration+presentation) | **151 PASS**, 0 xfail/xpass/skip |
| `test_bare_token_key_is_redacted` | **1 PASS** |
| Full `delia-api` | **1178 PASS** |
| jsonschema 4.26.0 Draft 2020-12 (venv isolado) | draft OK; 4/4 + 17/17; extra→`neutral_error` |
| plugin-ui markdown+rich-text | **175/175 PASS** |
| plugins/delia vitest | **191/191 PASS** |
| tsc delia | CLEAN |
| tsc plugin-ui | **31 errors** — paths fora do diff R3 (`visualComponents`, layout, charts, …); baseline debt, não atribuída a R3 sem evidência de introdução |
| Build / Federation | `TEST_NOT_RUN` |

Python 3.12.3 / pytest 8.3.4 (`delia-api/.venv`).

## 8. SSH (read-only — sem redeploy)

```text
SSH_TARGET: operador@192.168.1.237 (srv-api)
SSH_ACCESS: PASS (BatchMode)
REMOTE_CHECKOUT_SHA: 08f0bd104161106c09e0ec74ce7ebd6978993543
REMOTE_WORKTREE_STATUS: clean vs origin/main
DEPLOYED_IMAGE_ID: sha256:d149abbdebb014b5f69921fa78d136ea4abe387aaeed8763ea7d86f2a26b25ab
DEPLOYED_BUILD_SHA: NOT_LABELED (compose labels sem git SHA)
RUNNING_CONTAINER_ID: a9a1321777e8… (delpi-delia-api)
CONTAINER_HEALTH: healthy
GATEWAY_HEALTH: /apps/delia-api/health → 200
SANITIZER_CODE_PRESENT: YES ("token" L1863 disk + MODULE_FILE=/app/.../orchestration.py)
RUNTIME_TOKEN_REDACTION: PASS (fixture SYNTH-*; nested; render_specialist_outcome)
RUNTIME_BUSINESS_VALUE_PRESERVATION: PASS (token_count/token_value/op)
DEPLOYMENT_PROVENANCE: CORRELATED_INCOMPLETE — Image.Created 2026-10-16T20:14:30Z alinha ao deploy R3 (~R3_COMMIT 20:14:08Z); checkout avançou docs Stage02 depois; comportamento no container prova o fix; ausência de label git SHA impede prova criptográfica IMAGE↔SHA
SSH_VERDICT: ACCEPT_WITH_RESIDUAL
```

HTTP 200 ≠ business outcome; usado só como health.

## 9. Residual search

Escopos: `delia-api/app`, `delia-api/tests`, `plugins/delia/src`, `plugins/plugin-ui/src/components/markdown`, docs 83/84, `argument_validator._TRANSPORT_FORBIDDEN`.

| Achado | Avaliação |
|---|---|
| Único `_SENSITIVE_KEY_NAMES` | OK |
| Sem `xfail` ativo em `test_bare_token_key_is_redacted` | OK |
| Docs 86/87 históricos mencionam RED pré-fix | OK (histórico) |
| `PRESENTATION_CONTRACT_VERSION="1"` | OK — v2 não ativado |
| `ConversationMarkdown` só em probe proposal | OK |
| Fallback “legado” inconsistente em 84 | NONE |
| Bypass AuthZ/Domain | NONE no diff R3 |

## 10. Veredito

```text
R3_SECURITY_FIX_VERDICT: ACCEPT
R3_TEST_EVIDENCE_VERDICT: ACCEPT
R3_SSH_DEPLOY_VERDICT: ACCEPT_WITH_RESIDUAL

G1_CONTRACT_VERDICT: ACCEPT_WITH_RESIDUAL
G2_SECURITY_REUSE_VERDICT: ACCEPT_WITH_RESIDUAL

LINK_L1_BINDING_STATUS: TO_INVENTORY
G3_READINESS: BLOCKED
CP_333_STATUS: PLANNED_NOT_PASS
PHASE_STATUS: C3_EXECUTED=NO; C4=NO; C5=NO; PHASE_PROGRESSION=NONE

INDEPENDENT_VERDICT: ACCEPT_WITH_RESIDUAL
```

### Separação explícita

| Estado | Valor |
|---|---|
| R3 security fix accepted | **YES** |
| G1/G2 contract readiness (candidate reviewed) | **YES, com residual L1/renderer** |
| G3 implementation authorization | **NO** |

## 11. Próximo bounded

`DELIA-UX-CONVERSATION-MARKDOWN-B2-L1-BINDING-INVENTORY-01`

Inventariar owner → capability → `structured` → campo tipado publicado → admissão DÉLIA → política de link. **Não** emitir links só porque existe campo `url`.

G3 brief (`…-G3-BRIEF-01`) permanece **bloqueado** até bindings L1 comprovados (ou decisão explícita de Product Master restringindo o primeiro slice sem links — **não** tomada aqui).

## 12. Documentação desta revisão

- Este doc 89 (novo).
- Spec 83 §0.6 — estado pós-review.
- Matriz 20 — linhas G1/G2.
- Ledger §6.199.
- Doc 16 — nota no slice Markdown B2 (NEXT bounded da trilha; sem mudança do NEXT global da fase).
- 85/86/87/88 preservados como histórico.
