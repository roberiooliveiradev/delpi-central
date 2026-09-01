# ADR-004 — Rotas canônicas e aliases legado

**Status:** aceito (set/2026)  
**Contexto:** evolução de hub «só CT» para hub por `placement_key`; bookmarks antigos.

**Referência de mercado:** **redirect 308** + sunset header (RFC 7231); API versionada com rotas canônicas únicas (Stripe/GitHub pattern).

---

## Decisão

### MFE (rotas React — canônicas)

| Rota | Uso |
|------|-----|
| `/apps/production-pulse/operator` | Hub |
| `/apps/production-pulse/operator/placements/:placementKey` | Picker |
| `/apps/production-pulse/operator/devices/:deviceId` | Superfície driver |

**Redirects client-side (308 equivalente):**

| Legado | Canônico |
|--------|----------|
| `/operator/work-centers/:code` | `/operator/placements/wc:{branch}:{code}` |
| `/operator/work-centers/:code/devices/:deviceId` | `/operator/devices/:deviceId` |

`branch` do redirect: query `?branch=` ou filial ativa do contexto.

### BFF (API — canônicas)

| Rota | Uso |
|------|-----|
| `GET /operator/placements` | Hub |
| `GET /operator/placements/{placementKey}/devices` | Picker |
| `GET /operator/devices/{deviceId}` | Metadados superfície (opcional — ou reuse `GET /devices/{id}` com gate operator) |

### BFF — aliases (MVP, sem duplicar lógica)

| Alias | Comportamento |
|-------|----------------|
| `GET /operator/work-centers` | `GET /operator/placements?anchorType=work_center` |
| `GET /work-centers/{code}/devices` | **Deprecated** — responde **308** para `/operator/placements/wc:{branch}:{code}/devices` |

Implementação: handler fino delega ao use case canônico — **proibido** `if path` com regra de negócio duplicada.

### Removido do MVP

- Rotas MFE/API «CT-only» como superfície primária — só redirect.

---

## Consequências

- WIREFRAMES e OpenAPI futuro listam rotas canônicas; legado só na tabela acima.
- Teste: redirect preserva query `branch`.
