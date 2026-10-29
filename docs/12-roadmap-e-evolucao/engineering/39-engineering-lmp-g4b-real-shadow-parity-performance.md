# ENGINEERING.LMP.G4.B — Real Shadow Parity & Performance Evidence

**Status:** CONCLUÍDO — paridade real comprovada com dados TOTVS (tolerância 0), benchmark dentro do critério, 1 correção local testada.
**Missão:** `ENGINEERING.LMP.G4.B` — Real Shadow Parity, Performance Validation & Consumer Readiness.
**Baseline:** `dfb610ce27834fa94bdbcd4124cd2ff372078559` (R2 verificada publicada em `origin/main`).
**Referências:** docs 32–38; `lmp_semantics.v1.yaml`; `domain/lmp/parity.py`.

---

## 1. Pré-condição G4.A.R2

Commit `dfb610ce27` verificado e publicado em `origin/main` durante a reancoragem desta missão. Diff revisado (4 arquivos: provisioner `--apply`, compose ENG_S2S_TOKEN_URL, doc 38) — sem secrets. Integração S2S revalidada em runtime nesta missão (ver §6).

## 2. Shadow runner

`engineering-api/scripts/lmp_shadow_runner.py` — executor read-only e reproduzível:

- **Legado:** `GET /apps/api-delpi/engineering/lmps/dashboard/items` e `/lmps/dashboard/summary`.
- **Novo:** `GET /apps/engineering-api/v1/lmps` e `/v1/lmps/summary` (facts via S2S).
- **Facts:** `GET /apps/api-delpi/engineering/lmps/facts` (humano + `X-Delpi-Service-Authorization`) — benchmark do canal técnico.
- Mesmos filtros/janela (`status=Todos`, `listing_type=Todos`, `page_size=500`, paginação completa até esgotar `total`).
- Comparação via `compare_items`/`compare_summary` (tolerância 0 pós-normalização de tipos); chave `branch|ov|revisão|ciclo`.
- Degradação honesta (`status≠available`) é registrada como `TEST_NOT_RUN` da janela — nunca contada como divergência nem ocultada.
- Relatório JSON: SHA, ambiente, janelas, cobertura, divergências com `rule_id→category`, latências — sem tokens, secrets ou `sale_description`.

## 3. Corpus real

- **Janelas:** 12 competências completas (out/2025 → set/2026).
- **Método de seleção:** determinístico — TODOS os itens retornados pelos endpoints em cada janela (sem cherry-pick); chaves únicas deduplicadas.
- **Universo real:** 215 OVs únicas, 237 comparações de item (revisões/ciclos distintos contam como itens).
- **Cobertura efetiva:** kinds `LMP`=191, `OUTRO`=20, `AMOSTRA`=9; status `Pontual`=216, `Atrasado`=4; filiais `01`=168, `02`=52. Meta de 200 OVs: universo real é 215 — cobertura ≈100% do universo elegível do ambiente (não houve padding artificial).

## 4. Resultado de paridade (run final)

| Dimensão | Resultado |
|---|---|
| Itens comparados | **237** (12 janelas; jul/2026 retestado isoladamente após degradação transitória) |
| Itens matched | **237** |
| Divergências finais | **0** (campo e chave) |
| Summaries (R09/R10/COUNT) | **0 divergências** após correção §5 |
| F-LMP-01..04 | exercidos via BFF e facts direto |

`REAL_SHADOW = PASS` — dados TOTVS reais, tolerância zero, reproduzível.

## 5. Divergência encontrada e correção

```text
DIVERGENCE_ID: G4B-D01
RULE_ID: COUNT (summary.total_items)
OV_REFERENCE: universo (todas as janelas — ex.: ago/2026: legado 21, eng 19)
FIELD: total_items
LEGACY_VALUE: universo filtrado completo (todos os kinds)
ENGINEERING_VALUE: apenas itens listing_kind=LMP
EXPECTED_SEMANTICS: total_items = universo filtrado; total_lmps = LMP-only
ROOT_CAUSE: `get_lmp_summary._load_facts` forçava `lmp_only=True` na
  resolução do filtro — facts buscados já restritos a LMP; AMOSTRA/OUTRO
  nunca chegavam ao agregado.
CATEGORY: CONTRACT_MISMATCH (implementação migrada)
SEVERITY: medium (KPIs R09/R10 corretos; só total_items subcontava)
OWNER: engineering-api application
STATUS: FIXED + RETEST PASS
FIX_REFERENCE: get_lmp_summary.py — resolve_listing_type_filter sem
  lmp_only; teste test_summary_total_items_counts_all_listing_kinds
RETEST_RESULT: 11/11 janelas summary com 0 divergências; suíte 294 passed
```

Correção enquadra-se em "correção local de paridade comprovada": semântica oficial evidenciada no código legado (`_compute_summary(lmp_only, len(filtered))`) e confirmada por reteste real; diff mínimo (3 linhas); contrato público inalterado; teste de regressão adicionado.

