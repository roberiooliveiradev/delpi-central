# Supplier Enrichment — Company Registry Provider Inventory & Contract Freeze (S3)

Status: `CONTRACT_FREEZE = INCONCLUSIVE` — provider technically identified and
documented, but DELPI entitlement is not yet proven.

Scope: inventory, official-source evaluation, adapter design, offline contract
planning. No productive adapter, no live calls, no credentials.

Sources accessed on this execution (official only):

- Serpro commercial channel docs: <https://apicenter.estaleiro.serpro.gov.br/documentacao/consulta-cnpj/pt/>
- Serpro contracting page: <https://apicenter.estaleiro.serpro.gov.br/documentacao/consulta-cnpj/pt/como_contratar/>
- Serpro auth quick-start: <https://apicenter.estaleiro.serpro.gov.br/documentacao/consulta-cnpj/pt/quick_start/>
- Serpro V2 field dictionary: <https://apicenter.estaleiro.serpro.gov.br/documentacao/consulta-cnpj/pt/descricao_campos_v2/>
- Serpro return codes: <https://apicenter.estaleiro.serpro.gov.br/documentacao/consulta-cnpj/pt/codigos_retorno/>
- Serpro request identifier: <https://apicenter.estaleiro.serpro.gov.br/documentacao/consulta-cnpj/pt/identificador_requisicoes/>
- Conecta gov.br catalog: <https://www.gov.br/conecta/catalogo/apis/consulta-cnpj>
- Receita Federal open data: <https://dadosabertos.rfb.gov.br/CNPJ/>

---

## 1. EXISTING PROVIDERS INVENTORY (P0)

Monorepo-wide search for CNPJ/registry integrations
(`serpro|receita|conecta|redesim|company registry|cnpja|receitaws|brasilapi`,
plus concept-level search for registry lookups and env references):

| Finding | Location | Status |
|---|---|---|
| CNPJ lookup client/adapter | none — `supplies-api` provider port is fail-closed | `PROVEN` (absent) |
| External data providers | `api-delpi` INT-CEP-01: ViaCEP + BrasilAPI postal lookup (`POSTAL_ADDRESS_*` env) | `PROVEN` — postal only, unauthenticated public APIs, **not** a company-registry precedent to copy credentials-wise, but a valid fail-closed/timeout precedent |
| CNPJ fields in SA2/commercial domain | Protheus reads only (`api-delpi`, commercial-api) | `PROVEN` — no external lookup |
| Secrets/env for registry provider | none found | `TO_INVENTORY` — a contract could exist outside the repo; finance/procurement confirmation required |
| `CompanyRegistryProvider` port | `supplies-api/app/application/services/supplier_enrichment/contracts.py` | `PROVEN` — port exists, production adapter `UnavailableCompanyRegistryProvider` stays fail-closed |

Search miss does not prove absence of a commercial contract; no technical
evidence of one exists in the codebase or configuration.

---

## 2. COMPANY_REGISTRY_PROVIDER_MATRIX (P1)

| Provider | Owner | Legal eligibility | DELPI entitlement | Contract | Authentication | API version | Coverage | Freshness | Cost model | SLA | Retention rules | Provenance | Technical readiness | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Serpro Consulta CNPJ (commercial)** | Serpro | Private companies of any size contractable; e-CNPJ required for online contracting (manual path exists) | `TO_INVENTORY` — no contract evidence | Identified product; DELPI contract not proven | OAuth2 client credentials: `POST https://gateway.apisrpro.serpro.gov.br/token`, Basic base64(consumerKey:consumerSecret), Bearer 1h | V2 documented (`consulta-cnpj-df-v2`) | 3 modalities: Básica / QSA / Empresa | RFB base via REDESIM juntas, "updated in minutes" (official FAQ) | Per-request billing; trial/demo unbilled; 400/401/403/500/502/504 unbilled | Not published in public docs | Contract terms govern; not public | Government source (RFB), response fields documented | High — doc complete, demo env exists | **Candidate — ACCESS `TO_INVENTORY`** |
| **Conecta gov.br Consulta CNPJ** | RFB/Serpro via Conecta | Federal public administration only (Portaria RFB 1384/2016) | **Not eligible** — DELPI is a private company | N/A | OAuth2 jwt-token + IP firewall registration | V2 (api-cnpj-basica/qsa/empresa) | Same field family | Same RFB base | Free | Gov-to-gov | N/A | Government | N/A for DELPI | **REJECTED — ineligible** |
| **REDESIM public query** | Juntas Comerciais | Human/browser use | N/A | None | None | N/A | Public company data | Registry-level | Free | None | UI terms | Weak (no evidence payload) | Not a documented API; scraping/automation not authorized | **REJECTED — not an API contract** |
| **Receita open data (dados abertos)** | RFB | Public download | Usable | Open distribution | None | Dump schema | Full CNPJ base, all fields public | Monthly dumps (batch, not transactional) | Free | Best-effort | Public domain per RFB | Government dataset | Heavy: requires local mirror/ETL, no real-time lookup | `PLANNED` — viable batch alternative, not for online UX |
| Third-party mirrors (BrasilAPI CNPJ, ReceitaWS, CNPJA etc.) | Community vendors | Public | Available w/o contract | None | None/token | Varies | CNPJ fields (usually open-data derived) | Lag behind open data dumps | Free tiers | No SLA | Unclear | **No** provenance guarantee — cannot support `source_type=GOVERNMENT_API` claims | Easy HTTP | **REJECTED for provenance purposes** — may serve dev fixtures only |

