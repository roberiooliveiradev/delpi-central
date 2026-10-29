# ENGINEERING.LMP.DEPLOY.01 — Production Deployment & Runtime Evidence

**Gate:** DEPLOY.01 — Production Deployment, Core Registration & Runtime Validation
**Ambiente-alvo:** Produção — `https://minhadelpi.com.br` (`srv-api`, `operador@192.168.1.237`)
**Executor:** Devin · **Coordenação:** EVA — Architecture / Coordination
**Data:** 2026-10-29
**Baseline (`BASE_HEAD`):** `a74e21a99aee1c4b4a89074c0c89adfbd8187c96` (`origin/main`, branch `main`)
**`TARGET_SHA`:** `a74e21a99aee1c4b4a89074c0c89adfbd8187c96`
**SHA instalado em prod:** `497c8095e9fd58c0c43c4831d1fff8eaad013786` — delta para TARGET = 1 commit **docs-only** (`a74e21a99a`, controllership-finance REWORK-012). Código de `plugins/engineering` e `engineering-api` é **idêntico** entre `497c8095e9`, `a74e21a99a` e a referência validada G5.V `826c73b1c4d09d965856bd0543e5d984bdb1e6a8` (zero commits pós-G5.V nesses paths).
**Status:** deploy produtivo **já executado pelo operador** (ver §8 timeline); este documento consolida PREPARE, evidência de runtime e pendências.

---

## 1. Reancoragem e authorities

| Item | Valor |
|---|---|
| `BASE_HEAD` (local `origin/main`) | `a74e21a99aee1c4b4a89074c0c89adfbd8187c96` |
| Branch | `main` (working tree com alterações concorrentes de terceiros — preservadas, nenhuma em paths de engenharia) |
| Prod repo (`srv-api:~/projetos/delpi-central`) | `497c8095e9`, tree limpa (0 modificações), G5.V ancestral |
| G5.V `826c73b1` no HEAD local? | Sim (`git merge-base --is-ancestor` → OK) |
| G5.V `826c73b1` no HEAD prod? | Sim (`G5V_IN_PROD_REPO`) |
| Commits pós-G5.V em `plugins/engineering`, `engineering-api` | **0** |
| Commits pós-G5.V em `infra/`, compose | 1 (`e963666854` external-data-api scheduler — não relacionado) |

**Authorities lidas:** `AGENTS.md`; constituição (`development-standards-index`,
`evidence-driven-execution`, `centralized-rules-first`,
`clean-code-architecture-guardrails`, `english-code-identifiers`);
`plan-execution`, `local-first-deploy`, `infra-sequential-container-startup`,
`platform-delivery-runtime-operations`; docs Engenharia 32–43 (foco: 38 S2S
provisioning, 42 registro Core/routing, 43 G5.V); `CUTOVER-RUNBOOK.md`;
`engineering.manifest.json`; `infra/scripts/keycloak_s2s_engineering_facts_scope.py`.

## 2. Inventário produtivo (READ-only, `docker ps` em `srv-api`)

| Serviço | Container | Estado | Observação |
|---|---|---|---|
| Portal host | `delpi-portal` | Up ~18h | SPA serve `/apps/**` via longest-prefix |
| Remote MF | `delpi-plugin-ui` | Up ~23h | OK |
| Gateway Nginx | `delpi-gateway` | Up ~22h (healthy) | rotas engineering presentes (§5) |
| Keycloak | `infra-keycloak-1` | Up ~2d | realm `delpi` |
| Core API | `delpi-core-api` | Up (restart recente) | saudável |
| Postgres Core | `delpi-postgres-core` | Up ~2m | owner dos registros |
| Engineering API | `delpi-engineering-api` | Up (healthy) | started 2026-10-29 14:37 (-03) |
| MFE Engineering | `delpi-engineering` | Up | started 2026-10-29 14:36 (-03) |
| API DELPI | `delpi-api-delpi` | Up (healthy) | facts target S2S |
| Strategic Indicators | `delpi-strategic-indicators-api` | Up ~9d | metas/IDD via eng-api |
| MFE legado | `delpi-dashboard-lmps` | Up ~4 sem | coexistência preservada |
| Dashboard Eng legado | `delpi-dashboard-engineering` | Up ~4 sem | idem |

