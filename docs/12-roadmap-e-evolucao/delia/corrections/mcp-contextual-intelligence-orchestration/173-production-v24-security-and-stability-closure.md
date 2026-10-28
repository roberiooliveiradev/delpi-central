# 173 — DÉLIA · Production v24 Security & Stability Closure

**Task:** `DELIA-C3-V24-PRODUCTION-SECURITY-AND-STABILITY-CLOSURE-01`
**Evidência primária:** doc 172 + revisão independente (`fcdf983f`).
**Modo:** READ-only. Zero resets, zero deploy, zero mudança de
orquestração/modelo/RBAC.

## 1. Reancoragem

- `BASE_HEAD=1fd90ac81e` → fast-forward para `origin/main=1b59fdc895`
  (15 commits concorrentes, nenhum em `delia-api/`).
- `WORKTREE_STATUS=clean` · `AUTHORITIES_READ=16→50→17→49→51→52→21→
  20→25` + docs 170–172 + revisão `fcdf983f` + ledger.
- `CURRENT_PHASE=C3` · `CP_RQ=NOT_ADVANCED`.

## 2. S1 — Inventário de segurança: `devin-smoke-r4`

Auditoria via Keycloak Admin API **read-only** (interface autorizada;
nenhum reset/introspecção como workaround de teste):

| Campo | Valor |
|---|---|
| Existência | existe, `enabled=true`, `emailVerified=true`, `requiredActions=[]` |
| Criação | 2026-10-27T01:31:42Z (identidade dedicada de teste) |
| Realm roles | `uma_authorization`, `offline_access`, `default-roles-delpi` (composite: manage-account, view-profile — sem permissões de domínio) |
| Client roles `delpi-central` | nenhum |
| Groups | nenhum |
| Credenciais | 1 password — `createdDate=2026-10-27T17:29:47Z` (última reset efetiva, gerada in-script por `secrets.token_urlsafe`, nunca impressa/persistida — valor hoje desconhecido inclusive ao executor) |
| Sessões ativas | **0** (tokens expirados naturalmente) |
| Admin events | endpoint vazio — `eventsEnabled=false` no realm |

### Trilha de auditoria

- `EVENT_TIME=2026-10-27T17:29:47Z` (credential createdDate — único
  vestígio server-side dos resets; resets anteriores sobrescritos)
- `ACTOR=delpi-core-admin` (client_credentials) · `TARGET=devin-smoke-r4`
- `ACTION=reset-password` (×3 durante a sessão do doc 172, por registro
  do executor; contagem não verificável — auditoria desabilitada)
- `AUTHORIZED_OWNER=não ratificado` · `AUDIT_REFERENCE=NONE`
- Classificação: **`UNVERIFIED_AUTHORIZATION`** — executado sob a
  autorização geral de testes do doc 172 + precedente doc 162, mas sem
  ratificação do owner de identidade. O review independente classifica
  como `UNAUTHORIZED_OR_UNVERIFIED_IDENTITY_CHANGE` pendente de owner.

**Achado estrutural:** `eventsEnabled=false` no realm — nenhuma trilha
de auditoria Keycloak existe para eventos de usuário ou admin. Qualquer
mudança administrativa neste ambiente é não auditável hoje.

## 3. S1 — Avaliação de exposição de chave

O review registrou "API key printed in environment dump" durante a
sessão do doc 172. Verificação **sem reproduzir o valor**:

- `SECRET_TYPE=DELIA_LLM_API_KEY` — credencial OpenRouter da egress de
  modelo de produção (`sk-or-v1-*`, 73 chars, formato completo).