**Provider selection:** Serpro Consulta CNPJ (commercial, modality **Básica**
sufficient for the S1 field set; QSA/Empresa excluded from MVP — QSA carries
partner CPF/personal data outside LGPD scope decision).

**GATE-PROVIDER-ACCESS = `TO_INVENTORY`** — no evidence of DELPI contracting.
STOP for live tests and productive adapter (S3.1 requires formal contracting or
trial keys + e-CNPJ).

---

## 3. COMPANY_REGISTRY_PROVIDER_TECHNICAL_CONTRACT (P2)

Documented from official Serpro V2 docs (commercial channel). `PROVEN` for
documentation; runtime behavior `TO_INVENTORY` until contract.

### Authentication

- `POST https://gateway.apisrpro.serpro.gov.br/token`
- `Authorization: Basic base64(consumer_key:consumer_secret)`, `Content-Type: application/x-www-form-urlencoded`, body `grant_type=client_credentials`
- Bearer token, **1-hour expiry** — server-side lifecycle (cache + refresh), never exposed to the browser.
- Consumer key/secret issued per contract in `cliente.serpro.gov.br`.

### Request

- Method: `GET` on the contracted gateway (`gateway.apisrpro.serpro.gov.br`, base per `consulta-cnpj-df-v2` swagger — exact path segments are defined in the contract's swagger, TO_VERIFY at contract time).
- Path param: CNPJ (14 digits).
- Header: `Authorization: Bearer <token>`; optional **`X-Request-Tag`** (string ≤ 32 chars, free-form) — billing-grouping identifier; designated carrier of the correlation/evidence tag.
- Demo environment exists: simulated data, unbilled, separate trial credentials.
- "Carimbo de tempo" (timestamp-based requests) documented for incremental/dated queries — evaluate at contract time for freshness evidence.

### Response (V2, Básica modality)

Top-level groups (all fields in Básica unless noted):

- `ni` — CNPJ registration number (identity; must equal queried CNPJ)
- `tipoEstabelecimento`, `nomeEmpresarial`, `nomeFantasia`
- `situacaoCadastral {codigo, data, motivo}`
- `naturezaJuridica {codigo, descricao}`, `dataAbertura` (AAAA-MM-DD)
- `cnaePrincipal {codigo, descricao}`
- `endereco {tipoLogradouro, logradouro, numero, complemento, cep, bairro, municipio{codigo,descricao}, municipioJurisdicao{codigo,descricao}, uf, pais{codigo,descricao}}`
- `telefone[] {ddd, numero}` (multiple occurrences)
- `correioEletronico`
- `capitalSocial` (integer, cents), `porte`, `situacaoEspecial`, `dataSituacaoEspecial`
- QSA/Empresa only: `informacoesAdicionais`, `socios[]` (names, qualifications; **CPF only in Empresa**)

Note: naturezaJuridica `213-5` (Empresário Individual) suppresses `socios` fields
per official docs — a partial-response shape that must be tolerated.

### Error contract (documented)

| HTTP | Meaning | Billed |
|---|---|---|
| 200 | Full response | yes |
| 206 | Partial content | yes |
| 400 | Invalid CNPJ | no |
| 401 | Authentication failure | no |
| 403 | Denied (permission/endpoint/version/contract e.g. default) | no |
| 404 | CNPJ not found | — |
| 500/502 | Provider internal/integration error | no |
| 504 | Gateway timeout | no |

Timeouts, retry policy and quotas: not published → S3.1 defaults must come from
`http-integration-resilience` (bounded retries on 5xx/timeout only, never on
4xx; circuit breaker recommended since billing applies per call).

---

## 4. COMPANY_REGISTRY_FIELD_MAPPING (P3)

Confrontation of the official V2 schema with `CNPJ_SA2_MAPPING_V1` (S1). No
mapping spec changed — this is provider-side projection only.

| Provider path (V2) | Normalized field | SA2 target | Comparability | Eligibility | Notes |
|---|---|---|---|---|---|
| `ni` | `tax_id` | A2_CGC | PROTECTED | never applies | Identity check — **must** equal queried CNPJ else `CNPJ_DIVERGENT` |
| `nomeEmpresarial` | `supplier_name` | A2_NOME | COMPARABLE | ELIGIBLE candidates | SX3 length limit enforced by S1 engine |
| `nomeFantasia` | `short_name` | A2_NREDUZ | COMPARABLE | pending equivalence rule | S1 already flags `equivalence_rule_pending` — fantasia ≠ reduced name automatically |
| `endereco.tipoLogradouro` + `endereco.logradouro` | `address` | A2_END | COMPARABLE | ELIGIBLE candidates | Concatenation rule to be fixed in S3.1 normalization contract |
| `endereco.numero`, `endereco.complemento` | address parts | (composed) | COMPARABLE | part of `address` | See above |
| `endereco.bairro` | `district` | A2_BAIRRO | COMPARABLE | ELIGIBLE candidates | — |
| `endereco.cep` | `postal_code` | A2_CEP | COMPARABLE | ELIGIBLE candidates | Normalize to 8 digits |
| `endereco.municipio.descricao` + `endereco.uf` | `municipality` group | A2_EST/A2_MUN | COMPARABLE | gated by CC2 reconciliation | S1 rule preserved: IBGE/RFB municipality code **never** written to A2_COD_MUN directly |
| `endereco.municipio.codigo` | municipality code evidence | — | INFORMATIVE | never | Evidence for CC2 reconciliation; distinct coding system until proven identical to IBGE |
| `endereco.municipioJurisdicao.*` | jurisdiction info | — | INFORMATIVE | never | Not an SA2 field |
| `telefone[0]` | `phone` | A2_TEL | COMPARABLE | `trusted_source_policy_pending` | Public registry phone ≠ homologated commercial contact (S1 policy) |
| `correioEletronico` | `email` | A2_EMAIL | COMPARABLE | `trusted_source_policy_pending` | Same caveat |
| `situacaoCadastral.*`, `naturezaJuridica.*`, `cnaePrincipal.*`, `dataAbertura`, `capitalSocial`, `porte`, `situacaoEspecial`, `tipoEstabelecimento` | informational | none | INFORMATIVE | never | Display/provenance context only; never PUT |
| `socios.*`, `informacoesAdicionais.*` | out of scope | none | EXCLUDED | never | QSA/Empresa modality not contracted for MVP; contains personal data (CPF) |

Invariants preserved: tax_id protected, absent external field never clears
internal data, no new editable field, no financial/fiscal suggestion, no
`CNPJ_SA2_MAPPING_V1` change. `CONTRACT_IMPACT = NONE` on S1/S2.

---

## 5. COMPANY_REGISTRY_SOURCE_EVIDENCE_CONTRACT (P4)

Proposed evidence model (design — implementation is S3.1+):

| Field | Definition |
|---|---|
| `evidence_id` | Server-generated UUID per external query |
| `provider_id` | `serpro-consulta-cnpj` (contract modality recorded: `basica-v2`) |
| `provider_contract_version` | `v2` + doc revision captured at contract time |
| `supplier_code`/`supplier_store` | Bound to review subject |
| `source_reference` | `ni` (queried CNPJ) + query timestamp — never raw payload |
| `queried_at` | Server UTC timestamp |
| `response_digest` | SHA-256 of normalized projection (not raw payload — S2 retention rule) |
| `mapping_version` | `CNPJ_SA2_MAPPING_V1` version |
| `correlation_id` | Internal request id, also sent as `X-Request-Tag` (≤32 chars) for billing traceability |
| `actor_subject` | EffectiveUser.id at review creation |
| `data_classification` | `corporate-public` (Básica fields are public cadastral data) |
| `expires_at` | Ties to review TTL (24h default, pending B-02) |

Rules: evidence produced server-side only; browser never declares
`source_id`/`source_reference`; digest over the normalized projection keeps
auditability without storing raw payload; replay prevented by
`expires_at` + review `STALE` lifecycle + fresh fingerprint checks at
prepare-update; evidence is the future hook for `source_type=GOVERNMENT_API` +
`change_mode=EXTERNAL_SUGGESTION_USER_APPROVED` — still **rejected** by
api-delpi provenance contract v1 (no api-delpi change in this task).

### Threat model

- **Forged origin claim**: mitigated — origin is server-side only; client-supplied `source_*` rejected with 422 (already enforced in S2).
- **Stale/replayed snapshot**: mitigated — `queried_at` + digest + review expiry + baseline fingerprint re-validation.
- **CNPJ/identity mismatch**: `ni` must equal queried `tax_id` else hard error (`CNPJ_DIVERGENT`); protects against poisoned mapping.
- **Billing abuse**: per-request cost → `X-Request-Tag` correlation + per-user review limits + circuit breaker + no retries on 2xx-class failures.
- **Personal data leakage**: Básica modality excludes partner CPFs; schema guard rejects unexpected personal fields during normalization (denylist + allowlist of mapped paths).

---

## 6. LGPD / ROPA IMPACT (P5)

Reuses `supplier-enrichment-retention-classification.md` and institutional ROPA:
Básica response = public corporate cadastral data (not personal). QSA/Empresa
modalities introduce partner/representative CPF — **excluded from MVP** unless a
new DPO-reviewed decision authorizes it. Pointed gap for ROPA update:
external query event category (provider, correlation tag, digest) should be
registered when the contract is signed — flagged as `TO_INVENTORY` for the DPO
endorsement already pending from S2.

---

## 7. COMPANY_REGISTRY_ADAPTER_DESIGN (P6)

Design only — implementation requires S3.1 GO.

- `SerproCompanyRegistryProvider(CompanyRegistryProvider)` in
  `infrastructure/gateways/supplier_enrichment/serpro_provider.py`.
- Composition: `SerproTokenClient` (OAuth2 cc, caches bearer until exp−60s,
  never logs secret) + `CompanyRegistryHttpClient` (timeout ≤ 6s default, 1
  retry on 502/504/network, none on 4xx, circuit breaker) + `CnpjV2Normalizer`
  (pure: official schema → `ExternalRegistrySnapshot`, validates `ni`,
  schema-guards fields, computes `response_digest`).
- Config: `COMPANY_REGISTRY_PROVIDER=serpro|unavailable` (default
  `unavailable` — fail-closed preserved), `SERPRO_BASE_URL`,
  `SERPRO_TOKEN_URL`, `SERPRO_CONSUMER_KEY`, `SERPRO_CONSUMER_SECRET` (secrets
  via env/secret manager only), `SERPRO_TIMEOUT_SECONDS`,
  `SERPRO_RATE_LIMIT_RPS` (billing guard).
- Errors typed: `EnrichmentSourceUnavailableError` (5xx/timeout/breaker),
  `RegistryCnpjInvalidError` (400), `RegistryCnpjNotFoundError` (404),
  `RegistryContractViolationError` (schema mismatch/unexpected shape),
  `RegistryAccessDeniedError` (401/403 → alert, no retry).
- Provider knows nothing of Flask, Portal HTTP, SA2 comparison, or api-delpi.
- Feature gate independent of Protheus write gates; per-user query cap
  enforced in `create_review` flow.

### Offline contract tests — planned (fixtures per official V2 field dictionary, clearly labeled synthetic-not-captured)

CNPJ valid/invalid/divergent, 200 full, 206 partial, absent optionals,
unexpected types, schema-incompatible payload, unknown extra field tolerated vs
guarded, invalid dates, missing `ni`, over-limit `nomeEmpresarial`,
municipality without CC2 match, invalid phone/email, informational-only
fields, naturezaJuridica 213-5 socios-suppression shape, personal-field
rejection, log redaction of consumer secrets. `LIVE TESTS = TEST_NOT_RUN`.

---

## 8. S3_CONTRACT_FREEZE_REPORT (P8)

| Checklist item | Status |
|---|---|
| Provider identified | PROVEN — Serpro Consulta CNPJ, modality Básica v2 |
| DELPI entitlement | `TO_INVENTORY` — no contract evidence |
| Modality | PROVEN (Básica suffices; QSA/Empresa excluded) |
| Technical manual for contracted modality | PROVEN publicly; swagger `consulta-cnpj-df-v2` to verify post-contract |
| Authentication | PROVEN (OAuth2 client credentials, 1h bearer) |
| Request schema | PROVEN (GET + path CNPJ + Bearer + X-Request-Tag) |
| Response schema | PROVEN (official V2 field dictionary) |
| Field mapping to S1 | PROVEN (§4) — zero mapping-spec change |
| Nullability/absence | PARTIAL — 206/partial documented; per-field nullability to verify on contract |
| Errors/limits | PROVEN (code table); quotas not published |
| LGPD/retention | PROVEN for Básica; ROPA line pending |
| Source evidence | DESIGNED (§5) — implementation pending |
| Secrets strategy | DESIGNED (env/secret manager, key from client area) |
| Rollout/rollback | DESIGNED (`COMPANY_REGISTRY_PROVIDER` flag, default fail-closed) |
| Offline contract tests | PLANNED (fixtures grounded in official schema) |
| S1/S2 impact | NONE |
| Owner/execution GO | supplies-api; S3.1 requires separate GO after contracting |

**`CONTRACT_FREEZE = INCONCLUSIVE`** — correct and honest: the contract is
technically frozen against the official public documentation, but
`PROVIDER_ACCESS = TO_INVENTORY` blocks GO. Nothing may be billed or queried
until DELPI contracting (e-CNPJ flow) or trial keys are provisioned.
