# X4.S2 — Federated Deploy & Runtime Acceptance (2026-10-22)

> Verificação de produção da interface de enriquecimento cadastral (E14 `#enrichment`).
> Sem rebuild: o bundle produtivo já continha X4.S1.R1.

## 1. Baseline e deploy

| Item | Valor |
|---|---|
| Repo HEAD local | `a80caff8a9` (limpo) |
| `origin/main` | `b19c47d443`+ (avançou — concorrente) |
| X4.S1.R1 `a80caff8a9` ∈ origin/main | **YES** |
| Prod checkout | `c0b61d365` (`/home/operador/projetos/delpi-central`, limpo) |
| X4.S1.R1 ∈ prod checkout | **YES** |
| Imagem `delpi-supplies` | `sha256:7679f33853a3`, built 2026-10-22T21:01:45Z |
| Bundle servido | `assets/App-D6r9DFTy.js` (251 KB) via gateway público |
| remoteEntry público | `200 application/javascript` |

**Marcadores no bundle servido publicamente** (`App-D6r9DFTy.js`):
`enrichment-reviews`, `kind:"prepare"` (invariante R1), `Enriquecimento cadastral`,
`Nenhum dado foi gravado no Protheus` — **X4.S1.R1 presente**.

**Deploy: NÃO EXECUTADO — desnecessário.** Imagem já reconstruída após o push de R1
(checkout+imagem+ bundle coerentes). Redeploy seria churn sem ganho.

## 2. Backend health (GATE D5)

| Serviço | Estado |
|---|---|
| supplies-api | healthy; `{"service":"supplies-api","status":"ok"}` via gateway |
| api-delpi | healthy; `{"status":"online"}` |
| external-data-api | healthy (healthcheck exit 0) |
| delpi-redis | healthy |
| delpi-postgres-plugins | healthy; schema `supplies` em `plugins_hub`, migrations **V001/V002/V003** |
| Keycloak (`infra-keycloak-1`) | up; realm `delpi`, grant password funcional |
| core-api | up (sem healthcheck definido) |
| portal / gateway | up 28h/30h |

Config efetiva supplies-api (valores não-secretos):
`COMPANY_REGISTRY_PROVIDER=external-data-api`, `EXTERNAL_DATA_CNPJ_PROVIDER=brasilapi`,
`EXTERNAL_DATA_API_BASE_URL=http://external-data-api:8000`, rate limit `distributed`,
`S2S_CLIENT_ID=supplies-api`, `S2S_AUDIENCE=api-delpi`,
`S2S_ALLOWED_CLIENTS=supplies-api,controllership-finance-api`.

## 3. Smoke funcional real (GATE D6) — usuário `rober`, fornecedor `002469/01`

Review criada para o smoke: `1989ff2c-1e15-4599-bed3-d8ce3123e16b`
(`IN_REVIEW`, source `brasilapi-cnpj-v1`, retrieved 2026-10-22T21:25:32Z).

| Verificação | Resultado |
|---|---|
| Sem token | **401** |
| Supplier detail via BFF | `supplier_code/store/tax_id/sections` — SA2 canônico |
| POST review (BrasilAPI real) | **16 propostas**; comparison {PROTECTED:1, DIFFERENT:3, SOURCE_MISSING:5, MATCH:3, CURRENT_MISSING:4}; eligibility {ELIGIBLE:2, PROTECTED:1, N/A:12, PENDING_VALIDATION:1}; todas `PENDING` |
| Campos proibidos | nenhum qsa/cpf/partner nos `field_key` |
| ACCEPT `supplier_name` | rev 1→2, `ACCEPTED_FOR_DRAFT` |
| REJECT `tax_id` (protegido, pendente) | rev 2→3, `REJECTED_SUGGESTION` |
| Bulk REJECT `address,area_code,city` + `reason_code=SMOKE_X4S2` | rev 3→4 atômico |
| Decisions trail | 5 decisões, actor=`3bfdd634…` (rober), `review_revision` correto |
| prepare-update | `write_gate_enabled=false`, `baseline_status=CURRENT`, `draft_fields=[supplier_name]` — **draft-only** |
| Histórico | `total=2`; revisão do smoke + revisão anterior `d3b65302` (DECIDED) preservadas |

**Comparação real Protheus×BrasilAPI** (evidência AC-12): `postal_code`
`89120000 → 89093880` divergente/elegível; `supplier_name` divergente;
`state/district/city` MATCH; `tax_id` PROTECTED com `current/suggested=None`
(mascaramento confirmado).

## 4. Idempotência e concorrência (GATE D7) — runtime

| Cenário | Resultado |
|---|---|
| Replay idêntico (single) | `idempotent_replay=true`, rev inalterada, **zero duplicação** |
| Replay idêntico (bulk) | `idempotent_replay=true`, rev 4 estável |
| Mesma chave + payload divergente | **409 `ENRICHMENT_IDEMPOTENCY_CONFLICT`** |
| `expected_revision` stale | **409 `ENRICHMENT_REVISION_CONFLICT`** |
| 429/Retry-After | header propagado ao frontend (`ApiRequestError.retryAfter`, X4.S1); não exercitado contra BrasilAPI produtiva (proibido gerar rate-limit artificial) — `TEST_NOT_RUN` |

A correção X4.S1.R1 é de frontend (captura imutável); o backend prova a semântica
do contrato que ela protege.

## 5. Segurança (GATE D9) — bundle público inspecionado

- `App-D6r9DFTy.js`: **zero** `api-delpi`, **zero** `brasilapi.com.br`, **zero**
  `client_secret`/`Service-Authorization`/`s2s_` → MFE é BFF-only.
- Propostas protegidas não expõem valor (`current/suggested=None` no PROTECTED).
- Ownership: decisions trail só mostra ator da própria revisão.
- Zero POST/PUT ERP executado (somente endpoints `/enrichment-reviews*`).

## 6. Rollback readiness (GATE D3)

- Imagem anterior não sobrescrita por esta task (deploy dispensado).
- Rollback do MFE: `git checkout <SHA anterior>` + `up-prod-sequential.sh --build supplies`
  (procedimento oficial); dados S2 persistidos não dependem do bundle.
- Sem migrations alteradas → rollback não destrutivo garantido.

## 7. Resultado

| Gate | Status |
|---|---|
| D1 inventário | PASS |
| D2 commit/push | PASS — NOTHING TO PUSH |
| D3 backup/rollback | PASS (readiness; nada a reverter) |
| D4 deploy | DISPENSADO — bundle já contém X4.S1.R1 |
| D5 backend | PASS (7/7 serviços) |
| D6 smoke API | PASS — revisão/decisões/draft persistidos |
| D7 idempotência | PASS (exceto 429: `TEST_NOT_RUN` por política) |
| D8 visual | **INCONCLUSIVE** — sem ferramenta de browser; bundle verificado, render real não executado |
| D9 segurança | PASS |
| D10 pós-condição | PASS — serviços alheios preservados, uptime inalterado |

**AC:** 01–17, 23–26 `PASS`/`PROVEN` · AC-18–22 (desktop/mobile/tema/teclado/help visual) `INCONCLUSIVE`.

**Residuais:** (1) smoke visual federado pendente de sessão de browser;
(2) ROPA formal → DPO; (3) otimização de chunk >500 kB (warning pré-existente).

**Conclusão: `ACCEPT_WITH_RESIDUAL`** — backend/frontend verificados em produção
via API e bundle; residual = evidência visual interativa.
