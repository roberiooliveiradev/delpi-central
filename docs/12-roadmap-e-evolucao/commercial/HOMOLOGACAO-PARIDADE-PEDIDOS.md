# Homologação — paridade Portal do Vendedor → Portal Comercial

Checklist viva derivada do playbook [§ 2.1.1](./PLAYBOOK-MODULO-COMERCIAL.md#211-gate-de-paridade--pedidos-venda-abertos--portal-comercial).

**Donos:** Comercial + QA  
**Gate de depreciação:** checklist abaixo + registro na tabela; F2c executado em ago/2026 ([F2C-CUTOVER-RUNBOOK.md](./F2C-CUTOVER-RUNBOOK.md)).

**Estado técnico (engenharia, ago/2026):** paridade F2b no MFE `plugins/commercial`; cutover F2c (redirects + menu oculto) aplicado no código / ambiente local.

---

## Capacidades

| Capacidade do Portal do Vendedor | Evidência no Portal Comercial | Status |
|----------------------------------|-------------------------------|--------|
| Lista de pedidos em aberto (TOTVS) | `/apps/commercial/open-orders` + filtros (busca, filial, status) + export CSV | [x] |
| Ops abertas / indicadores operacionais equivalentes | Banner/lista OPs em open-orders (`list_ops_abertas_pedidos_venda`) | [x] |
| Minha carteira / lista de clientes | `/apps/commercial/customers` + enrichment + filtro admin | [x] |
| Detalhe / check-up do cliente | `/apps/commercial/customers/:codigo/:loja` (pedidos + faturamento/NF + avatar) | [x] |
| Configuração de vendedores e carteiras (admin) | `/apps/commercial/seller-portfolios` via `commercial-api` | [x] |
| Avatar de cliente | GET/PUT/DELETE `/apps/commercial-api/customers/{code}/{store}/avatar` | [x] |
| Deep links `codigo`+`loja` | Rotas commercial; redirects PVA no snippet (desativados no nginx até flip RBAC) | [x] |
| Permissões (access / admin) mapeadas | `commercial.accounts.view` / `commercial.seller-portfolios.manage` (+ aliases) | [x] |
| Favoritos / URLs antigas | Snippet `commercial-f2c-redirects.conf` pronto; include nginx **comentado** até cutover | [x] |

---

## Evidências por área (preencher na homologação)

### Pedidos em aberto

- [x] Lista carrega via `/apps/api-delpi/pedidos-venda-abertos/`
- [x] Colunas essenciais: pedido, cliente, produto, quantidade, status, filial
- [x] Escopo de carteira respeitado (`sellerIdFilter` / minha carteira)
- [x] Filtros + export CSV

### Carteira / clientes

- [x] `GET /apps/commercial-api/seller-portfolios/me`
- [x] Enrichment via `POST /apps/commercial-api/customers/enrichment`
- [x] Deep link abre detalhe com código + loja
- [x] Série faturamento + NF no detalhe

### Admin carteiras

- [x] `GET/POST /apps/commercial-api/seller-portfolios`
- [x] Transferência `POST /seller-portfolios/transfer` (+ `reason_note`)
- [x] Busca TOTVS + directory users
- [x] RBAC `commercial.seller-portfolios.manage` (403 sem permissão)

### RBAC e cutover

- [x] `commercial.accounts.view` cobre rotas principais
- [x] Alias legado `pedidos-venda-abertos.access` documentado
- [x] Alias legado `pedidos-venda-abertos.admin` → manage
- [x] `COMMERCIAL_PORTFOLIO_SOURCE=commercial` após backfill

### UX / infra

- [x] MFE federado: `/apps/commercial/assets/remoteEntry.js`
- [x] Header `X-Delpi-Caller-App: commercial`
- [x] Tema claro/escuro no portal federado
- [x] Mobile (≤768px) sem scroll horizontal involuntário
- [x] Manifest registrado (`plugins/commercial/scripts/register-manifest.sh`)

---

## Registro de homologação

| Data | Ambiente | Responsável | Resultado | Observações |
|------|----------|-------------|-----------|-------------|
| 2026-08-06 | local/dev | Engenharia | ❌ F2c prematuro — rollback | Commercial open-orders sem paridade UX (KPIs/Excel/previsão OP); PVA restaurado no menu |
| 2026-08-06 | local/dev | Engenharia (plano F2c) | revertido | Cutover técnico desfeito até fechar gap |

---

## Comunicação (cutover)

Entrada canônica do domínio: **Portal Comercial** (`/apps/commercial`).  
URLs antigas de `/apps/pedidos-venda-abertos/*` redirecionam automaticamente **após** o flip F2c (include do snippet no gateway + RBAC `commercial.*`).  
Permissões legadas `pedidos-venda-abertos.access` / `.admin` continuam válidas como aliases.

---

## Referências

- [PLAYBOOK-MODULO-COMERCIAL.md](./PLAYBOOK-MODULO-COMERCIAL.md)
- [F2C-CUTOVER-RUNBOOK.md](./F2C-CUTOVER-RUNBOOK.md)
- [ADR-002](./adr/ADR-002-deprecar-pedidos-venda-abertos.md)
- Plugin: `plugins/commercial/README.md`
