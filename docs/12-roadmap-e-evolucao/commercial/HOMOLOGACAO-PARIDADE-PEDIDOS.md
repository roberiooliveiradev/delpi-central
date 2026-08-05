# Homologação — paridade Portal do Vendedor → Portal Comercial

Checklist viva derivada do playbook [§ 2.1.1](./PLAYBOOK-MODULO-COMERCIAL.md#211-gate-de-paridade--pedidos-venda-abertos--portal-comercial).

**Donos:** Comercial + QA  
**Gate de depreciação:** todas as linhas ✅ antes de ocultar `pedidos-venda-abertos`.

---

## Capacidades

| Capacidade do Portal do Vendedor | Evidência no Portal Comercial | Status |
|----------------------------------|-------------------------------|--------|
| Lista de pedidos em aberto (TOTVS) | Tela `/apps/commercial/open-orders` + filtros essenciais | [ ] |
| Ops abertas / indicadores operacionais equivalentes | Equivalente ou superior documentado | [ ] |
| Minha carteira / lista de clientes | Tela `/apps/commercial/customers` | [ ] |
| Detalhe / check-up do cliente | Tela `/apps/commercial/customers/:codigo/:loja` | [ ] |
| Configuração de vendedores e carteiras (admin) | Tela `/apps/commercial/seller-portfolios` via `commercial-api` | [ ] |
| Avatar de cliente | Avatar via `GET /apps/commercial-api/customers/{code}/{store}/avatar` | [ ] |
| Deep links `codigo`+`loja` | Rotas preservadas no Portal Comercial | [ ] |
| Permissões (access / admin) mapeadas | `commercial.accounts.view` / `commercial.seller-portfolios.manage` + 403 | [ ] |
| Favoritos / URLs antigas | Redirect ou período de convivência documentado | [ ] |

---

## Evidências por área (preencher na homologação)

### Pedidos em aberto

- [ ] Lista carrega via `/apps/api-delpi/pedidos-venda-abertos`
- [ ] Colunas essenciais: pedido, cliente, produto, quantidade, status, filial
- [ ] Escopo de carteira respeitado (seller portfolio)

### Carteira / clientes

- [ ] `GET /apps/commercial-api/seller-portfolios/me`
- [ ] Enrichment via `POST /apps/commercial-api/customers/enrichment`
- [ ] Deep link abre detalhe com código + loja

### Admin carteiras

- [ ] `GET/POST /apps/commercial-api/seller-portfolios`
- [ ] Transferência de clientes (stub/UI → API)
- [ ] RBAC `commercial.seller-portfolios.manage` (403 sem permissão)

### RBAC e cutover

- [ ] `commercial.accounts.view` cobre rotas principais
- [ ] Alias legado `pedidos-venda-abertos.access` documentado para cutover
- [ ] Alias legado `pedidos-venda-abertos.admin` → `commercial.seller-portfolios.manage`

### UX / infra

- [ ] MFE federado: `/apps/commercial/assets/remoteEntry.js`
- [ ] Header `X-Delpi-Caller-App: commercial`
- [ ] Tema claro/escuro no portal federado
- [ ] Mobile (≤768px) sem scroll horizontal involuntário

---

## Registro de homologação

| Data | Ambiente | Responsável | Resultado | Observações |
|------|----------|-------------|-----------|-------------|
| | | | | |

---

## Referências

- [PLAYBOOK-MODULO-COMERCIAL.md](./PLAYBOOK-MODULO-COMERCIAL.md)
- [API-ROUTES.md](./API-ROUTES.md)
- [WIREFRAMES.md](./WIREFRAMES.md)
- Plugin: `plugins/commercial/README.md`