Observação fora de escopo: `delpi-external-data-scheduler` reporta `unhealthy`
(pre-existente, PROC-0076 — não relacionado a esta missão).

## 3. Registro Core (produção)

Consulta direta `apps`/`app_routes`/`permissions`/`role_permissions`/`user_roles`
em `delpi-postgres-core` (READ-only):

| Item | Estado |
|---|---|
| App `engineering` | **registrado** — `version=0.2.0`, `active=t`, `base_path=/apps/engineering` |
| `created_at` | 2026-10-28 11:46 (-03) |
| `updated_at` | 2026-10-29 14:42 (-03) — manifest 0.2.0 com rota LMPs |
| Rotas | `/apps/engineering`, `/apps/engineering/overview`, `/apps/engineering/lmps`, `/apps/engineering/help` — todas `engineering.access` |
| Permissão `engineering.access` | existe |
| Permissão `engineering.manage` | **não existe** na Core prod — código eng-api usa exclusivamente `engineering.access` (AuthZ unificada G3); não é bloqueio |
| Grants efetivos | via roles: `Analista de Engenharia - SC` → `engineering.access` (**4 usuários**); `Dashboards Lideranças` → `engineering.access` (role_permission presente) |
| Legados | `dashboard-lmps` 1.2.0 ativo; `dashboard-engineering` 0.2.1 ativo — nenhum cutover |

O registro (causa-raiz do doc 42 §5) **já foi resolvido em prod** pelo operador.

## 4. S2S interservice (produção)

Execução de `keycloak_s2s_engineering_facts_scope.py` em modo `--check`
(read-only, via stdin no container `delpi-engineering-api`,
`KC_BASE_URL=http://keycloak:8080/auth`, realm `delpi`):

```text
[OK] client engineering-api — service account habilitada
[OK] client scope engineering-facts.read — presente
[OK] default scope engineering-facts.read — atribuído
[OK] audience mapper api-delpi — presente no cliente
```

| Item | Esperado | Efetivo (env do container) |
|---|---|---|
| Client técnico | `engineering-api` | `S2S_CLIENT_ID=engineering-api` ✓ |
| Grant | client_credentials | service account habilitada ✓ |
| Scope | `engineering-facts.read` | `S2S_SCOPE=` (default scopes do client) ✓ |
| Audience | `api-delpi` | `S2S_AUDIENCE=api-delpi` ✓ |
| Allowlist api-delpi | contém `engineering-api` | `S2S_ALLOWED_CLIENTS=supplies-api,controllership-finance-api,engineering-api` ✓ |
| Token URL | realm `delpi` | `http://keycloak:8080/auth/realms/delpi/.../token` ✓ |
| Header | `X-Delpi-Service-Authorization` | código `downstream_client.py` — `X-Delpi-Service-Token` proibido ✓ |
| Secret | `infra/.env` gitignored | `ENG_S2S_CLIENT_SECRET` setado; nunca impresso ✓ |
| Identidade separada | token técnico ≠ token humano | cadeia comprovada (§6) |

Residual transversal já conhecido (doc 37 §5): env_file compartilhado injeta
vars genéricas `S2S_*`, `CF_S2S_*` e `API_DELPI_INTERNAL_SERVICE_TOKEN` no
container eng-api — **não utilizadas** pelo código facts (o compose mapeia
`ENG_S2S_*`→`S2S_*` com precedência e o código proíbe header interno legado).

## 5. Gateway (produção, `nginx -T`)

- `location ^~ /apps/engineering-api/` → `engineering-api:8000` com rewrite ✓
- `location ~ ^/apps/([^/]+)/assets/remoteEntry\.js$` → `delpi-$1` (padrão genérico cobre `engineering`) ✓
- `location ^~ /apps/api-delpi/` → `api-delpi:8000` ✓
- Borda exige SSO: `/apps/engineering`, remoteEntry e `/apps/engineering-api/v1/lmps` anônimos → **401** (fail-closed esperado).

