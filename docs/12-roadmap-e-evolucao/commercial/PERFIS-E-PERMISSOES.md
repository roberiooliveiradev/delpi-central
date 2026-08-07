# Perfis e permissões — Portal Comercial

> **Objetivo:** permission codes = **capacidades** (`view` / `manage` / `export`) — **sem** códigos de cargo. Papéis Minha Delpi agrupam codes (você decide quem recebe o quê).  
> **Modelo:** [permission-resolver.md](../../03-autenticacao-autorizacao/permission-resolver.md)  
> **Manifest:** [commercial.manifest.json](../../../plugins/commercial/commercial.manifest.json)  
> **Consolidação:** [GESTAO-A-VISTA.md](./GESTAO-A-VISTA.md)

## Princípio

```text
Usuário → Papel(éis) Minha Delpi → permission codes → API / MFE
```

| É | Não é |
|---|--------|
| `commercial.analytics.view` | `commercial.supervisor` / `commercial.vendedor` |
| Papel que **agrupa** codes | Permission com nome de persona |

## Catálogo (manifest + commercial-api)

| Código | Nome UI | Onde vale |
|--------|---------|-----------|
| `commercial.accounts.view` | Acessar Portal Comercial | Início, pedidos, carteira, conta |
| `commercial.worklist.view` | Ver Meu dia | `/my-day`, worklist |
| `commercial.followups.manage` | Gerir follow-ups | criar/concluir tarefas |
| `commercial.seller-portfolios.manage` | Administrar carteiras | CRUD `/seller-portfolios`; `is_admin` |
| `commercial.audit.view` | Ver auditoria | quando exposta |
| `commercial.analytics.view` | Ver Gestão à vista | **Toda** `/gestao/*` (visão geral, OTD, equipe, oportunidades OV) |
| `commercial.propostas.view` | Ver propostas documento | `/propostas` lista/detalhe ADY |
| `commercial.propostas.export` | Exportar PDF proposta | POST PDF com overrides |
| `commercial.accounts.team.view` | Ver carteira da equipe | filtro vendedor Pedidos/Carteira; Gestão Equipe |
| `commercial.worklist.team.view` | Ver worklist da equipe | Meu dia `scope=team` |

**Home** usa `accounts.view`. **Não** existem `otd.view` / `oportunidades.view` separados — cobertos por `analytics.view`.

## Aliases (OR) — coexistência com irmãos

| Área | Codes aceitos |
|------|----------------|
| Leitura portal | `accounts.view` \| `pedidos-venda-abertos.access` \| `api-delpi.access` |
| Admin carteiras | `seller-portfolios.manage` \| `pedidos-venda-abertos.admin` |
| Gestão BI / OTD / OV | `analytics.view` \| `dashboard-commercial.view` \| `api-delpi.access` |
| Documento ADY + PDF | `propostas.view` (+ export) \| `propostas-comerciais.view` \| `api-delpi.access` \| `dashboard-commercial.view` |
| Team | **somente** `commercial.*.team.view` |

Novas atribuições de papel: preferir só `commercial.*`.

## Equipe (G4)

- Universo = carteiras **ativas** na commercial-api.
- Filtro MFE: `accounts.team.view || seller-portfolios.manage`.
- `is_admin` no `/sellers/me` = **apenas** `can_manage_portfolios` (CRUD).

## Papéis sugeridos (exemplos — criar na Minha Delpi)

| Papel | Codes (exemplo) |
|-------|-----------------|
| Comercial — Operacional | accounts.view + worklist.view + followups.manage |
| Comercial — Vê gestão | operacional + **analytics.view** |
| Comercial — Vê equipe | + accounts.team.view + worklist.team.view |
| Comercial — Emite PDF | + propostas.view + propostas.export |
| Comercial — Admin carteiras | + seller-portfolios.manage |
| Comercial — Auditor | accounts.view + audit.view |

## O que NÃO fazer

- Permission com nome de cargo/persona.
- Exigir `seller-portfolios.manage` para ver Gestão ou equipe.
- Usar o MFE como única barreira — API revalida codes.

## Checklist homologação RBAC

- [ ] Sem `analytics.view` (nem alias dashboard) → nav Gestão oculta / 403
- [ ] Sem `propostas.view` → nav Propostas oculta / 403
- [ ] `team.view` sem `manage` → filtro equipe ok; tela Carteiras oculta
- [ ] `manage` → Carteiras + filtro equipe
- [ ] Aliases PVA/dashboard ainda aceitos na API (coexistência)
