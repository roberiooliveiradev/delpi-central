# E9 / WF-07 — smoke federado live (GATE-FEATURE)

- Data: 2026-09-21
- Ambiente: Portal de produção `https://minhadelpi.com.br` (jornada no shell, MFE federado)
- Baseline código (smoke): `9b5cc1ae2102c04a4ab740b6f25df3eded6457b3` (= `origin/main` no momento do gate)
- Commits de evidência/docs: `4acef0976e` + `542fc1dbc6` (docs only; sem mudança de produto)
- Commit E9.S4 (Help/URL) ancestral: `9a772992b8`
- Commit E9.S2 (BFF) ancestral: `22c32e7173`

## Deployment identity

| Artefato | Evidência |
|---|---|
| MFE Supplies (prod) | `App-C2Qj6Ude.js` + `__federation_expose_App-BXO3fGL4.js`; `Last-Modified: Mon, 21 Sep 2026 18:23:42 GMT` |
| Hash MFE | MD5 `App-C2Qj6Ude.js` = `5dba1b51ccc715e5e63db97b81ee0d11` — **idêntico** ao `plugins/supplies/dist` rebuildado no HEAD |
| Conteúdo E9 no bundle | Contém `deliveries/late` e `Entregas / Atrasos`; sem `atrasos do dia` |
| supplies-api (prod) | Rota autenticada `GET /apps/supplies-api/deliveries/late` → **404** `{detail:"Not Found", code:"not_found"}` |
| supplies-api (sem sessão) | Mesmo path → **401** `{detail:"Unauthorized"}` (auth global; path não materializa composição E9) |
| Container local `delpi-supplies` | **STALE** — `App-omdSFLt9.js` / `Last-Modified: Fri, 18 Sep 2026 17:35:18 GMT` (pré-E9 MFE). Não usado como prova deste gate |
| Container local `delpi-supplies-api` | Bind-mount do código HEAD; tem `deliveries_routes.py`; pytest PASS |

Conclusão de identidade: o **MFE de produção contém E9.S3/S4**. O **BFF de produção não entrega** `GET /deliveries/late` (404 pós-auth). Stack E9 incompleta no runtime federado.

## Suites de código (pré-smoke)

### Backend (`delpi-supplies-api`, código HEAD via bind-mount)

```bash
docker exec -w /app delpi-supplies-api python -m pytest \
  tests/application/test_late_deliveries_composition.py \
  tests/interface/http/test_deliveries_bff.py \
  tests/interface/http/test_purchase_orders_bff.py -q
```

Resultado: **41 passed**.

### MFE

```bash
cd plugins/supplies && npm test -- --run && npm run build
```

Resultado: **32 files / 156 tests PASS**; `tsc -b && vite build` PASS (`App-C2Qj6Ude.js`).

### plugin-ui

Commits em `plugins/plugin-ui` após E9.S4 (sala/collaboration/tasks) existem no HEAD. Dirty tree local adicional em tasks. Smoke federado **não** apresentou `is not a function` / factory failure do kit na página Entregas; a UI renderizou FilterBar/PageHero/estados. Residual: dirty local de `plugin-ui` não faz parte do artefato prod testado.

## Jornada federada

```text
Portal → Suprimentos → /apps/supplies/deliveries
```

Identidade: `user` / (credencial de smoke já usada no gate E8; não persistida).

### Happy path / UI

- Shell íntegro; remote federado carrega; **não** é placeholder.
- Título **Entregas / Atrasos**; filtros Unidade / Período de digitação / Situação.
- Default observado: Situação **Em atraso**; período **Este mês** (`2026-09-01` → `2026-09-21`).
- Resumo mostra `—` (sem payload).
- Banner de erro: `[not_found] Not Found` + botão **Tentar novamente**.
- Tabela «Recebimentos MP» sem linhas (falha upstream, não empty 200).

### Rede

