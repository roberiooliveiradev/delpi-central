# PLAYBOOK-01 — Fronteiras api-delpi × supplies-api

Espelho do playbook Comercial apenas como referência de boundaries, sem copiar regra de carteira nem framework.

## Missão por camada

| Camada | Faz | Não faz |
|---|---|---|
| **api-delpi** | SQL TOTVS, views, interpretação ERP, cache de query, contratos compartilháveis | escopo CC Delpi, tasks, notas, settings, membership do Portal |
| **supplies-api** | BFF, authz do Portal com effective permissions Core-first, unidade, composição, estado Minha DELPI, gateways | recalcular CPV/OTD/ESTSEG; escrever Protheus; confiar em permission claims JWT |
| **purchase-requests-api** | até **C2**: owner do escopo CC + jobs SC; em C2 transfere ownership | KPIs gerenciais; permanecer como hop eterno após C3 |
| **MFE supplies** | render, navegação e UX capability-driven | fetch TOTVS; autorizar de verdade; decidir unidade sem backend |

## Authz

```text
JWT válido
→ Core effective permissions
→ capability mínima (ADR-007)
→ unit scope (ADR-006)
→ resource scope / ownership
→ ação
```

Frontend nunca substitui validação server-side.

## Paths TOTVS que o BFF deve reusar

Ver [API-ROUTES.md](./API-ROUTES.md). Famílias atuais de supplies, safety-stock, stock-balances, PO-OTD e products/purchases/parents/price-history devem ser reutilizadas antes de qualquer SQL novo.

## Caller

`X-Delpi-Caller-App: supplies-api` nas chamadas em que esse header fizer parte do padrão canônico.

## Erros e resiliência

- timeout explícito em cada client;
- retry somente quando idempotente e permitido;
- sem logar JWT;
- falha parcial permitida em composição auxiliar, nunca para mascarar authz;
- request/correlation id propagado.

## Evolução de contrato

Mudança material em contrato downstream segue `contract-evolution-backward-compatibility.mdc`. O BFF não deve alterar silenciosamente a semântica de campo para “corrigir” divergência no MFE.

## Purchase Requests

```text
C1: supplies-api → purchase-requests-api
C2: supplies-api assume schema/jobs + reconciliação
C3: redirect/desligamento do legado
```

A api-delpi continua dona do SQL TOTVS de SC/PC; C2 move somente ownership do estado/processo Minha DELPI.