**Drift transitório (não-divergência):** run intermediário classificou jul/2026 e out/nov-2025 como ausentes — causa: `status=unavailable` honesto da fonte facts (timeout PI/TOTVS) e/ou DNS cache do gateway pós-restart. Runner corrigido para classificar degradação como `TEST_NOT_RUN`; reteste isolado de jul/2026: 17/17 matched, 0 divergências.

## 6. Segurança revalidada (runtime)

- `/v1/lmps` sem Bearer → 401; facts sem credenciais → 401.
- Facts com `X-Delpi-Service-Authorization` inválido → 401 `S2S_TOKEN_INVALID`.
- Facts com token válido de outro serviço (supplies-api) → 403 `S2S_CLIENT_DENIED` (evidência R2 mantida).
- Facts humano+S2S válido → 200; S2S-only sem humano → 401.
- Zero `engineering.*` em guards de `api-delpi/app/` (residual search).
- AuthZ funcional na eng-api via Core; `manage`-only e permissão legada → 403 (testes).

## 7. Benchmark (mesma janela/universo, leitura real)

| Caminho | P50 | P95 | P99 |
|---|---|---|---|
| Legado `/lmps/dashboard/items` | 2.757s | 4.045s | 6.217s |
| Facts `/engineering/lmps/facts` | 2.334s | 3.266s | 3.932s |
| Engineering `/v1/lmps` | 2.818s | 4.024s | 5.011s |

- **Critério doc 34:** P95 facts ≤ 1,2× legado → 3.266 ≤ 4.854 ✓ (facts é ~0,81× do legado).
- `/v1/lmps` ≈ paridade com legado (regras migradas em Python sem regressão mensurável de latência).
- Comparação honesta: facts retorna fatos crus; dashboard/items inclui enrich+PI full — payloads não idênticos, registrado conforme §6 da missão. Amostra: 12 janelas × 3 caminhos, leitura única por janela; não é teste de carga.
- Observado: timeout intermitente de `pi-counts` (cold start TOTVS) → degradação honesta documentada (residual G4.B, owner platform-reliability).

## 8. Matriz de readiness de consumidores

| Consumidor | Contrato atual | Contrato futuro | Paridade | Bloqueios | Próximo gate |
|---|---|---|---|---|---|
| Dashboard LMPs | api-delpi `/lmps*` legado | E-LMP-01/03 | **PROVEN** (237 itens, 0 div) | — | G4.C/G5 |
| Dashboard Engenharia | api-delpi overview | home/overview eng-api | pendente (domínio distinto) | inventariar contratos | G4.C |
| Strategic Indicators | KPIs LMP via api-delpi | E-LMP-03 realizado (metas=SI) | R09/R10 paridade real | — | G7 |
| Portal Engenharia | — | `/v1/lmps` | contrato pronto | UI não migrada | G5 |
| DÉLIA | nenhum | proposta LMP | pendente | contrato inexistente | G7 |
| EVA | tools atuais (sem LMP) | tools LMP futuras | pendente | aguarda contrato validado | G6 |
| TV Dashboard | via SI (indireto) | via SI | indireto | — | com SI |
| Console de APIs | catálogo | catálogo | inventário | — | — |

## 9. Observabilidade e dados

Runner registra SHA, ambiente, janelas, cobertura agregada, divergências por chave técnica e latências. Não registra tokens/secrets/`sale_description`/payloads pessoais; relatório em `/tmp` (não anexado ao Git).

## 10. Arquivos alterados

- `engineering-api/engineering_app/application/use_cases/get_lmp_summary.py` — correção de paridade (G4B-D01).
- `engineering-api/scripts/lmp_shadow_runner.py` — novo executor read-only.
- `engineering-api/tests/test_lmp_routes.py` — stub de summary + teste de regressão.
- Doc 39 (este documento).

## 11. Testes no SHA final

- eng-api: **294 passed** (inclui novo teste de regressão).
- api-delpi `-k lmp`: **182 passed**.
- Audits: phase3 37 passed, platform_guardrails passed, openapi 0, fastapi_authz 0, backend_boundaries 0.
- Residual search: 0 ocorrências de `engineering.*` em `api-delpi/app/`.

## 12. Residuais e riscos

- Corpus limitado ao universo real do ambiente dev (215 OVs; poucos `Atrasado`/AMOSTRA) — cobertura de categorias raras documentada; homologação volumétrica pode ampliar.
- `pi-counts` timeout intermitente em cold start — degradação honesta, sem mascaramento.
- Status filter no summary: contrato eng `/v1/lmps/summary` não expõe `status`/`listing_type` — equivalente ao default legado `Todos`; se consumidor usar filtros, registrar gap em G4.C.
- Provisioning staging/prod pendente (ACT separado).

## 13. Veredicto proposto

**`ACCEPT`** — paridade real tolerância 0 em dados TOTVS, benchmark dentro do critério, boundary S2S/Core intactos, legado intocado. Próximo passo: G4.C (readiness Dashboard Engenharia/contratos faltantes) — não iniciado.
