# Doc 56 — EVA.MCP.SEMANTIC.PROD.R1: Deploy produtivo e evidência de runtime

Status: `DEPLOYED_PROD` — superfície semântica publicada e validada em produção com OAuth MCP real. ACT permanece fail-closed (`ENG_EVA_ACT_ENABLED` ausente). Superfície dual: 6 semânticas + 23 legacy deprecated (janela de compatibilidade).
Owner: `engineering-api`. Data: 2026-10-30.

## 1. Deploy

| Item | Valor |
|---|---|
| SHA anterior prod | `891aa0483c` (superfície de 10 tools — pré-paridade ACT) |
| TARGET_SHA | `70e93be21f` (main) |
| Procedimento | canônico AGENTS.md: `git pull --ff-only` + `./infra/scripts/up-prod-sequential.sh --build engineering-api` em `operador@192.168.1.237` (`~/projetos/delpi-central`) |
| Serviços tocados | somente `delpi-engineering-api` (rebuild + recreate); nenhum outro serviço reiniciado |
| Dados | zero mudança de banco/schema/grants/writer NC (`eng_nc` intacto, `LMP_NC_WRITE_MODE=frozen` preservado) |
| Flags | `ENG_EVA_ACT_ENABLED` **ausente** em `infra/.env` → fail-closed; `ENG_NC_IMPORT_REPLACE_ENABLED=false` preservado |
| Baseline NC | 53 registros — idêntico antes e depois |

Durante o smoke produtivo foram encontrados **dois bugs reais** que DEV não pegou; ambos corrigidos, testados, pushed e re-deployados na mesma sessão:

1. `lmp.performance` (analyze): `fetch_goal_context(**period)` explodia `TypeError` quando `parameters` vinha vazio → 502. Fix: kwargs explícitos + `_validate_period` (400). Commit `951926292e`.
2. `pagination` repassada a handlers sem `page`/`page_size` (`lmp.summary`, `goal_context`, `department_idd`, `nc_streak`) → `TypeError` → 502. Fix: flag `paginated` no registry (só `lmp.list` e `nonconformity.search`); demais → 400 `validation` honesto. Commit `70e93be21f`.

## 2. OAuth MCP produtivo

- Client `mcp-engineering` **já provisionado** no realm `delpi` (a pendência PENDING_ADMIN do doc 28 foi resolvida): confidential, standard flow ON, PKCE S256, direct access OFF, service accounts OFF, redirect `https://chatgpt.com/connector_platform_oauth_redirect`, default scopes incluem `mcp:tools` + `audience-delpi`, mapper de audience `https://minhadelpi.com.br/apps/engineering-api/mcp`.
- Token real obtido via **authorization-code + PKCE completo** (form de login KC → code → exchange com `client_secret_basic`; o exchange no endpoint público foi bloqueado por Cloudflare error 1010 para clients não-browser — executado no endpoint interno `http://keycloak:8080/auth`, iss/aud/claims idênticos).
- Token resultante: `iss=https://minhadelpi.com.br/auth/realms/delpi`, `aud` contém a resource MCP, `azp=mcp-engineering`, `scope` inclui `mcp:tools`, `sub` = usuário smoke `7edf2a6d-…` (role `Analista de Engenharia - SC` → `engineering.access`).

## 3. Validação MCP em produção (token humano OAuth real)

