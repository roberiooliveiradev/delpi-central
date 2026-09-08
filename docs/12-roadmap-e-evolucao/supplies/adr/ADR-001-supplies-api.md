# ADR-001 — Criação da supplies-api

| Campo | Valor |
|-------|--------|
| Status | Aceito (documentação) · **não implementado** |
| Data | 2026-09-08 |
| Contexto | Portal Suprimentos (`supplies`) — Minha DELPI |
| Relacionados | [ADR-002](./ADR-002-purchase-requests-api.md), [ADR-004](./ADR-004-plugin-identity-and-css-root.md), [PLAYBOOK-01](../PLAYBOOK-01-fronteiras-api-delpi.md), [MATRIZ-BOUNDARIES.md](../MATRIZ-BOUNDARIES.md) |

---

## Contexto

O domínio de Suprimentos já possui:

- MFEs que chamam **api-delpi direto** (`dashboard-supplies`, `estoque-seguranca`, `materiais-terceiros`);
- um bounded context Delpi maduro (`purchase-requests-api` + schema `purchase_requests`);
- KPIs no Strategic Indicators (`departmentId: supplies`);
- dezenas de rotas TOTVS `/supplies/*` e `/products/*` na api-delpi.

O produto-alvo é um **portal departamental** (padrão Comercial / Transformômetro / Maintenance): shell único, workflows Delpi, BFF de composição. Manter o MFE falando com api-delpi viola `.cursor/rules/mfe-own-api-no-direct-api-delpi.mdc` assim que o Portal tiver API própria.

Não existe pacote `supplies-api` no monorepo. **CONFIRMADO_NO_CODIGO.**

## Decisão

1. Criar o pacote **`supplies-api/`** no monorepo, Clean Architecture, Postgres próprio (schema `supplies` em `postgres-plugins`), OpenAPI próprio, container Compose, `ROOT_PATH=/apps/supplies-api`.
2. O MFE `plugins/supplies` **só** chama `supplies-api`. Zero `apiDelpiUrl` / `API_DELPI_BASE` / `/apps/api-delpi`.
3. Leituras TOTVS permanecem na **api-delpi**. A `supplies-api` consome via **gateway HTTP** (`DelpiApiClient`), aplica RBAC/filial/escopo **antes** de devolver ao MFE.
4. Estado criado pela Minha DELPI (tarefas, follow-ups, notas de fornecedor, alertas, preferências, settings, auditoria funcional) vive na `supplies-api`. **Não** persistir cópia de SC1/SC7/SB2.
5. Naming técnico em **inglês**; ao usuário o produto chama-se **Portal Suprimentos**.
6. Core API continua dona só de governança (apps, permissions, grupos, favoritos). Sem regra de Suprimentos na Core.

## Consequências

### Positivas

- Fronteira clara TOTVS × produto Delpi.
- Mesmo padrão do Portal Comercial (`commercial-api`).
- Espaço para worklist, alertas e Fornecedor 360 complementar sem inflar a api-delpi.

### Negativas / custos

- Dual-read e coexistência com MFEs que ainda chamam api-delpi.
- Absorção posterior de `purchase-requests-api` (ADR-002).
- Compose + gateway + volume de upload (se houver anexos de follow-up).

### Não decisões

- Escrita no TOTVS (SC/PC/ESTSEG).
- Destino final de BIs externos (ADR-005).
- Runtime `type: module`.

## Alternativas rejeitadas

| Alternativa | Motivo |
|-------------|--------|
| MFE chama api-delpi «só para KPI/read» | Proibido pela regra de bounded context |
| Colocar workflows Delpi na api-delpi | Viola missão da api-delpi (já rejeitado no Comercial) |
| Portal só com deep links, sem API | Vira launcher; não unifica jornada nem escopo |
| Reusar `purchase-requests-api` como API do Portal inteiro | SRP invertido: SC não é dona de CPV/OTD/estoque/SI |

## Plano mínimo (quando autorizado)

1. Scaffold health + JWT + envelope `{ success, message, data, meta }`.
2. Gateway api-delpi com timeout explícito e `X-Delpi-Caller-App: supplies-api`.
3. BFF dos KPIs já existentes (`/supplies/cpv|otd|stock-value|inventory-turnover|negotiation-savings/summary`).
4. Só então estado Delpi (DATA-MODEL).

## Referências

- Comercial: `docs/12-roadmap-e-evolucao/commercial/adr/ADR-001-commercial-api.md`
- Regras: `mfe-own-api-no-direct-api-delpi.mdc`, `application-bounded-context-decoupling.mdc`
