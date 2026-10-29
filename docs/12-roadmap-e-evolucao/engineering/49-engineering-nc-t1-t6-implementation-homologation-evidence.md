# Engineering NC — T1–T6: implementação, homologação integrada e evidências

Data: 2026-10-29 · Executor: Devin · Missão: `ENGINEERING.NC.MASTER.EXECUTION` (Plano Mestre 48)

## 1. Âncoras

| Item | Valor |
|---|---|
| BASE_HEAD (missão) | `712ea62048` (G0, doc 47) |
| HEAD T2+T2b+T4 | `7b610cf232` |
| HEAD T3 (EVA) | `d4edb2dad3` |
| HEAD T5/T6 (este doc) | a registrar no commit deste gate |
| Plano canônico | doc 48 — `48-engineering-nc-end-to-end-delivery-track-master-plan.md` |

## 2. Matriz de gates T1–T6

| Gate | Escopo | Estado | Evidência |
|---|---|---|---|
| T1 | Inventário revalidado, contratos, ADR persistência | PASS | doc 47 (G0 integral); inventário revalidado no HEAD antes de T2 — rotas, schema V001–V009, consumidores e permissões conferidos |
| T2 | Domain + ports + use cases READ + adapters + rotas E-NC-01..06,11 | PASS | commit `7b610cf232`; 51 testes NC verdes; boundary permitido só em `infrastructure/persistence/` |
| T2b | Sandbox Postgres isolado + adapter + seed | PASS | container `delpi-nc-sandbox` (postgres:15), schema derivado das migrations oficiais, 3 registros sintéticos; adapter 10/10 |
| T3 | EVA READ tools + catálogo + PREPARE | PASS | commit `d4edb2dad3`; 83 testes MCP; tools registradas com classes DISCOVERY/READ/PREPARE |
| T4 | WRITE E-NC-07..10 em base isolada | PASS | commit `7b610cf232`; create/update/delete/import + dry-run + optimistic lock + history append-only no sandbox |
| T5 | Portal NC UI + EVA PREPARE | PASS | este doc; MFE `delpi-engineering` servindo list/detail/form; E2E real 10/10 |
| T6 | Homologação integrada dev + runbook | PASS (dev isolado) | §7–§9; cutover produção **não** executado (T7/T8 fora de escopo) |

## 3. Arquitetura entregue

```text
Portal Engenharia (plugins/engineering MFE)
  → /apps/engineering-api/v1/nonconformities*   (Engineering API — owner funcional)
      → domain/application (use cases E-NC-01..11 + PREPARE)
      → NonconformityRepository port
          ├─ PostgresNonconformityRepository → postgres dedicado (ENG_NC_DB_*)
          ├─ InMemoryNonconformityRepository → testes/dev
          └─ UnavailableNonconformityRepository → degradação honesta
      → facts TOTVS via api-delpi (enriquecimento OV/produto/BOM) — sem SoT próprio
      → Core API → autorização efetiva (engineering.access / engineering.manage)
EVA MCP (eng-api /mcp)
  → tools READ + PREPARE sobre os mesmos use cases — token humano propagado
```

Decisões implementadas (conforme ADR doc 47, Opção B com escopo sandbox):

- Engineering API é owner funcional do bounded context NC (contratos + regras).
- Persistência via port/adapter com **principal dedicado** `ENG_NC_DB_*` — o composer rejeita reutilização de `PLUGINS_DB_USER` (guarda ativa contra segundo writer no storage compartilhado).
- Sandbox `delpi-nc-sandbox` = dataset isolado; schema é cópia fiel das migrations V001–V009 (`engineering.lmp_nonconformities`, `_products`, `lmp_problem_tags`, `_problem_tags`, `_history` + trigger append-only V008).
- `ENG_NC_IMPORT_REPLACE_ENABLED=true` exigido para replace-all; `confirm_replace` exigido no contrato; dry-run implementado.
- api-delpi permanece SoT TOTVS (facts/enriquecimento); legado dashboard-lmps intacto e operacional.

## 4. Contratos entregues (E-NC-*)

| Contrato | Método/rota | AuthZ Core | Estado |
|---|---|---|---|
| E-NC-01 list | `GET /v1/nonconformities` (filtros, sort whitelist, paginação) | engineering.access | PASS |
| E-NC-02 detail | `GET /v1/nonconformities/{id}` | engineering.access | PASS |
| E-NC-03 history | `GET /v1/nonconformities/{id}/history` | engineering.access | PASS |
| E-NC-04 indicators | `GET /v1/nonconformities/indicators` (streak) | engineering.access | PASS |
| E-NC-05 tags | `GET /v1/nonconformities/problem-tags` | engineering.access | PASS |
| E-NC-06 export | `GET /v1/nonconformities/export` | engineering.access | PASS |
| E-NC-07 create | `POST /v1/nonconformities` | engineering.manage | PASS (sandbox) |
| E-NC-08 update | `PUT /v1/nonconformities/{id}` (+ `expected_updated_at` optimistic lock → 409) | engineering.manage | PASS (sandbox) |
| E-NC-09 delete | `DELETE /v1/nonconformities/{id}` | engineering.manage | PASS (sandbox) |
| E-NC-10 import | `POST /v1/nonconformities/import` (`dry_run`, `confirm_replace`) | engineering.manage | PASS (sandbox) |
| E-NC-11 context | `GET /v1/nonconformities/{id}/context` (OV/produto/BOM via api-delpi facts) | engineering.access | PASS |
| PREPARE | `POST /v1/nonconformities/prepare` | engineering.manage | PASS — sem efeitos colaterais |

