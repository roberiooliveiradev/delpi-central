# E11.S5 — Deploy federado e Runtime Gate — Estoque de Segurança (WF-16)

> **Status:** `E11_DEPLOY_STATUS = PASS_DEPLOYED` · `GATE-FEATURE E11 = INCONCLUSIVE` (smoke autenticado e QA visual sem sessão real).
> **Revisão GPT E11.S4:** `553a19a0e8a3b375b7f71b934e5dfa4be63e8c8e` — `E11_S5_READY_TO_AUTHORIZE=YES`; autorização de deploy recebida nesta task.

## Baseline

- BASE HEAD: `d849f53abc` → rebase ff para `553a19a0e8` (origin/main; divergência = docs + revisão GPT somente).
- Produção antes do deploy: SHA `284998fbf0` (repo srv-api), imagens `infra-supplies-api:289c0c45` e `infra-supplies:67ad9c89`.
- SOURCE/DEPLOY SHA: `553a19a0e8a3b375b7f71b934e5dfa4be63e8c8e` (contém E11.S1–S4: `9ca161a4`, `b93fc084`, `d849f53a` + revisão).

## Inventário de erros (S5.A)

| Erro | Arquivo | Regra | Classe |
|---|---|---|---|
| fast-refresh export | `app/SuppliesSessionContext.tsx:84` | react-refresh/only-export-components | PREEXISTING_OTHER_SCOPE (set/26) |
| memoization | `features/analytics/OtdAnalyticsPage.tsx:67` | react-hooks/preserve-manual-memoization | PREEXISTING_OTHER_SCOPE |
| `_branches` unused | `features/deliveries/query.ts:38` | no-unused-vars | PREEXISTING_OTHER_SCOPE |
| `\_"` escapes | `features/help/userManual.structural.test.ts:101` ×2 | no-useless-escape | PREEXISTING_OTHER_SCOPE |
| `\_"` escapes | `features/purchase-orders/PurchaseOrders.structural.test.ts:223,233` ×4 | no-useless-escape | PREEXISTING_OTHER_SCOPE |
| `_branches` unused | `features/purchase-orders/query.ts:24` | no-unused-vars | PREEXISTING_OTHER_SCOPE |

Todos pré-E11 (commits de set/2026), sem relação causal com E11 → **P2, documentados**; não corrigidos por conveniência.
`LINT_GLOBAL = FAIL_BASELINE` (10 erros/22 warnings) · `LINT_E11 = PASS` (`safety-stock/` = 0) · `LINT_DELTA = 0`.

## Testes pré-deploy (HEAD `553a19a0`)

- `supplies-api` pytest: **505 pass / 21 skip**.
- `plugins/supplies` vitest: **430 pass** · `tsc -b` PASS · `vite build` PASS.
- Regressões E10/overview intactas (suíte completa verde).

## Deploy executado (srv-api `operador@192.168.1.237:~/projetos/delpi-central`)

1. `git pull --ff-only` → `284998fb` → `553a19a0`.
2. `./infra/scripts/up-prod-sequential.sh --fase api --build supplies-api` → imagem **`aa60c1c3c36d`**, container `delpi-supplies-api` healthy.
3. `./infra/scripts/up-prod-sequential.sh --fase mfe --build supplies` → imagem **`6f01d3dc5678`**, container `delpi-supplies` up.

Ordem BFF→MFE respeitada; nenhum serviço não relacionado reconstruído.

## Verificação de versão implantada (S5.F)

| Item | Valor |
|---|---|
| DEPLOY_SHA | `553a19a0e8a3b375b7f71b934e5dfa4be63e8c8e` |
| BFF IMAGE_ID | `aa60c1c3c36d` (antes `289c0c45`) |
| MFE IMAGE_ID | `6f01d3dc5678` (antes `67ad9c89`) |
| REMOTE_BUNDLE | `/apps/supplies/assets/remoteEntry.js` via gateway → 200, md5 `3310dd178e40268e7007546f1ccf48f1` (idêntico ao do container) |
| Código novo no container BFF | `_require_safety_stock_dict` presente (def + 5 call sites) |
| Bundle MFE contém | `Ver detalhes`, `Falta comprar`, `Ruptura`, `Fornecedores vinculados`, `itemBranch`, `invalidResponse`, nova seção do Manual |

## Smoke de backend (S5.G) — anônimo via gateway

`GET /apps/supplies-api/safety-stock/{filters,summary,items,items/{code}/details,items/{code}/suppliers}` → **401 em todas** (AuthZ fail-closed, rotas registradas no serviço novo).

