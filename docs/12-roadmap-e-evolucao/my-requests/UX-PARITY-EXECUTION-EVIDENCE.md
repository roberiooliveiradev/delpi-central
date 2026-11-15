# UX parity — evidência de execução (HML)

> **PO visual review — 15/11/2026:** o pacote acima passou no E2E anterior, mas as screenshots de aceite revelaram **gap visual residual**: controles renderizados fora do Hero e cabeçalhos sem ordenação perceptível/validada. O plano de correção executável está em [UX-V2-HERO-TABLE-HELPDESK-PARITY-CORRECTION-PLAN.md](./UX-V2-HERO-TABLE-HELPDESK-PARITY-CORRECTION-PLAN.md). Portanto o aceite visual final fica **PENDING** até correção, E2E com clique real e verificador independente. O histórico de evidências abaixo permanece válido para o escopo executado, sem reinterpretar PASS como aceite dos novos critérios.

> **TASK_ID:** `MYREQ-HELPDESK-PLUGIN-UI-CROSS-MFE-UX-IMPLEMENTATION-HML-01`
> **Data:** 15/11/2026 · **Branch:** `main` · **Ambiente:** HML (`delpi-hml`, srv-api)
> **Documento de intenção:** `UX-PARITY-HELPDESK-PLUGIN-UI-TWO-MFES.md` (este arquivo é evidência, não intenção)

## 1. Entrega

| Item | Valor |
|---|---|
| BASE_HEAD | `26c35d2a` |
| FINAL_MAIN_SHA | `1696ce51c1` |
| Commits | `8553acecab` (feat kit + migração + shell + sort API), `58ca532df7` (fix card href), `1696ce51c1` (dedup títulos) |
| HML checkout | `/home/operador/projetos-teste/delpi-central` @ `1696ce51c1` |

## 2. O que foi entregue

**Plugin UI** — `DashboardListTools.tsx` + `dashboard-list-tools.css`:
`createDashboardFilterRulesBuilder`, `createDashboardSortLevelsBuilder`,
`createDashboardToolbarPopover`, `newDashboardFilterRuleId` — exportados de
`components/data/index.ts`; CSS via `styles.css` (classes `delpi-ui-*`).

**Helpdesk** — builders locais viraram adaptadores sobre os factories do kit
(`TicketListFilterBuilder`, `TicketListSortBuilder`, `HelpdeskListToolbarPopover`);
modelos/catálogos GLPI, serialização e tooltips preservados; CSS morto removido;
shim estendido; 3 bugs latentes de tipos corrigidos.

**My Requests** — `RequestListShell` compartilhado por Minhas e Fila:
hero compacto com caminho (eyebrow) + hint `?` no título, busca debounced 300ms,
filtros em regras AND, chips de status/escopo, ordenação, colunas persistidas,
Tabela|Cards (cards default em ≤768px), URL state completo, merge honesto
Requests+PRC com janela limitada e navegação por origem. Nova/Admin com hero
compacto sem barras de filtro. Dedup de títulos (nav → caminho → hero).

**Requests API** — `sort=field:dir[,…]` (até 3 níveis, whitelist
`created_at/updated_at/request_number/status/type_code/branch`, default
`created_at:desc`) em `/v1/requests/mine` e `/v1/requests/work-queue`;
parser de domínio; `invalid_sort` → 422; ORDER BY fixo + desempate por id
(Postgres) e ordenação estável equivalente (memory); ordenação antes da página;
retrocompatível.

## 3. Verificação local

| Gate | Resultado |
|---|---|
| plugin-ui vitest | 2643 passed (incl. `DashboardListTools.test.tsx` 6/6) |
| plugin-ui build | OK |
| helpdesk typecheck | exit 0 |
| helpdesk vitest | 281/282 — 1 fail pré-existente (`helpTooltips` budget `listUi.myTickets`, fora do diff) |
| helpdesk build | OK |
| my-requests typecheck | exit 0 |
| my-requests vitest | 218/220 — 2 fails pré-existentes (`ProcessIssuePayloadPanel`, fora do diff); 27 testes novos |
| my-requests build | OK |
| requests-api sort tests | 5/5 (`test_request_list_sort.py`, venv `eva-venv`) |
| requests-api suíte | 262/264 — 2 fails pré-existentes (`test_request_use_cases`, fora do diff) |
| `test_audit_architecture_phase3.py` | 22 OK |
| `audit_platform_guardrails.py --check` | 0 findings |
| delpi-verifier (2 rodadas) | ACCEPT_WITH_RESIDUAL após OC-1 (shim helpdesk) corrigida |

## 4. Deploy HML

Ordem API → remote → MFE: `requests-api` → `plugin-ui` → `my-requests`
(`up-hml-sequential.sh --build`).