Mapeamento de erros: 401 unauthenticated · 403 unauthorized · 400 validação · 404 not_found · 409 concorrência · 502/503 dependência indisponível. Rotas registradas nas allowlists canônicas (`test_health`, `test_auth_middleware`).

## 5. Portal Engenharia (MFE)

- Caminho standalone `/apps/engineering/nonconformities` (doc 45) — **não** aninhado em `/lmps` como destino definitivo.
- Páginas: listagem (filtros, sort server-side, paginação, KPIs streak, export JSON, painel de importação com dry-run + confirmação destrutiva), detalhe (identificação, problema/tratativa, tags, produtos, contexto TOTVS, histórico append-only, excluir com confirmação), formulário create/edit (tags com catálogo, produtos, optimistic lock via `expected_updated_at`).
- Kit nativo exclusivamente: `EngineeringPageHero/PagePath/SectionCard/DetailCard/DetailFieldGrid/KpiCard/StatusBadge/StateBanner/EmptyState/ActionButton/DateField`, `DataTableSection` compartilhada das LMPs, classes `engineering-*`/BEM no `index.css`.
- Bridge `/apps/engineering/lmps/nonconformities`: "Experiência nativa disponível" + link para o registro legado (coexistência reversível; legado não desativado).
- Ajuda: seção "Não conformidades" no manual (HelpPage) + tooltips `hint/titleHint` nos filtros, tabela, contexto, histórico e painel de importação.
- Catálogo Início: entrada `nonconformities` com `requiredPermission: engineering.access`.

## 6. EVA — ledger de capacidades

| API → Contrato | EVA tool | Classe | AuthZ | Teste | Outcome |
|---|---|---|---|---|---|
| E-NC-01 | `list_nonconformities` | READ | token humano propagado | vitest MCP + live | PASS |
| E-NC-02 | `get_nonconformity` | READ | idem | idem | PASS |
| E-NC-03 | (contexto inclui history nos contratos) | READ | idem | idem | PASS |
| E-NC-04 | `get_nonconformity_indicators` | READ | idem | idem | PASS |
| E-NC-05 | `list_nonconformity_problem_tags` | READ | idem | idem | PASS |
| E-NC-11 | `get_nonconformity_context` | READ | idem | idem | PASS |
| PREPARE | `prepare_nonconformity_mutation` | PREPARE | `requires_human_confirmation=true`, `side_effects="none"` | contract freeze + live | PASS |
| ACT (create/update/delete/import) | — | ACT | **ausente por design** | `DESTRUCTIVE_ACT_TOOLS` vazio | PENDING (exige autorização separada — T7/T8) |

Suíte MCP: **83 testes** (contract freeze, authz negativos, propagação de token, validação, upstream honesto).

## 7. Testes automatizados por camada

| Camada | Comando | Resultado |
|---|---|---|
| domínio+rotas NC (eng-api) | pytest `test_nonconformity_domain.py` + `test_nonconformity_routes.py` | 51 PASS |
| adapter Postgres sandbox | pytest `test_nonconformity_postgres_adapter.py` (marca integration) | 10 PASS — list/filter/sort, get, streak, replace-all, dry-run, optimistic-lock 409, trigger append-only |
| MCP/EVA | pytest `test_eva_mcp.py` | 83 PASS |
| suíte eng-api completa | pytest | regressão OK — 3 falhas pré-existentes/ambientais (yaml ausente no mount, avatar https de trabalho concorrente) não relacionadas ao NC |
| MFE unit | `npm run test` | 141 PASS (119 preexistentes + 22 NC) |
| MFE lint/typecheck/build | `npm run ci` | 0 erros (warnings react-hooks já existentes no codebase) |
| E2E browser real | `npx playwright test -c e2e/playwright.config.ts` | **10/10 PASS** (desktop + mobile) |

## 8. Evidência de browser real (T6 §7)

Harness `plugins/engineering/e2e/` (mesmo padrão bpmn-modeler: login real SSO → Keycloak → portal autenticado; usuário dev autorizado via `DEV_PORTAL_*` em `infra/.env.local`).

Validado no stack real (Portal → MFE federado → Engineering API → Postgres sandbox; Core efetivo):

