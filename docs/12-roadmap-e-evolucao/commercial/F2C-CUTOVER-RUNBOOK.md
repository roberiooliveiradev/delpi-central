# F2c — runbook de cutover (MFEs legados → Portal Comercial)

**Pré-requisito:** [HOMOLOGACAO-PARIDADE-PEDIDOS.md](./HOMOLOGACAO-PARIDADE-PEDIDOS.md) + [ADR-002](./adr/ADR-002-deprecar-pedidos-venda-abertos.md).

**Status (set/2026):** MFEs `pedidos-venda-abertos` e `propostas-comerciais` **removidos** do monorepo e do Compose. UX canônica = Portal Comercial (`/apps/commercial/open-orders`, `/apps/commercial/proposals`, …). Redirects F2c **ativos** no gateway. Rotas TOTVS na **api-delpi** (`/pedidos-venda-abertos/*`, `/propostas-comerciais/*` / `/commercial-proposals/*`) **permanecem** — consumidas via **commercial-api**.

---

## Gap de UX (fechado em engenharia)

- [x] KPIs (pode faturar, parcial, atraso)
- [x] Filtros (cliente, status estoque, datas)
- [x] Tabela ~16 colunas + previsão OP FIFO + badges
- [x] Excel + column picker + fonte + sort/paginação
- [x] Carteira agregada + detalhe com abas
- [x] Admin carteiras via commercial-api
- [x] Propostas ADY (lista / detalhe / PDF) no Portal
- [x] Containers + código MFE removidos; redirects nginx ativos

## 0. Pré-check técnico

- [ ] `COMMERCIAL_PORTFOLIO_SOURCE=commercial` + backfill/reconcile
- [ ] Migration `V005__seller_portfolio_members` aplicada (`up` só — nunca `reset`)
- [ ] Smoke: open-orders, customers, detail, seller-portfolios, proposals
- [ ] Smoke multi-membro: usuário em 2 carteiras; `/me.portfolios[]`; filtro «Todas»

### Multi-membro (obrigatório)

Membership N:N vive **somente** em `commercial.seller_portfolio_members`. O schema legado `pedidos_venda_abertos.sellers` **não** é fonte de verdade.

## 1. Redirects (gateway)

Snippet ativo: [gateway/snippets/commercial-f2c-redirects.conf](../../../gateway/snippets/commercial-f2c-redirects.conf) (include em `nginx.conf` / `nginx.dev.conf`).

## 2. Produção — comandos (srv-api)

Executar **a partir da raiz do repo** (nunca `docker compose` em lote sem o script sequencial).

```bash
# 0) Pull do código com a remoção
cd /caminho/delpi-central
git pull --ff-only origin main

# 1) Rebuild gateway (redirects) + commercial (já canônico) — um serviço por vez
./infra/scripts/up-prod-sequential.sh --pull --build gateway
./infra/scripts/up-prod-sequential.sh --build commercial
# Se commercial-api também mudou no mesmo deploy:
./infra/scripts/up-prod-sequential.sh --build commercial-api

# 2) Parar e remover containers legados (se ainda existirem no host)
cd infra
docker compose -f docker-compose.yml --env-file .env stop pedidos-venda-abertos propostas-comerciais || true
docker compose -f docker-compose.yml --env-file .env rm -f pedidos-venda-abertos propostas-comerciais || true
docker rm -f delpi-pedidos-venda-abertos delpi-propostas-comerciais || true

# 3) Remover imagens órfãs dos MFEs (opcional)
docker images --format '{{.Repository}}:{{.Tag}} {{.ID}}' | grep -E 'pedidos-venda-abertos|propostas-comerciais' || true
# docker rmi <IMAGE_ID> …

# 4) Desregistrar do launcher (Core API) — JWT com apps.manage / superadmin
export TOKEN='…'   # ou: bash infra/scripts/get-prod-token.sh (se existir)
export BASE_URL='https://SEU_HOST'   # ou http://localhost via gateway

curl -fsS -X DELETE "$BASE_URL/core-api/admin/apps/pedidos-venda-abertos" \
  -H "Authorization: Bearer $TOKEN"

curl -fsS -X DELETE "$BASE_URL/core-api/admin/apps/propostas-comerciais" \
  -H "Authorization: Bearer $TOKEN"

# 5) Smoke redirects + rotas canônicas
curl -sI "$BASE_URL/apps/pedidos-venda-abertos" | head -n 5
# esperado: 302 → /apps/commercial/open-orders
curl -sI "$BASE_URL/apps/propostas-comerciais" | head -n 5
# esperado: 302 → /apps/commercial/proposals
curl -sI "$BASE_URL/apps/commercial/assets/remoteEntry.js" | head -n 5
# esperado: 200
```

**Não** apagar volume de avatares (`…/pedidos-venda-abertos/avatars`) nem rotas api-delpi — o Portal Comercial ainda usa.

**Não** rodar `run_plugins_migrations.py reset` no schema `pedidos_venda_abertos`.

## 3. Dev (WSL)

```bash
./infra/scripts/up-dev-sequential.sh --build gateway
./infra/scripts/up-dev-sequential.sh --build commercial
docker rm -f delpi-pedidos-venda-abertos delpi-propostas-comerciais || true
# unregister idem (TOKEN + BASE_URL=http://localhost)
```

## 4. Comunicação pós-flip

Entrada canônica = Portal Comercial; deep links antigos redirecionam; aliases RBAC `pedidos-venda-abertos.access` / `.admin` e `propostas-comerciais.view` podem permanecer como alias até limpeza de perfis.
