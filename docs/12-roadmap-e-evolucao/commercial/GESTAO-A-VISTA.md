# Gestão à vista — Portal Comercial (consolidação nativa)

> **Status:** ETAPA 0 (docs + capabilities) · irmãos **coexistem** (decisão 5C) · zero hosteamento · `commercial.analytics.view` único para toda a Gestão  
> **Produto:** `plugins/commercial` · `/apps/commercial`  
> **Plano:** consolidação nativa (Gestão BI + Propostas ADY + elevar operacional)

## Norte

| Camada | Papel |
|--------|--------|
| MFE `commercial` | Única UX de produto a evoluir — páginas **nativas** |
| `commercial-api` | Estado Delpi (carteiras, Meu dia, avatars) |
| `api-delpi` | TOTVS HTTP (`/commercial/*`, `/propostas-comerciais`, `/pedidos-venda-abertos`) |
| MFEs irmãos | Permanecem no menu; **não** hostear/deep-link como entrega |

**Proibido:** iframe / Module Federation / deep link obrigatório para `dashboard-commercial`, `propostas-comerciais` ou PVA.

## Nav alvo

```text
Início → Meu dia → Pedidos → Carteira → Propostas → Gestão → Carteiras†
```

† `seller-portfolios.manage`. Gestão exige `analytics.view`. Propostas exige `propostas.view`.

Subnav Gestão: `Visão geral · OTD · Equipe · Oportunidades`.

## Duas “propostas”

| Nome no Portal | TOTVS | API | Uso |
|----------------|-------|-----|-----|
| **Oportunidades (OV)** | AD1010 | `/commercial/proposals` | Funil / ciclo / BOM / histórico |
| **Propostas (documento)** | ADY010 | `/propostas-comerciais` | Documento ativo + PDF revisável |

## Permissões (capacidades — sem cargo)

| Code | Função |
|------|--------|
| `commercial.accounts.view` | Portal, pedidos, carteira, conta |
| `commercial.worklist.view` / `followups.manage` | Meu dia |
| `commercial.seller-portfolios.manage` | CRUD Carteiras (`is_admin`) |
| `commercial.audit.view` | Auditoria |
| `commercial.analytics.view` | **Toda** a Gestão (visão geral, OTD, equipe, OV) |
| `commercial.propostas.view` / `.export` | Lista/detalhe ADY + PDF |
| `commercial.accounts.team.view` | Filtro multi-vendedor / Gestão Equipe |
| `commercial.worklist.team.view` | Meu dia `scope=team` |

### Aliases (OR) enquanto irmãos coexistem

| Área | Aceita também |
|------|----------------|
| Leitura portal | `pedidos-venda-abertos.access`, `api-delpi.access` |
| Admin carteiras | `pedidos-venda-abertos.admin` |
| Gestão BI | `dashboard-commercial.view`, `api-delpi.access` |
| ADY/PDF | `propostas-comerciais.view`, `api-delpi.access`, `dashboard-commercial.view` |
| Team | **só** `commercial.*.team.view` (sem alias) |

### Equipe (G4)

Universo = carteiras **ativas** (`listSellerPortfolios`). Filtro MFE: `accounts.team.view || manage`. `is_admin` no JSON = apenas manage.

## Filtros Gestão

| | |
|--|--|
| URL | `competence`, `start_date`, `end_date`, `branch`, `customer_segment` |
| sessionStorage | `delpi.commercial.gestao.filters` (não reutilizar chave do dashboard) |
| Hook | `useGestaoFilters` |
| Datas v1 | **2× DateField** (+ competence) — sem DateRangeField |

## DoD por etapa (resumo)

| Etapa | Saída | Checkpoint |
|-------|-------|------------|
| 0 | Docs + manifest + PERFIS | Commit |
| 1a | Pedidos ≥ PVA (KPIs/Excel/OP/kit) | Commit + rebuild commercial |
| 1b | Carteira + Conta operacional kit-first | Commit + rebuild |
| 1c | Carteiras + team RBAC + Home sem deep link | Commit + rebuild commercial-api/MFE |
| 1b-híbrida | Conta CTAs internos | Commit |
| 2–5 | `/gestao/*` | Commit + rebuild |
| 6 | `/propostas` ADY+PDF | Commit + rebuild |

Após cada etapa: commit git → `up-dev-sequential.sh` dos serviços tocados → smoke/logs/403.

## Conteúdo PT

Textos de UI novos em `plugins/commercial/src/content/` (não hardcode em JSX). Não importar JSON da api-delpi no build Docker do MFE.

## Bloqueios explícitos

- **P3 CRM** só após etapas 0–6 + pedido explícito
- **DateRangeField** fora da v1
- **Remoção** de plugins irmãos só no futuro (`cleanup-later`)
- Endpoints `new-clients-*` / `rol/by-customer` fora do escopo 0–6

## Referências

- [WIREFRAMES.md](./WIREFRAMES.md) · [PERFIS-E-PERMISSOES.md](./PERFIS-E-PERMISSOES.md) · [PLAYBOOK-01-fronteiras-api-delpi.md](./PLAYBOOK-01-fronteiras-api-delpi.md)
- [DESIGN-IA-COMERCIAL.md](./DESIGN-IA-COMERCIAL.md) · [IMPLEMENTATION-PLAN.md](./IMPLEMENTATION-PLAN.md) · [INVENTARIO-ATIVOS.md](./INVENTARIO-ATIVOS.md)
- Inventários de origem: `plugins/dashboard-commercial/docs/`, `docs/12-roadmap-e-evolucao/propostas-comerciais/`, PVA README
