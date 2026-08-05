# Homologação — paridade Portal do Vendedor → Portal Comercial

Checklist viva derivada do playbook [§ 2.1.1](./PLAYBOOK-MODULO-COMERCIAL.md#211-gate-de-paridade--pedidos-venda-abertos--portal-comercial).

**Donos:** Comercial + QA  
**Gate de depreciação:** todas as linhas ✅ antes de ocultar `pedidos-venda-abertos` ([F2C-CUTOVER-RUNBOOK.md](./F2C-CUTOVER-RUNBOOK.md)).

**Estado técnico (engenharia, ago/2026):** implementado no MFE `plugins/commercial` — aguarda assinatura Comercial/QA nas colunas Status.

---

## Capacidades

| Capacidade do Portal do Vendedor | Evidência no Portal Comercial | Status |
|----------------------------------|-------------------------------|--------|
| Lista de pedidos em aberto (TOTVS) | `/apps/commercial/open-orders` + filtros (busca, filial, status) + export CSV | [ ] |
| Ops abertas / indicadores operacionais equivalentes | Banner/lista OPs em open-orders (`list_ops_abertas_pedidos_venda`) | [ ] |
| Minha carteira / lista de clientes | `/apps/commercial/customers` + enrichment + filtro admin | [ ] |
| Detalhe / check-up do cliente | `/apps/commercial/customers/:codigo/:loja` (pedidos + faturamento/NF + avatar) | [ ] |
| Configuração de vendedores e carteiras (admin) | `/apps/commercial/seller-portfolios` via `commercial-api` | [ ] |
| Avatar de cliente | GET/PUT/DELETE `/apps/commercial-api/customers/{code}/{store}/avatar` | [ ] |
| Deep links `codigo`+`loja` | Rotas commercial; redirects PVA documentados no runbook F2c | [ ] |
| Permissões (access / admin) mapeadas | `commercial.accounts.view` / `commercial.seller-portfolios.manage` (+ aliases) | [ ] |
| Favoritos / URLs antigas | Snippet [commercial-f2c-redirects.conf](../../../gateway/snippets/commercial-f2c-redirects.conf) — ativar no flip | [ ] |

---

## Evidências por área (preencher na homologação)

### Pedidos em aberto

- [ ] Lista carrega via `/apps/api-delpi/pedidos-venda-abertos/`
- [ ] Colunas essenciais: pedido, cliente, produto, quantidade, status, filial
- [ ] Escopo de carteira respeitado (`sellerIdFilter` / minha carteira)
- [ ] Filtros + export CSV

### Carteira / clientes

- [ ] `GET /apps/commercial-api/seller-portfolios/me`
- [ ] Enrichment via `POST /apps/commercial-api/customers/enrichment`
- [ ] Deep link abre detalhe com código + loja
- [ ] Série faturamento + NF no detalhe

### Admin carteiras

- [ ] `GET/POST /apps/commercial-api/seller-portfolios`
- [ ] Transferência `POST /seller-portfolios/transfer` (+ `reason_note`)
- [ ] Busca TOTVS + directory users
- [ ] RBAC `commercial.seller-portfolios.manage` (403 sem permissão)

### RBAC e cutover

- [ ] `commercial.accounts.view` cobre rotas principais
- [ ] Alias legado `pedidos-venda-abertos.access` documentado
- [ ] Alias legado `pedidos-venda-abertos.admin` → manage
- [ ] `COMMERCIAL_PORTFOLIO_SOURCE=commercial` após backfill

### UX / infra

- [ ] MFE federado: `/apps/commercial/assets/remoteEntry.js`
- [ ] Header `X-Delpi-Caller-App: commercial`
- [ ] Tema claro/escuro no portal federado
- [ ] Mobile (≤768px) sem scroll horizontal involuntário
- [ ] Manifest registrado (`plugins/commercial/scripts/register-manifest.sh`)

---

## Registro de homologação

| Data | Ambiente | Responsável | Resultado | Observações |
|------|----------|-------------|-----------|-------------|
| | | | | |

---

## Referências

- [PLAYBOOK-MODULO-COMERCIAL.md](./PLAYBOOK-MODULO-COMERCIAL.md)
- [F2C-CUTOVER-RUNBOOK.md](./F2C-CUTOVER-RUNBOOK.md)
- [ADR-002](./adr/ADR-002-deprecar-pedidos-venda-abertos.md)
- Plugin: `plugins/commercial/README.md`
