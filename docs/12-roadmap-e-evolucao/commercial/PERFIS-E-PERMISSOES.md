# Perfis e permissões — Portal Comercial

> **Objetivo:** permission codes = **capacidades** (`view` / `manage` / `export`) — **sem** códigos de cargo. Papéis Minha Delpi agrupam codes (você decide quem recebe o quê).  
> **Modelo:** [permission-resolver.md](../../03-autenticacao-autorizacao/permission-resolver.md)  
> **Manifest:** [commercial.manifest.json](../../../plugins/commercial/commercial.manifest.json)  
> **Consolidação:** [GESTAO-A-VISTA.md](./GESTAO-A-VISTA.md)  
> **Multi-membro (E5.1):** [WIREFRAMES.md](./WIREFRAMES.md) WF-05R · [DATA-MODEL.md](./DATA-MODEL.md) § 3.1b · [F2C-CUTOVER-RUNBOOK.md](./F2C-CUTOVER-RUNBOOK.md)

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
| `commercial.accounts.view` | Acessar Portal Comercial | Início, Meus pedidos, Minha Carteira, conta |
| `commercial.worklist.view` | Ver Meu dia | `/my-day`, worklist |
| `commercial.followups.manage` | Gerir follow-ups | criar/concluir tarefas |
| `commercial.seller-portfolios.manage` | Administrar carteiras | CRUD `/seller-portfolios` (+ detalhe `/seller-portfolios/:id`); `is_admin` |
| `commercial.audit.view` | Ver auditoria | quando exposta |
| `commercial.analytics.view` | Ver Gestão à vista | **Toda** `/analytics/*` (visão geral, OTD, equipe, oportunidades OV) |
| `commercial.proposals.view` | Ver propostas documento | `/proposals` lista/detalhe ADY |
| `commercial.proposals.export` | Exportar PDF proposta | POST PDF com overrides |
| `commercial.accounts.team.view` | Ver carteira da equipe | filtro de carteira/vendedor em Pedidos e Minha Carteira; Gestão Equipe — **sem** CRUD |
| `commercial.worklist.team.view` | Ver worklist da equipe | Meu dia `scope=team` |

**Home** usa `accounts.view`. **Não** existem `otd.view` / `opportunities.view` separados — cobertos por `analytics.view`.

## Aliases (OR) — coexistência com irmãos

| Área | Codes aceitos |
|------|----------------|
| Leitura portal | `accounts.view` \| `pedidos-venda-abertos.access` \| `api-delpi.access` |
| Admin carteiras | `seller-portfolios.manage` \| `pedidos-venda-abertos.admin` |
| Gestão BI / OTD / OV | `analytics.view` \| `dashboard-commercial.view` \| `api-delpi.access` |
| Documento ADY + PDF | `proposals.view` (+ export) \| `propostas.view` (legado) \| `propostas-comerciais.view` \| `api-delpi.access` \| `dashboard-commercial.view` |
| Team | **somente** `commercial.*.team.view` |

Novas atribuições de papel: preferir só `commercial.*`.

## Equipe e carteiras multi-membro (G4 + E5.1)

- Universo de filtro = carteiras **ativas** na commercial-api (membership via `seller_portfolio_members`).
- Filtro MFE (Pedidos / Minha Carteira): `accounts.team.view || seller-portfolios.manage`.
- `is_admin` no `/sellers/me` (ou equivalente `/seller-portfolios/me`) = **apenas** `can_manage_portfolios` (CRUD na tela Carteiras).
- **Admin (`seller-portfolios.manage`):** lista full-page, detalhe, org, membros, clientes, transferir, inativar/excluir.
- **Gestor (`accounts.team.view` sem `manage`):** vê **todas** as carteiras ativas nos filtros das bancadas; **não** acessa `/seller-portfolios` (nav oculta / 403).
- **Operacional:** vê as carteiras em que é owner ou member; «Todas as carteiras» = união dedupe; chip Escopo = identidade (`N carteiras` se >1), seleção no filtro da página.
- **Directory picker (criar carteira / adicionar membro):** só usuários com acesso ao portal (`app=commercial` no diretório). Sem portal access → não aparece no picker.

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
- Dar CRUD de carteiras a quem só tem `team.view`.
- Usar o MFE como única barreira — API revalida codes.
- Vincular usuário sem acesso ao app `commercial` via picker (API/directory gate).

## Checklist homologação RBAC

- [ ] Sem `analytics.view` (nem alias dashboard) → nav Gestão oculta / 403
- [ ] Sem `propostas.view` → nav Propostas oculta / 403
- [ ] `team.view` sem `manage` → filtro equipe/carteiras ok; tela Carteiras oculta / 403
- [ ] `manage` → Carteiras (lista + detalhe + org) + filtro equipe
- [ ] Aliases PVA/dashboard ainda aceitos na API (coexistência)
- [ ] Usuário em 2+ carteiras → `/me` lista `portfolios[]`; chip Escopo «N carteiras»; filtro «Todas» união dedupe
- [ ] Membro secundário (não owner) vê clientes da carteira compartilhada
- [ ] Directory picker: usuário sem `app=commercial` não aparece; com acesso aparece
- [ ] Migration `V005` aplicada (`up` só — nunca `reset`) — [F2C-CUTOVER-RUNBOOK.md](./F2C-CUTOVER-RUNBOOK.md)