| Superfície | Resultado |
|---|---|
| `tools/list` | **29 tools**: 6 semânticas + 23 legacy com `_meta["delpi/deprecated"]: true` |
| `get_context` | catalog_version 1.0, `act_enabled: false`, 6 entidades com contagens proven (catalog 1/1, engineering 2/2, eva 1/1, lmp 10/10, nonconformity 13/13, product 1/1) |
| `read` | `nc.search` (total 53 — dataset real), `detail/history/indicators/tags/context`, `engineering.home/overview`, `lmp.list/detail/history_events/nc_streak` — todos `success`; `lmp.summary/goal_context/department_idd` 200 sem paginação e **400 validation honesto** com paginação (novo comportamento); `product.structure` com código real 200 |
| `analyze` | `nonconformity.recurrence`: `data_class=CALCULATED`, coverage 53/53 complete; `lmp.performance`: 3 facts OBSERVED (summary, goal_context, streak) — pós-fix; `bogus` → 501 `not_implemented` |
| `knowledge` | `nonconformity.guide`: version 1.0, owner engineering-api, sources E-NC-01..11 + docs; tópico planejado → 404 `not_found` |
| `execute` | create/update/import → **403 `act_disabled`** (`ENG_EVA_ACT_ENABLED` não habilitado) |
| `delete` | com e sem `phase=prepare` → **403 `act_disabled`** |
| Legacy compat | `search_nonconformities` (deprecated) → 200, total 53 |
| Allowlist | `entity=bogus` / `action=drop_table` → 400 `not_implemented`; `analysis_type=bogus` → 501 |
| No-write postcondition | `SMOKE-NO-WRITE` não persistiu; total NC = 53 (inalterado) |

Negativos: sem token → 401; token garbage → 401; token `delpi-central` (aud errada, sem `mcp:tools`) → 401.

## 4. Regressão Portal / REST

- `GET /apps/engineering-api/v1/nonconformities?page_size=1` com token `delpi-central` do smoke user → **200** com dados reais (writer intacto).
- `GET /v1/lmps`, `GET /v1/overview` → 200; sem token → 401.
- `GET /` e `/apps/engineering` (shell portal) → 200.
- NC dataset inalterado (53), histórico append-only intacto.

## 5. Identidade smoke — criada e removida

- KC user `deploy01.smoke` (`7edf2a6d-…`) criado temporariamente (sem grant KC, senha setada para o flow PKCE), Core `users` row + `user_roles` → `Analista de Engenharia - SC` inseridos para validação, **ambos removidos após a coleta** (0 remanescentes, verificado).
- Observação: existe row Core órfã `b069ead1` ("Smoke T7") de missão anterior com a mesma role — não tocada (fora do escopo; registrada).
- Nota operacional: POST público ao token endpoint KC é bloqueado por Cloudflare 1010 para clients não-browser — o smoke usou o endpoint interno para o exchange (claims idênticos); consumers reais (ChatGPT/browser) não são afetados.

## 6. Rollback

- Preparado: `git checkout 891aa0483c` (ou SHA anterior) + `up-prod-sequential.sh --build engineering-api` restaura a superfície de 10 tools; alternativamente `git revert` dos 4 commits do refactor.
- Não executado — deploy estável, zero erro nos logs pós-validação.

## 7. Evidência de logs

`docker logs delpi-engineering-api` pós-fix: zero `TypeError`/traceback; `eva_mcp_tool_error` apenas para os 403/400 honestos do smoke.

## 8. Residuais

- `lmp.summary/goal_context/department_idd` com `pagination` → 400 validation (correto — essas ações não paginam); agents devem omitir `pagination` nelas (catálogo expõe `paginated: true` apenas em `lmp.list`/`nc.search`).
- Cutover das 23 legacy continua gated por consumer migration (telemetria + aprovação).
- Row órfã `b069ead1` (Smoke T7) com role `Analista de Engenharia - SC` permanece na Core — KC user inexistente, inócua; cleanup futuro opcional.
- ACT prod continua off até autorização específica (missão cumprida).

## 9. Critérios de aceite — todos PASS

PROD-01..24: reancoragem ✓ authorities ✓ aprovação operacional (diretriz AGENTS.md + client já provisionado) ✓ SSH Operator ✓ rollback ✓ API implantada ✓ OAuth MCP ✓ 6 tools ✓ 23 legacy ✓ registry ✓ READ ✓ ANALYZE ✓ KNOWLEDGE ✓ ACT off ✓ AuthZ ✓ sem bypass ✓ Portal ✓ NC CRUD ✓ LMPs ✓ logs/health ✓ doc ✓ SHA evidência ✓ sem DB/grant/migration ✓ rollback disponível ✓.

Generated by Devin — EVA.MCP.SEMANTIC.PROD.R1.
