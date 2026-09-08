# ADR-001 — Criação da commercial-api e migração do estado Delpi de carteira

| Campo | Valor |
|-------|--------|
| Status | Aceito · **F2 / F2c cumpridos** (estado Delpi em commercial-api; MFEs PVA/propostas removidos set/2026) |
| Data | 2026-08-05 (ADR) · atualização 2026-09 |
| Contexto | Portal Comercial (`commercial`) — Minha DELPI |
| Relacionados | [PLAYBOOK-01-fronteiras-api-delpi.md](../PLAYBOOK-01-fronteiras-api-delpi.md), [PLAYBOOK-MODULO-COMERCIAL.md](../PLAYBOOK-MODULO-COMERCIAL.md), [ADR-002](./ADR-002-deprecar-pedidos-venda-abertos.md), [F2C-CUTOVER-RUNBOOK.md](../F2C-CUTOVER-RUNBOOK.md) |

---

## Contexto

O domínio Comercial tinha plugins MFE analíticos e dezenas de rotas read-only TOTVS na **api-delpi**. O Portal do Vendedor (`pedidos-venda-abertos`) introduziu estado **Delpi** (carteira de vendedores e avatars) no Postgres de plugins **servido pela api-delpi**. (Pós-F2c: MFEs PVA/propostas removidos; estado Delpi vive na commercial-api.)

O produto-alvo inclui workflows de CRM (oportunidades, follow-ups, forecast, amostras, confirmação de pedidos) que **não** são SQL Protheus. Manter esse estado na api-delpi misturaria:

- integração TOTVS (missão da api-delpi);
- domínio operacional Delpi (missão de APIs dedicadas, como `transformometro-api` / `maintenance-api`).

## Decisão

1. Criar o pacote **`commercial-api/`** no monorepo, Clean Architecture, Postgres próprio (schema `commercial` ou equivalente em `postgres-plugins`), OpenAPI próprio, container Compose.
2. **Migrar** para a commercial-api (fase F2) **todas** as rotas de `pedidos-venda-abertos` cujo estado canônico é Delpi (Postgres / avatar) — **leituras e escritas** de seller portfolio e customer avatar. Critério: se não é SQL/view TOTVS, sai da api-delpi.
3. Manter **somente** leituras SQL TOTVS na api-delpi (pedidos abertos, ops, search/enrichment, billing-series, NF); commercial-api consome enrichment via **gateway HTTP** (`DelpiApiClient`) quando precisar compor.
4. O **Portal Comercial** chama commercial-api para **carteira, avatar e BFF TOTVS**; `dashboard-commercial` (legado) pode chamar api-delpi para KPIs. MFEs PVA/propostas **não** existem mais (F2c).
5. Naming técnico em **inglês**; ao usuário o produto chama-se **Portal Comercial** (pt-BR).
6. Shell/`type: module` (`plugins/commercial`) **só** após runtime plugin×módulo 1.1.0 se necessário — F1–F2 não bloqueiam.
7. **Depreciação / remoção** de `pedidos-venda-abertos` (e propostas MFE): ADR-002 + F2c — **executado** set/2026.

## Consequências

### Positivas

- Fronteira clara TOTVS × CRM Delpi.
- Espaço para oportunidades/forecast sem inflar a api-delpi.
- Alinhamento com o padrão maintenance / transformômetro.
- Volume e migrations de anexo sob governança da API dona do dado.

### Negativas / custos

- Dual-read/cutover na F2 (trabalho de migração e homologação) — **concluído**.
- Remoção dos MFEs legados (F2c) exige redirects + unregister Core — ver runbook.

### Não decisões (fora deste ADR)

- Escrita no TOTVS (pedido/proposta).
- Destino final de `dashboard-commercial` (permanece até Gestão nativa).
- Política final de rentabilidade / IA / WEG.
- Fonte definitiva de segmentos/famílias WEG (ADR futuro).

### Cumprimento pós-ADR

- F2 (estado Delpi em commercial-api): **cumprido**.
- F2c (remoção MFEs + redirects): **cumprido** set/2026 — [F2C-CUTOVER-RUNBOOK.md](../F2C-CUTOVER-RUNBOOK.md).

## Alternativas rejeitadas

| Alternativa | Motivo da rejeição |
|---|---|
| Manter todo CRUD na api-delpi | Viola missão da api-delpi; escala CRM no lugar errado |
| BFF único: MFE só fala com commercial-api (já na F1) | Reescreveria dashboard/propostas sem ganho imediato |
| Novo monólito MFE absorvendo os três plugins | Quebra coexistência, favoritos e deploys independentes |
| Runtime de módulo fake no Comercial | Proibido; usar roadmap canônico da plataforma |

## Plano mínimo de implementação

1. Scaffold `commercial-api` + health + auth JWT + envelope.
2. Migrations iniciais de `seller_portfolios` / `seller_customers` / `customer_avatars` conforme [DATA-MODEL.md](../DATA-MODEL.md) § 3 (alinhado ao V001/V002).
3. Dual-read e reconciliação de contagens.
4. Cutover do MFE; deprecar na api-delpi o conjunto completo de rotas Delpi (sellers GET+CRUD + avatars).
5. Só então entidades CRM (F5+).

## Referências

- Inventário: [INVENTARIO-ATIVOS.md](../INVENTARIO-ATIVOS.md)
- Migrations atuais: `api-delpi/migrations/plugins/pedidos-venda-abertos/`
- Padrão fronteira: `docs/12-roadmap-e-evolucao/maintenance/PLAYBOOK-01-fronteiras-api-delpi.md`
- Upload: `.cursor/rules/persistent-upload-storage.mdc`
- Migrations: `.cursor/rules/migrations-immutable-checksum.mdc`, `plugins-migrations-no-reset-prod.mdc`
