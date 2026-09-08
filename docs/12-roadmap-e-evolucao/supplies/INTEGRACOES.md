# INTEGRACOES — Portal Suprimentos

## 1. Diagrama

```text
MFE supplies
  GET/POST /apps/supplies-api/*
    Authorization: Bearer
    X-Request-Id (propaga)
      → supplies-api
          → Core /me (cache curto de perms se o padrão da lib existir; senão a cada request)
          → api-delpi (timeout explícito, caller supplies-api)
          → purchase-requests-api (C1)
          → strategic-indicators-api
          → opcional inspecoes-entrada HTTP (projeção 360)
```

## 2. Observabilidade

Alinhar `observability-standards.mdc` (quando a E2 implementar):

- Correlation / request id em log estruturado JSON (`request_id`, `user_sub`, `branch`, `operation_id`).
- **Nunca** logar `Authorization`, cookies, body de mapping com PII além do necessário.
- Métricas: latência BFF, latência gateway, taxa 403 filial, taxa 502 TOTVS, cache hit se houver.
- Tracing opcional no padrão já usado por commercial-api.

## 3. HTTP resilience

- Timeout em **todo** client HTTP (api-delpi, SI, PR-api, Core).
- Retry só GET idempotente; sem retry em POST tasks.
- Circuit/breaker se o pacote irmão já tiver padrão; senão fail fast + 502.
- Cancelamento: respeitar disconnect do cliente no stream se houver (P2).

## 4. Segurança

- JWT validado em todas as rotas autenticadas (health/ready públicos).
- Autorização no backend (caps + filial + fail-closed SC).
- Rate-limit: gateway da plataforma (não inventar no MFE).
- SSRF: só hosts internos Compose (api-delpi, SI), allowlist.
- Uploads futuros: volume persistente + tipos MIME + tamanho.

## 5. Multi-unidade no fio

Query `branch` validada contra o **catálogo de unidades** ∩ units do JWT (`supplies.unit.filial-{TOTVS}`), não contra um enum hardcoded eterno de dois sites. 403 se fora do conjunto. Omitir `branch` = união das units permitidas. Nova filial TOTVS não exige permission nova em CPV/ESTSEG/SC — só o code de unidade. Ver [ADR-006](./adr/ADR-006-unit-permissions.md).

## 6. Notificações

Hoje: catálogo Core `purchase_requests` (PO linked + receipt).  
C2: jobs na supplies-api, **mesma** categoria Core (não criar canal paralelo sem `feature-help-sync`).

## 7. Chat / OpenAPI

Nova rota **só** na api-delpi se gap TOTVS. Depois import Action Catalog. Portal não é dono de tool routing.

## 8. Compose / Gateway (quando E2/E3)

- Serviço `supplies-api` + `supplies` (`<<: *plugin-ui-federated`).
- `location ^~ /apps/supplies-api/` no nginx (espelho commercial-api / purchase-requests-api).
- Assets: location genérica já cobre `/apps/supplies/assets/`.
- Startup sequencial (`infra-sequential-container-startup.mdc`).