- Login real Keycloak; deep link `/apps/engineering/nonconformities`.
- Listagem: hero, filtros (status/OV/LMP/cliente/produto/tag/período), KPIs streak, tabela com dados reais do sandbox.
- Detalhe por clique na linha: `NC 005000`, badge de status, campos de auditoria (`Criado por`/`Atualizado por`), seções Identificação/Histórico/Contexto.
- Formulário `/new`: todas as seções renderizadas; cancelar retorna à listagem.
- Bridge legado `/lmps/nonconformities`: botões para experiência nativa e registro legado presentes.
- **Zero pageerrors** e **zero chamadas diretas do MFE a `/apps/api-delpi/`** (guard de boundary ativo nos specs).
- Viewports: Desktop Chrome + Pixel 7.
- Capturas (locais, gitignored): `plugins/engineering/e2e/artifacts/nc-list.png`, `nc-detail.png`, `nc-form.png`, `nc-legacy-bridge.png`.

Smoke autenticado adicional (curl + token dev): list/indicators/tags/context retornaram dados do sandbox; `GET` sem bearer → 401.

## 9. Runbook PREPARE/ACT (futuro cutover — não executado)

```text
FASE 0 (agora — concluída)
  bounded context + sandbox isolado + EVA READ/PREPARE + Portal NC coexistindo.

FASE 1 (T7 — requer autorização)
  1. Aprovação formal dos owners: role DB dedicada + grants engineering.lmp_*;
     runner de migrations (≥V012) sob ownership Engineering API.
  2. Freeze de writers legados na janela; checksum contagem/PK/history.
  3. Grants+deploy eng-api como writer único; legado read-only via contrato novo.
  4. Hardening do guard WRITE legado (api-delpi.access ⇒ write — risco doc 47).
  5. Telemetria 30–60d consumidores não-óbvios antes de deprecar endpoint legado.

FASE 2 (T8 — requer autorização)
  1. EVA ACT tools: contrato específico + aprovação + idempotência + auditoria;
     delete/import com confirmação humana reforçada.
  2. Cutover de consumidores; desativação do endpoint legado só com ledger zerado.
  3. Rollback: grants reversíveis, sem drop, compensação de writes intercalados.
```

## 10. Arquivos alterados neste gate (T5/T6)

Backend/MCP: nenhum diff novo (T2/T3 já commitados em `7b610cf232`/`d4edb2dad3`).

Frontend (`plugins/engineering`):

- `src/features/nonconformities/` — feature completa (types, api client, rotas, sub-router, 3 páginas, ncCopy com labels/variants/help).
- `src/api/httpClient.ts` — `postJson`/`putJson`/`deleteJson` + envelope `ApiFailBody` (mensagens de validação/conflito honestas).
- `src/app/engineeringRoutes.ts` — view `nonconformities`.
- `src/App.tsx` — dispatch da feature.
- `src/content/engineeringRouteCatalog.ts` — entrada no catálogo Início.
- `src/features/lmps/LmpsFeature.tsx` — bridge legado → experiência nativa.
- `src/features/lmps/utils/navigation.ts`, `src/features/help/HelpPage.tsx` — navegação/help.
- `src/index.css` — classes `engineering-nc-*` BEM.
- `e2e/` — harness Playwright (config, helpers SSO, spec NC, .gitignore artifacts).
- `package.json`/`package-lock.json` — `@playwright/test@1.62.1` devDep (mesma versão do bpmn-modeler) + script `test:e2e`.

## 11. Riscos e residuais

| Item | Estado |
|---|---|
| WRITE real no storage compartilhado `postgres-plugins` | PENDING — aguarda grants/role dedicada (T7) |
| Guard legado `api-delpi.access ⇒ write NC` | Documentado (doc 47); hardening na janela de cutover |
| Telemetria de consumidores legados 30–60d | TO_INVENTORY antes de qualquer deprecação |
| E2E em CI | Harness funciona onde Chromium tem deps de SO (WSL local carece de `libnspr4`; executado no host Windows — 10/10) |
| Falhas de teste eng-api pré-existentes | Não relacionadas ao NC (yaml mount, avatar https de trabalho concorrente) — preservadas |
| Divergência 9p WSL↔Windows em escrita de arquivos | Contornada: escrita de artefatos via temp NTFS + `cat` no WSL |

## 12. Decisões pendentes (owner externo)

1. Grants/role DB dedicada de produção para `engineering.lmp_*` (T7).
2. Runner de migrations sob ownership Engineering API (≥V012).
3. Política soft vs hard delete a confirmar com owner funcional.
4. Autorização EVA ACT (T8) — nunca habilitar sem contrato específico.

## 13. Próximo passo operacional

Retornar à Coordenação EVA com este doc + commits. T7/T8 permanecem **não autorizados**: sem deploy produtivo, sem migration produtiva, sem alteração de grants, sem cutover, sem desativação de endpoints legados e sem EVA ACT.
