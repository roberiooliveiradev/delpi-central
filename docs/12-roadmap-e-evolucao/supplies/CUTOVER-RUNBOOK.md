# CUTOVER-RUNBOOK — Portal Suprimentos

**Não executar nesta etapa.** Pré-requisito: [HOMOLOGACAO-PARIDADE.md](./HOMOLOGACAO-PARIDADE.md) + [ADR-003](./adr/ADR-003-legacy-app-consolidation.md).

Modelo: coexistência → equivalente → paridade → homologar → redirect/alias → ocultar launcher → período de segurança → remover com ADR.

---

## 0. Pré-check

- [ ] `supplies-api` e MFE `supplies` estáveis em prod
- [ ] Aliases RBAC resolvendo no BFF
- [ ] Smoke: home, overview, SC, ESTSEG, 360, help, 403 filial
- [ ] Favoritos Core ainda apontam para legado **até** o flip
- [ ] Snippet nginx preparado (não ativo antes do GO)

## 1. Redirects (quando GO)

Espelho `gateway/snippets/commercial-f2c-redirects.conf`:

| De | Para |
|----|------|
| `/apps/dashboard-supplies` | `/apps/supplies/overview` |
| `/apps/dashboard-supplies/cpv` | `/apps/supplies/overview?focus=cpv` (ou rota de foco) |
| `/apps/dashboard-supplies/otd` | `/apps/supplies/suppliers/otd` |
| `/apps/dashboard-supplies/stock` | `/apps/supplies/inventory` |
| `/apps/dashboard-supplies/inventory-turnover` | `/apps/supplies/inventory?tab=turnover` |
| `/apps/dashboard-supplies/negotiation-savings` | `/apps/supplies/negotiations` |
| `/apps/purchase-requests` | `/apps/supplies/purchase-requests` |
| `/apps/estoque-seguranca` | `/apps/supplies/safety-stock` |
| `/apps/estoque-seguranca/analise-consumo` | `/apps/supplies/safety-stock/consumption-analysis` |

Query strings de filtro: mapear 1:1 quando os nomes coincidirem; documentar perda se houver.

BIs: **só** se E1.S1 tiver path Core.

## 2. Sequência prod (esboço)

```bash
./infra/scripts/up-prod-sequential.sh --pull --build gateway
./infra/scripts/up-prod-sequential.sh --build supplies-api
./infra/scripts/up-prod-sequential.sh --build supplies
# unregister launcher legado (apps.manage) — um app por vez
# smoke 302
```

**Não** apagar SQL api-delpi nem schema `purchase_requests` no mesmo dia. **Não** `docker compose` em lote. **Não** reset de migrations.

## 3. Rollback

Desligar snippet de redirect; re-registrar manifesto legado; supplies permanece no ar.

## 4. Período de segurança

Mínimo alinhado ao Comercial (combinar com PO; sugerido 2–4 semanas). Só então remover Compose/código com atualização do ADR-003 para **executado**.

## 5. RBAC

Manter aliases até limpeza de papéis. Não quebrar `purchase-requests.unit.filial-01` no flip.