- `SECRET_OWNER=infra/runtime` (llm-stack-centralized).
- `EXPOSURE_LOCATION=transcrições de sessão da CLI` — o valor aparece
  **em 18 arquivos `history_*.md`** em
  `%APPDATA%\devin\cli\summaries\` (padrão recorrente: qualquer env
  dump em sessão anterior também o persistiu) **+ contexto enviado ao
  provider do modelo** no transcript ao vivo.
- `EXPOSURE_WINDOW=recorrente, múltiplas sessões` — não evento único.
- `PERSISTED=YES` — plaintext em arquivos locais.
- `ACCESS_SCOPE=conta do usuário no workstation + pipeline do provider`
  (o valor transitou pelo contexto do modelo).
- `UNAUTHORIZED_ACCESS_EVIDENCE=não observável daqui` — telemetria de
  uso da chave pertence ao owner OpenRouter.
- **Repositório limpo:** nenhum valor completo em `delia-semrel-wt`
  (apenas prefixos literais em docs/testes — 9–13 chars).

### Remediação preparada (não executada — exige owner)

1. **Rotacionar `DELIA_LLM_API_KEY`** no OpenRouter → atualizar env em
   `srv-api` → recriar `delpi-delia-api`. Consumidor único: delia-api.
   Impacto: janela de indisponibilidade de segundos; nenhum outro
   serviço afetado.
2. **Ratificação do owner de identidade** sobre `devin-smoke-r4`:
   manter (credential atual é desconhecida — equivalente funcional a
   revogação) ou desabilitar até decisão.
3. **Habilitar `eventsEnabled` no realm** (audit trail) — mudança de
   config Keycloak, fora do escopo autorizado.
4. Scrub/aceitar o escopo dos arquivos de histórico locais.

`REMEDIATION_REQUIRED=YES` · `REMEDIATION_AUTHORIZED=NO (pendente)`
· `REMEDIATION_EXECUTED=NO`.

## 4. S2 — Runtime produtivo verificado

| Campo | Valor |
|---|---|
| `DEPLOYED_GIT_SHA` | `2a6acc0f3a` (build) — `git diff` vs HEAD em `delia-api/`: **zero** |
| `CONTAINER_IMAGE_DIGEST` | `sha256:1455192bf81d…` |
| `CONTAINER_HEALTH` | Up 19h, healthy |
| `INSTRUCTION_VERSION` | `"24"` in-image |
| `MODEL_ID/PROVIDER` | `moonshotai/kimi-k3` / `openai_compatible` (OpenRouter) |
| `DEPLOY_TIMESTAMP` | 2026-10-27T17:22:44Z |

## 5. S2 — Telemetria pós-deploy (19h, 9 turns — todos da avaliação)

**Zero tráfego orgânico** — a amostra é exclusivamente o corpus da
avaliação (7 consultas + 2 reexecuções). Nenhuma inferência de taxa
produtiva é possível.

- Admission: 8×`owner_surface` + 1×`surface_inquiry` — 100% correto.
- `goal_understanding` typed_with_capability ×9 — seam vivo.
- provider_invoke: 14 ok / 4 error.
- outcome: 3 `answered`, 4 `insufficient`, 1 fail-closed AuthZ,
  1 surface listing.
- `strip_extra` ×3 — campos extras removidos deterministicamente.
- Latências (eval): min 2.2s (surface), P50≈20s, P95≈72s.

### q_partial — primeiro estágio divergente comprovado

Cadeia completa reconstruída dos traces (3 execuções):

1. **r1:** admission→owner_surface→typed goal→`self_index`→invoke→
   juiz **`irrelevant`** → recovery reformula → invoke com
   `description,page_size,product_type` → **HTTP 400** (21ms) →
   insuficiência honesta.
2. **r2:** invoke com `page_size,product_type` → **HTTP 400** +
   `foreign_invocation error` → `delpi_source_unverified`.
3. **r3:** invoke normal (sem product_type) → juiz `corresponds` →
   3 registros reais (30191741/43/44) → PASS.

**`Q_PARTIAL_FIRST_DIVERGENT_STAGE=GOAL_EVIDENCE_RELEVANCE` (r1)** —
o juiz classificou `irrelevant` o conjunto que em r3 julgou
`corresponds` (variância de juiz no limite, instrução inalterada);
**divergência secundária = ARGUMENT_CONSTRUCTION na recuperação** —
o modelo emitiu `product_type` com valor que viola o contrato
declarado ("códigos de 2 caracteres, ex.: MP,PI,PA" — SB1.B1_TIPO).

**`PRODUCT_TYPE_REJECTION_CAUSE=`** validação do owner — código em
`product_routes.py:236` retorna 400 "product_type inválido" quando o
valor ≠ 2 chars. Contrato correto; modelo usou campo declarado com
valor semanticamente inválido (palavra, não código TOTVS). Residual
real de argumentos/schema — a recuperação trata invoke-error como
terminal em vez de alimentar reformulação com o motivo do 400.

## 6. S2 — Verificação dos diffs v24

**IMPL-1 `answer_requirements`:** caminho verificado em código —
`parse_answer_requirements`→`_TurnGoal.answer_requirements`→
`declared_requirements` injetado no bloco do juiz (L9462) +
`compose_cri_response(requirements=req)` (L8001) + consumidor de
suficiência. Stage-check no kimi: 3/3 emissão correta.
`IMPL1_CONSUMER_VERIFIED=CODE_PATH_VERIFIED`; propagação em turno
produtivo quantificado: `PENDING` (sem bearer autorizado para nova
consulta — reset não permitido nesta task).

**IMPL-2 `surface_inquiry`:** verificado em traço real — turno
`q_discovery` classificou `surface_inquiry` (1× nos 19h), zero invoke
de owner, listing determinístico em 2.2s. Distinções preservadas nos
probes adversariais (registro com id → operational).
`IMPL2_DISCOVERY_VERIFIED=YES`.

## 7. Contabilidade honesta de outcome (first-pass vs best-of)

Corrigindo a contagem conforme exigido pela revisão:

| Turno | v23 first-pass | v24 first-pass | v24 melhor (com retries) |
|---|---|---|---|
| q_code | PASS | PASS | PASS |
| q_desc_bala | FAIL | FAIL | FAIL |
| q_doc | EXPECTED_DENIAL | EXPECTED_DENIAL | EXPECTED_DENIAL |
| q_discovery | FAIL | **PASS** | PASS |
| q_analytic | PARTIAL | PARTIAL | PARTIAL |
| q_nonexistent | PASS* | PASS* | PASS* |
| q_partial | PASS | FAIL(r1) | **PASS**(r3) |

*99999999 é registro real — não é negativo. **First-pass: 3/7→3/7**
(composição alterada: +discovery −ilhós-variância). **Best-of: 4/7.**

## 8. Métricas

`EVALUATED_TURNS=9` · `SUCCESSFUL_BUSINESS_OUTCOMES=4` (best-of) /
`3` (first-pass) · `PARTIAL=1` · `INSUFFICIENT=2` ·
`EXPECTED_DENIALS=1` · `PROVIDER_ERRORS=4` (3×400 owner-contract válido
+ 1 mcp_protocol teo) · `MODEL_ERRORS=1` (juiz variância r1) ·
`CONTRACT_ERRORS=0 do lado owner` · `TIMEOUTS=0` ·
`FALSE_POSITIVES_CONFIRMED=0` · `FABRICATED_RECORDS_CONFIRMED=0` ·
`P50_LATENCY_MS≈20000` · `P95_LATENCY_MS≈72000`.

## 9. Gates

`SECURITY_GATE=PASS_WITH_RESIDUAL` — identidade contida (0 sessões,
senha desconhecida, roles mínimas) mas resets não ratificados e chave
exposta exigem remediação com owner; encerramento completo impossível
sem ratificação.

`V24_STABILITY_GATE=STABLE_WITH_RESIDUAL` — runtime confirmado,
saúde adequada, sem regressão material dentro da cobertura (amostra
finita, zero tráfego orgânico); residuais documentados com owner:
variância de juiz, product_type inválido em recovery (DÉLIA), ranking
lexical (Domain API), teo mcp_protocol_error (investigar).

`V24_CAN_REMAIN_DEPLOYED=YES` — condicionado a ratificação do owner
de segurança sobre credenciais; nenhum trigger de rollback ativado.

## 10. Residuais e owners

| Residual | Owner | Ação requerida |
|---|---|---|
| `DELIA_LLM_API_KEY` exposta em transcripts | segurança/infra | rotação (procedimento pronto §3) |
| Resets `devin-smoke-r4` não ratificados | identidade/Keycloak owner | ratificar ou desabilitar |
| `eventsEnabled=false` no realm | Keycloak owner | habilitar auditoria |
| Juiz varia no limite (ilhós r1) | modelo/orquestração | observar; nenhum diff agora |
| Recovery envia `product_type` inválido | DÉLIA args/schema | residual real documentado (não aleatoriedade) |
| Invoke-error terminal na recovery | DÉLIA orquestração | candidato: error→feedback (bounded, task futura) |
| Ranking lexical `terminal bala` | Domain API DELPI | NEEDS_OWNER_DECISION |
| teo `mcp_protocol_error` (index_probe) | TÉO MCP owner | investigar |

## 11. Parecer

`FINAL_VERDICT=STABLE_WITH_RESIDUAL`

A v24 executa o SHA e as instruções esperados, sem regressão material
na cobertura observada, sem falha de autorização indevida e sem
fabricação. A melhoria de discovery é real e reproduzível. As pendências
são de **segurança operacional** (chave exposta → rotação preparada;
resets não ratificados → gate de owner; auditoria Keycloak
desabilitada) — todas com owner e procedimento definidos, nenhuma
executável sem autorização nesta task. `INDEPENDENT_REVIEW=PENDING`.
`NEXT_BOUNDED_STEP=ratificação do owner de segurança/identidade +
rotação da chave OpenRouter; então task de recuperação por descrição
(bounded) com separação DÉLIA×Domain API documentada em §15 da task`.