## 6. Evidência de runtime (produção, logs seguros)

### Cadeia funcional — tráfego autenticado real (2026-10-29 14:51–14:55 -03)

Origem `delpi-gateway` (usuário autenticado via SSO):

| Chamada | Resultado |
|---|---|
| `GET /apps/engineering-api/v1/lmps?page_size=1` **sem** token | **401** |
| `GET /v1/lmps?start_date=…&competence=2026-10&page_size=1` | **200** (`list_lmps`, 1.6s) |
| `GET /v1/lmps/003696?branch=01` | **200** (`get_lmp_detail`) |
| `GET /v1/lmps/goal-context` | **200** (metas/IDD via owner oficial) |
| `GET /v1/lmps/nonconformities/streak` | **200** — chamada downstream `GET delpi-api-delpi:8000/engineering/lmps/nonconformities/streak` → **200** |
| `GET delpi-api-delpi:8000/engineering/lmps/facts?…&page_size=500&include_qtd_pi=true` | **200** (S2S direto container→container) |

Parâmetros de query (`branch`, `competence`, `page_size`, intervalo de datas)
correspondem ao padrão de chamadas da UI nova — indício forte de uso real do
Portal em produção (formal browser-check do §9 da missão permanece com operador).

### Health

`delpi-engineering-api` healthcheck OK (`GET /health` → 200 contínuo,
`operation_id=get_engineering_health`). `delpi-engineering` serve
`remoteEntry.js` (ver §7).

### Cold-start residual

Logs das últimas 24h mostram `GET /apps/api-delpi/engineering/lmps/facts*` → 500
após ~120s (timeout downstream TOTVS em cold start — residual já documentado no
doc 38 §10; chamadas subsequentes 200). Observável, não mascarado.

## 7. Artefatos — rastreabilidade bit-a-bit

Build local reproduzido em `a74e21a99a` (`npm run build`, plugins/engineering)
produziu nomes de chunks **idênticos** aos servidos pelo container
`delpi-engineering` em produção:

```text
__federation_expose_App-BXIplwKI.js   index-B4SFKWmm.js   App-ULf5I1D7.js
__federation_fn_import-CSkvuf8Q.js    __federation_shared_lucide-react-CryiIvcU.js
__federation_shared_react-8tQwtpwq.js __federation_shared_react-dom-BHjNfo1u.js
```

Imagens `infra-engineering:latest` / `infra-engineering-api:latest` criadas
2026-10-29 17:36–17:37 UTC a partir do repo prod `497c8095e9` (eng code idêntico
ao TARGET_SHA). Artefato em produção = artefato testado.

## 8. Timeline do ACT (executado pelo operador, reconstruída por evidência)

| Horário (-03) | Evento |
|---|---|
| 2026-10-28 11:46 | App `engineering` registrado na Core prod |
| 2026-10-29 14:36 | `delpi-engineering` rebuilt/started (imagem `infra-engineering`) |
| 2026-10-29 14:37 | `delpi-engineering-api` rebuilt/started (healthy) |
| 2026-10-29 14:42 | Manifest 0.2.0 atualizado na Core (`apps.updated_at`) |
| 2026-10-29 14:51–14:55 | Smoke autenticado real: 401 probe → 200 list/detail/goal/streak; S2S facts 200 |

Serviços não afetados (Keycloak, Core, legados, demais apps) preservados —
nenhum `compose down`, nenhuma migration, nenhum cutover.

## 9. Gates de qualidade no SHA-alvo (`a74e21a99a`)