| Serviço | Imagem nova | Rollback tag |
|---|---|---|
| requests-api | `sha256:1f2fa9cc57ee` (healthy) | `delpi-hml/requests-api:rollback-ux-v2-20261115` (b4e8228b02cc) |
| plugin-ui | `sha256:6b2fee71dc9c` (healthy) | `delpi-hml/plugin-ui:rollback-ux-v2-20261115` (3532cc3001a0) |
| my-requests | `sha256:17145e6867a0` (healthy) | `delpi-hml/my-requests:rollback-ux-v2-20261115` (d80842b10bf9) |

Artefato verificado: `request_list_sort.py` e `sort` Query param no container;
`style-CT-B9CIT.css` com classes list-tools; `__federation_expose_Index-*.js`
exporta `createDashboardFilterRulesBuilder`; bundle MFE `App-*.js` com UX V2.
Rotas `/v1/requests/mine|work-queue` fail-closed 401 sem token.

## 5. E2E HML (Chromium real, usuário `hml-tester`)

Spec versionada: `plugins/my-requests/e2e/specs/ux-v2.spec.ts` (harness em
`~/myreq-e2e-run` na VM). **16/16 PASS** — desktop, mobile, tablet, mobile-320:

- mine: hero + toolbar + popovers Filtros/Ordenar abrem/fecham;
- mine: busca serializa `?q=` na URL;
- work-queue: mesma experiência + sort parametrizado;
- new + admin: hero compacto, zero barras de filtro;
- todo teste: zero pageerrors + zero chamadas `/apps/api-delpi/*`.

**Bug real capturado pelo E2E** (mobile-320): página em branco no modo Cards —
`DataRecordCard` recebia `href=""` para rows requests-api (`destination` vazio)
→ `isSafeNavigationHref` lançava exceção e derrubava a árvore. Fix `58ca532df7`:
href resolve a origem no render + regressão estrutural.

**Dedup de títulos** (`1696ce51c1`): a página exibia o nome 3× (PageHeader +
hero + seção); agora nav → eyebrow «Início / Minhas solicitações» → hero, e a
ajuda da seção virou tooltip `?` no título do hero (padrão Helpdesk).

## 6. Limitações e riscos residuais

- **Helpdesk não consta no inventário HML** (`docker-compose.hml.yml` sem
  serviço `helpdesk`) — migração validada por testes/build/typecheck locais;
  E2E HML do Helpdesk: `TEST_NOT_RUN`.
- Work-queue do `hml-tester`: fila renderiza (4 pendências); cobertura de
  permissões negativas (403 real) não exercitada — `TEST_NOT_RUN`.
- Temas dark, zoom 200%, screen reader: cobertos parcialmente por contratos do
  kit/testes estruturais; sweep visual manual pendente.
- Splash do portal (`AppHostLoadingScreen`) aparece em fade nos screenshots —
  comportamento do host, não do diff.
- Falhas pré-existentes citadas em §3 não são deste escopo.
- `delia-api/` WIP concorrente preservado no working tree (não commitado).

## 7. Rollback

```
docker tag delpi-hml/<svc>:rollback-ux-v2-20261115 delpi-hml/<svc>:local
docker compose -f infra/docker-compose.hml.yml up -d --no-deps <svc>
```

Sem migrations, sem writes de negócio, sem TOTVS, sem grants RBAC.
`PRD_DEPLOY=NOT_EXECUTED`.

## 8. delpi-verifier (verificação independente)

Motor `cursor` (Composer), executor `swe-2-high` — independência OK.

| Rodada | Escopo | Veredito |
|---|---|---|
| 1 | `working tree` | ordens de correção (OC-1: shim Helpdesk sem tipos do kit) |
| 2 | `working tree` | `ACCEPT_WITH_RESIDUAL` — OC-1 corrigida |
| 3 | `fb81da0a96..f0da9a0666` | `ACCEPT_WITH_RESIDUAL` |

Rodada 3 confirma: typecheck/build `my-requests` exit 0; structural
`MyRequestsListUx` 13/13; `DashboardListTools` 6/6 no plugin-ui; shim
Helpdesk `typecheck` exit 0 (OC-1 mantida corrigida); sort whitelisted
com desempate `r.id ASC` confirmado em código. Não verificável pelo
verificador: E2E HML (contrato proíbe SSH/deploy) e pytest `requests-api`
(ambiente sem `delpi_auth` no PYTHONPATH) — ambos executados pelo executor
com evidência nas seções 3 e 5.

Residual da rodada 3: `audit_platform_guardrails --base fb81da0a96` falha
com 27 findings em `controllership-finance/src/index.css` — commit
concorrente `88f10f1e0b` de outro executor, fora deste escopo (DR-1
registrado; arquivos `my-requests` do executor sem findings novos).
