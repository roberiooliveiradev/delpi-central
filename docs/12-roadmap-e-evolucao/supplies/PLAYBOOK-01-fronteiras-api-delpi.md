# PLAYBOOK-01 — Fronteiras api-delpi × supplies-api

Espelho do [playbook comercial](../commercial/PLAYBOOK-01-fronteiras-api-delpi.md), **sem** copiar regra de carteira.

## Missão por camada

| Camada | Faz | Não faz |
|--------|-----|---------|
| **api-delpi** | SQL TOTVS, views, interpretação ERP, cache de query, permissões de rota TOTVS | Escopo CC Delpi, tarefas, notas, alertas, «portal settings», membership de comprador |
| **supplies-api** | BFF, RBAC do Portal, filial, composição, estado Delpi, gateway | Recalcular CPV/OTD/ESTSEG; escrever Protheus |
| **purchase-requests-api** | Até C3: escopo CC + jobs SC | KPIs gerenciais |
| **MFE supplies** | Render + capability | Fetch TOTVS; decidir filial sem o backend |

## Paths TOTVS que o BFF deve reusar (não clonar)

Ver [API-ROUTES.md](./API-ROUTES.md). Famílias: `/supplies/cpv|otd|stock-*|inventory-turnover|negotiation-savings|purchase-order-otd*|purchase-requests*|safety-stock*|stock-balances*` e `/products/{code}/parents|purchases|last-purchase|suppliers|stock|purchase-price-history`.

## Caller

`X-Delpi-Caller-App: supplies-api` (nunca o id do MFE, quando a chamada sai do BFF).

## Erros

Mapear 401/403/404/409/422/5xx do gateway para envelope da supplies-api. Timeout explícito. Retry só em GET idempotente. Sem logar JWT.

## Evolução de contrato

Breaking change em `data` TOTVS: política da api-delpi (`contract-evolution-backward-compatibility.mdc`). BFF não «conserta» campo no MFE com segundo significado.