| Gate | Resultado |
|---|---|
| `npm run typecheck` (plugins/engineering) | PASS — 0 erros |
| `npm run lint` | 0 erros, 11 warnings (pré-existentes, idem G5.V) |
| `npm test` (vitest) | **119/119 PASS** (14 arquivos) |
| `npm run build` | PASS (warning de chunk >500kB pré-existente) |
| `pytest` engineering-api (repo `.venv`) | **311/311 PASS** |
| Audits CI (`test_audit_architecture_phase3`, `backend_boundaries`, `fastapi_authz`, `openapi_contracts`, `platform_guardrails`) | **78 passed + 4 subtests** |
| `audit_mfe_plugin_ui_css` | warnings pré-existentes multi-plugin; engineering: 1 warn (`lmps.css:199` composição de classe kit para card full-width — padrão documentado G5.V) |
| Residual search | 0 chamada funcional api-delpi no MFE; 0 secrets em paths eng |
| Secret scan | nenhum secret impresso/commitado; `ENG_S2S_*` apenas em `infra/.env` |

## 10. Validação em navegador real — estado

| Item | Estado |
|---|---|
| Portal `/apps/engineering` | infra completa (app registrado, remoteEntry 200 interno, host longest-prefix, grants por role) + tráfego autenticado real nas rotas novas (§6) |
| Checklist formal §9 da missão (login → home → overview → lmps → detalhe → temas/responsivo) | **PENDING_OPERATOR** — requer usuário autorizado em browser; matriz visual já homologada em dev (G5.V, 16 screenshots) sobre artefato bit-idêntico |
| Paridade de dados legado×novo | **TEST_NOT_RUN** — mesmos facts/contratos; G4.B provou paridade tolerância 0 em dev; comparação prod depende de sessão autorizada |
| Testes negativos AuthZ prod | 401 sem token observado ao vivo; usuário-sem-grant / token inválido / S2S inadequado / Core-down: cobertos por unit tests (311) + evidência dev (doc 38 §5); live-test com 2ª identidade = **TEST_NOT_RUN** (não criar usuários nem induzir falha em prod sem autorização) |

## 11. Plano ACT residual (para autorização operacional, se desejado)

O deploy funcional já ocorreu. Ações residuais opcionais, todas reversíveis:

1. `cd ~/projetos/delpi-central && git pull --ff-only` em `srv-api` — alinha
   `497c8095e9` → `a74e21a99a` (docs-only; sem rebuild necessário).
2. Browser-check §9 com usuário `Analista de Engenharia - SC` autorizado.
3. Comparativo de paridade §10 (mesmos filtros/período, novo × legado).
4. Negativo AuthZ com identidade secundária sem grant (somente leitura).

Rollback (se necessário): `DELETE /admin/apps/engineering` na Core ou revert de
manifest; `docker compose` recreate do MFE/API com imagem anterior; `.env` S2S
reversível (remover `engineering-api` de `S2S_ALLOWED_CLIENTS`); sem remoção de
dados, sem revogação de grants legados. Risco baixo — componentes aditivos.

## 12. Condições de interrupção (permanecem de pé)

Rollback imediato se: remoteEntry 404/5xx persistente; eng-api sem health;
S2S `S2S_CLIENT_DENIED`/`S2S_TOKEN_INVALID` recorrente; regressão no legado
`/apps/dashboard-lmps`; vazamento de dados/segredos.

## 13. Pendências e próximo gate

- Browser-check formal + paridade de dados prod: com operador/usuário autorizado.
- `engineering.manage` não existe na Core prod — avaliar se algum fluxo admin
  futuro o exige antes de criar (hoje não é usado).
- Residual config: vars legadas `API_DELPI_INTERNAL_SERVICE_TOKEN`/`S2S_*`
  genéricas no env do eng-api (não utilizadas) — cleanup transversal do doc 37 §5.
- `delpi-external-data-scheduler` unhealthy — fora de escopo (PROC-0076).
- Gate NC permanece **fora de escopo** — legado intacto; não avançar para
  G6–G9 automaticamente. Retornar à EVA — Coordenação.

## 14. Veredicto proposto

**`ACCEPT_WITH_RESIDUAL`** — Portal Engenharia/LMPs disponível em produção com
artefato rastreável bit-a-bit, Core/Keycloak/S2S provisionados e verificados,
cadeia autenticada real comprovada ponta a ponta, legado preservado e zero
cutover. Residuais: browser-check formal e paridade prod pendentes de sessão
autorizada; cold-start timeout TOTVS observável (não mascarado); warnings
pré-existentes de lint/CSS.