- Browser chama somente `GET /apps/supplies-api/deliveries/late?...`.
- **ZERO** chamada browser → `/api-delpi` ou `/supplies/purchase-order-otd`.
- Todas: request **sem** `branch` (correto).
- Deep link `branch=01&status=on_time&sort_by=expected_delivery_date&sort_dir=desc` preservado na URL; request coerente; resposta **404**.

### URL / F5 / histórico

| Caso | Resultado |
|---|---|
| Deep link completo | URL e query BFF coerentes |
| F5 | Mantém `branch=01`, `status=on_time`, sort |
| Back / Forward entre deep links | Restaura estados A↔B |

### Help / discoverability

| Superfície | Resultado |
|---|---|
| Manual `/help` | Quero «acompanhar entregas atrasadas»; FAQ diferencia Entregas; sem «atrasos do dia»; cita digitação |
| Início | Menciona Entregas; busca «atraso» encontra |
| Manifest `showInMenu=false` | Página alcançável via Início/Ajuda/URL |

### NO DRILL

Zero `a[href*='/purchase-orders/']` na página. Pedido não é link.

### Auth

| Caso | Resultado |
|---|---|
| Sem sessão (deep link) | Redireciona `/login` |
| BFF sem bearer | 401 |
| 403 unidade | `INCONCLUSIVE` (só identidade autorizada; padrão E8) |

### Empty / sort / pagination runtime

`INCONCLUSIVE` / não executáveis com dados: BFF 404 impede lista 200+empty, sort header e página 2.

Empty/state/retry **UI** observável via erro + «Tentar novamente» (estado de erro, não empty).

### Console

Erros `Failed to load resource: 404` nas chamadas BFF. Sem `TypeError` / federation factory error / React crash.

### Responsive / tema / teclado

- Desktop: OK estrutural.
- Mobile ~390px: título presente; residual sidebar Portal (igual E8).
- Tema dark: toggle não acionado no smoke → `INCONCLUSIVE`.
- Teclado: Tab move foco para `BUTTON`.

### Performance 01+02

Não observável (BFF 404 antes da composição). Residual para reteste pós-deploy da API.

## RQ coverage

| RQ | Runtime | Nota |
|---|---|---|
| RQ-E9-01 acesso | PASS parcial | Página abre com `supplies.access`; 403 unidade INCONCLUSIVE |
| RQ-E9-02 lista operacional | **FAIL** | BFF 404 — sem linhas/resumo |
| RQ-E9-03 unidade | PASS parcial | UI + query `branch`/Todas; dados não retornam |
| RQ-E9-04 período/status | PASS parcial | Defaults e query corretos; dados não retornam |
| RQ-E9-05 sort/paginação | INCONCLUSIVE runtime / PASS em testes | Sem dataset 200 |
| RQ-E9-06 NO DRILL | PASS | |
| RQ-E9-07 states | PASS parcial | loading/error/retry OK; empty 200 não provado |
| RQ-E9-08 Help | PASS | |
| RQ-E9-09 URL/F5 | PASS | |
| RQ-E9-10 AuthZ/BFF-only | PASS parcial | BFF-only no browser; AuthZ auto PASS; runtime BFF path 404 |

## Classificação

```text
GATE-FEATURE WF-07 = FAIL
```

Causa raiz material: **MFE E9 implantado em produção; supplies-api de produção não serve `GET /deliveries/late` (404 not_found pós-auth)**. Suites HEAD do BFF passam no container local com código montado.

Isso **não** autoriza E10 / WF-15.

## Residuais / próximo passo operacional (fora deste brief)

1. Deploy/rebuild de `supplies-api` em produção contendo E9.S2 (`deliveries_routes` + composition).
2. Reexecutar smoke federado (happy path 200, Todas, sort, pagination, empty, latência consolidado).
3. Atualizar este gate para PASS somente com evidência 200.

## Não persistido

JWT, cookies, tokens, senhas, dados comerciais de linhas.