Cenários autenticados (403 sem capability, `branch=01/02/all`, 422 filial inválida, 404 produto, payload shape): **INCONCLUSIVE** — sem sessão real autorizada; não simulado.

## Smoke federado autenticado / visual (S5.H/I/J)

`AUTHENTICATED_SMOKE = INCONCLUSIVE` · `VISUAL_DESKTOP/MOBILE = INCONCLUSIVE` · `LIGHT_DARK = INCONCLUSIVE` · `KEYBOARD_FOCUS = INCONCLUSIVE` · `HELP_RUNTIME = INCONCLUSIVE` (Manual novo está no bundle servido — verificado por string; renderização visual não comprovada sem sessão).

## Observabilidade (S5.K)

- `delpi-supplies-api` healthy; logs pós-boot limpos (gunicorn up, zero error/traceback).
- `delpi-supplies` up; gateway healthy; `nginx -t` OK.

## Rollback (S5.L)

- Repo srv-api: `git checkout 284998fbf0` + rebuild, **ou** restaurar imagens `infra-supplies-api:289c0c45` / `infra-supplies:67ad9c89` (`docker tag` + `compose up -d`).
- Gatilhos de rollback não ocorreram; `ROLLBACK_EXECUTED = NO`.
- Sem migrations / sem escrita ERP envolvidas.

## GATE-FEATURE E11

| Item | Estado |
|---|---|
| E11_SOURCE_IN_HEAD | PASS |
| E11_BFF_BUILD / E11_MFE_BUILD | PASS |
| E11_TESTS / E11_LINT_DELTA / E11_HELP | PASS |
| E11_DEPLOY_BFF / E11_DEPLOY_MFE / E11_BUNDLE_VERIFIED | PASS |
| E11_API_SMOKE | PASS (401 anônimo em todas as rotas) |
| E11_AUTHENTICATED_SMOKE | INCONCLUSIVE |
| E11_VISUAL_* / LIGHT_DARK / KEYBOARD_FOCUS | INCONCLUSIVE |
| E11_REGRESSION | PASS (suítes verdes; demais serviços intactos) |
| E11_ROLLBACK_READY | PASS |

**`GATE-FEATURE E11 = INCONCLUSIVE`** — falta jornada federada autenticada + QA visual para PASS. Nenhum deploy/falha material pendente.

## Residuais

- Smoke autenticado desktop/mobile, claro/escuro, teclado — dependem de sessão real do PO.
- 10 erros de lint preexistentes fora de E11 (P2, roteados por owner de feature).
- `peer_branch_stock` segue TO_INVENTORY.

## Próxima etapa

Sessão autenticada com usuário autorizado executando a jornada S5.H; ao PASS, fechar `GATE-FEATURE E11 = PASS` e atualizar README/PLAN.


## Revisão GPT — E11.S5 (2026-10-24)

**Veredito: `ACCEPT_WITH_RESIDUAL`** para publicação técnica; **`E11_DEPLOY_STATUS=PASS_DEPLOYED`**, **`GATE-FEATURE E11=INCONCLUSIVE`**. Conferido o relatório versionado em `e504b65c76`, com `SOURCE/DEPLOY_SHA=553a19a0e8a3b375b7f71b934e5dfa4be63e8c8e`, imagens BFF/MFE e hash do bundle federado relatados. Health, gateway e smoke 401 das cinco rotas são evidência operacional reportada pelo executor e registrada no relatório; não houve sessão produtiva autenticada disponibilizada ao GPT para reexecutar os checks.

**Gate pendente:** executar com identidade autorizada efetiva as consultas `branch=all|01|02`, filtros, resumo, paginação, ordenação, detalhe por `product_code+branch`, fornecedores, F5/back, 401/403/422/404 quando aplicáveis, Help renderizada, desktop/mobile, claro/escuro e teclado/foco. Registrar URLs/horários e evidências sanitizadas. Não equiparar 401 anônimo a funcionamento autenticado nem declarar `PASS` inferido. Se indisponível, conservar `INCONCLUSIVE` e não iniciar página seguinte com dependência de gate fechado.

**Residuais de manutenção:** dez erros de lint anteriores a E11 continuam `PREEXISTING_OTHER_SCOPE`; `peer_branch_stock=TO_INVENTORY`. O cabeçalho antigo de `IMPLEMENTATION-PLAN.md` ainda contém status histórico de E10 e a frase 'não iniciar E11'; harmonizar a visão atual com a cronologia documentada em task documental bounded, sem reescrever evidências históricas. **Nenhum novo deploy/código nesta revisão.**
