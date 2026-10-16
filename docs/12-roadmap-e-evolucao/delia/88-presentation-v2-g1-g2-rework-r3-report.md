# 88 — Rework R3 (token redaction + L1 inventory + fallback reconciliation) — Relatório de execução

**Data:** 2026-10-16  
**Task:** `DELIA-UX-CONVERSATION-MARKDOWN-B2-G1-G2-R3-FINAL-CLOSURE`  
**BASE_HEAD (reanchor):** `40ac318a0c3d6dde1f69d0f84e72faeec2ffad61` (= `origin/main` no início; prompt citava `772fcc66ef` — FF 41 commits controllership, sem drift material no owner de sanitização)  
**CP:** `CP-333` — `PLANNED_NOT_PASS` (inalterado)  
**Tipo:** bounded security fix no owner legítimo + inventário/docs/probes; **sem** `presentation.v2` runtime, **sem** `ConversationMarkdown`, **sem** emissão de links.

> B2 aqui = Markdown conversacional (spec 82/83). **Não** confundir com `C3-STAGE-02-B2` (PREPARE/ACT).

## 1. R3-01 — Exposição da chave `token` (CRITICAL)

**Reuse Gate:** `EXISTING_EQUIVALENT=YES` / `REUSE_DECISION=EXTEND` — extender `_SENSITIVE_KEY_NAMES` em `delia-api/app/application/capability_provision/orchestration.py`; sem sanitizador paralelo.

**RED:** `test_bare_token_key_is_redacted` = XFAIL(strict) antes do fix (valor `tk-raw-SECRET` vazava).

**Fix:** incluir a chave canônica `"token"` no frozenset (matching exato via `_canonical_key` — cobre `token`/`Token`/`TOKEN`).

**GREEN:** mesmo teste PASS sem `xfail`. Variantes de caso + nested/list + preservação de `token_value`/`token-value`/`token_count` (exact-match; substring proibida).

**Trade-off aceito:** campo de negócio literalmente nomeado `token` é redigido (fail-closed).

## 2. R3-02 — Inventário L1 (CRITICAL / Contract)

Revalidado no HEAD:

| Candidato | OWNER | CONTRACT | CAPABILITY_ID | FIELD | FIELD_SEMANTICS | SOURCE_AUTHORITY | DISCLOSURE_POLICY | LIVE_AUTHZ | LINK_DESTINATION | VALIDATION_POLICY | CONSUMER | EVIDENCE | STATUS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mural_acessos link | `api-delpi` `domain/services/mural_acessos/link_url.py` | OpenAPI mural_access_link + `normalize_link_url` | *(nenhum binding DÉLIA)* | `url` | destino de atalho publicado no mural | Domain API write | UI/public mural | Core/Domain no destino | `http`/`https` + netloc | scheme+netloc+maxlen no write | MFE mural-acessos / public menu | código + OpenAPI; **zero** referência em `delia-api` | `CONTRACT_REAL` / binding `TO_INVENTORY` |
| external capability `url` arg | `api-delpi` `argument_validator.py` | `_TRANSPORT_FORBIDDEN` | n/a | `url` | transporte | n/a | n/a | n/a | n/a | **proibido** | n/a | código | `FORBIDDEN_BY_DESIGN` |
| Provenance / SourceRef / WorkspaceEntityRef / owner_hint | DÉLIA domain | projection contracts | n/a | n/a | identity/hint — **sem URL** | n/a | n/a | n/a | n/a | URL-free | turn path | R1/R2 + regrep HEAD | `NOT_A_SOURCE` |

**Estado:** `LINK_L1_CONTRACT=SPECIFIED` / `LINK_L1_CAPABILITY_BINDINGS=TO_INVENTORY` / `LINK_NAVIGABLE_EMISSION=BLOCKED`. L1 **não** revogada; zero links fabricados.

## 3. R3-03 — Fallback contract reconciliation

Inconsistência: doc 84 §2.9 / §6 diziam que `additionalProperties:false` → “fallback legado”, enquanto §2.5 + probe executável exigem `neutral_error` para v2 estruturalmente inválido.

**Congelado consistentemente:**

| Situação | Comportamento |
|---|---|
| v1 conhecido e válido | `render_legacy` |
| Versão desconhecida + legado validado | `render_legacy` |
| Versão desconhecida + legado inválido | `neutral_error` |
| v2 estruturalmente inválido (incl. props extras) | `neutral_error` |
| v2 admitido com falha só de renderização | `inert_text` |
| v2 válido | `render_v2` |

Probe novo: `test_fallback_v2_extra_properties_are_neutral_error_not_legacy_downgrade`. Runtime `parsePresentation` **não** alterado (D9 preservada).

## 4. Validação de schema

- Avaliador subset stdlib (versionado): probes em `test_presentation_v2_proposal.py` PASS.
- Validador autoritativo isolado (`jsonschema` 4.26.0, Draft 2020-12, venv temporário `/tmp/.jsonschema-probe`, **não** adicionado a deps de produção): schema check OK; 4/4 positivos; 17/17 negativos; non-object reject; extra-prop → policy `neutral_error`.

## 5. Testes

| Suíte | Resultado |
|---|---|
| Targeted delia-api (5 arquivos) | **236 PASS** (0 xfail) |
| Full delia-api | **1178 PASS** pré-+1 fallback; +1 probe → **1179** esperado; revalidar no SHA do commit |
| plugin-ui markdown+rich-text | **175/175 PASS** |
| plugins/delia vitest | **191/191 PASS** |
| Typecheck delia | PASS (sem erros no pacote) |
| Typecheck plugin-ui | FAIL pré-existente (outros owners; fora de escopo) |
| Build/Federation | `TEST_NOT_RUN` |

## 6. Estados preservados

```text
G1=CANDIDATE_REWORKED
G2=CANDIDATE_REWORKED
G3=BLOCKED
G4=TEST_NOT_RUN
CP-333=PLANNED_NOT_PASS
TOKEN_REDACTION_STATUS=CLOSED_R3_01
FALLBACK_CONTRACT_STATUS=RECONCILED_R3_03
LINK_L1_CONTRACT=SPECIFIED
LINK_L1_CAPABILITY_BINDINGS=TO_INVENTORY
PRESENTATION_V1=CURRENT_RUNTIME
PRESENTATION_V2=CONTRACT_TARGET
RUNTIME_B2_IMPLEMENTATION_AUTHORIZED=NO
PHASE_PROGRESSION=NONE
INDEPENDENT_REVIEW=PENDING
```

## 7. Veredito do executor

`READY_FOR_INDEPENDENT_REVIEW`

O executor **não** emite `G1/G2=APPROVED` nem `CP-333=PASS`.
