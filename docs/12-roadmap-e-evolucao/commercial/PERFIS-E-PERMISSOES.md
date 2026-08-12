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
| `commercial.accounts.view` | Acessar Portal Comercial | Início, Meus pedidos, conta; Minha Carteira só com membership ou team/manage |
| `commercial.worklist.view` | Ver Meu dia | `/my-day`, worklist |
| `commercial.followups.manage` | Gerir follow-ups | criar/concluir tarefas |
| `commercial.seller-portfolios.manage` | Administrar carteiras | CRUD `/seller-portfolios`; `is_admin`; escopo irrestrito na api-delpi |
| `commercial.audit.view` | Ver auditoria | quando exposta |
| `commercial.analytics.view` | Ver Gestão à vista | `/analytics`, OTD, oportunidades OV (**não** Equipe sozinha) |
| `commercial.proposals.view` | Ver propostas documento | `/proposals` lista/detalhe ADY |
| `commercial.proposals.export` | Exportar PDF proposta | POST PDF com overrides |
| `commercial.accounts.team.view` | Ver carteira da equipe | filtro equipe; Gestão Equipe — **sem** CRUD |
| `commercial.worklist.team.view` | Ver worklist da equipe | Meu dia `scope=team` |

**Home** usa `accounts.view`. **Não** existem `otd.view` / `opportunities.view` separados — cobertos por `analytics.view`.

## Breaking change — aliases removidos (ago/2026)

Gates da **commercial-api** e escopo irrestrito na **api-delpi** aceitam **somente** `commercial.*` canônicos.

| Antes (OR legado) | Agora |
|-------------------|--------|
| `accounts.view` \| PVA.access \| `api-delpi.access` | só `commercial.accounts.view` |
| `seller-portfolios.manage` \| PVA.admin \| `api-delpi.access` | só `commercial.seller-portfolios.manage` |
| `analytics.view` \| dashboard-commercial \| `api-delpi.access` | só `commercial.analytics.view` |
| proposals + aliases PT/irmão/`api-delpi` | só `commercial.proposals.view` / `.export` |

**Ops:** re-grant papéis que ainda tinham só `api-delpi.access`, `pedidos-venda-abertos.*`, `dashboard-commercial.view` ou `propostas-comerciais.view` / `commercial.propostas.*`. `api-delpi.access` **não** eleva mais manage nem «vê todas as carteiras».

## Equipe e carteiras multi-membro (G4 + E5.1)

- Universo de filtro = carteiras **ativas** na commercial-api (membership via `seller_portfolio_members`).
- Filtro MFE (Pedidos / Minha Carteira): `accounts.team.view || seller-portfolios.manage` (rótulo «Todas as carteiras»); multi-própria sem team → «Todas as minhas carteiras».
- `is_admin` no `/seller-portfolios/me` = **apenas** `commercial.seller-portfolios.manage`.
- **Admin (`seller-portfolios.manage`):** lista full-page, detalhe, org, membros, clientes, transferir, inativar/excluir.
- **Gestor (`accounts.team.view` sem `manage`):** vê **todas** as carteiras ativas nos filtros das bancadas; **não** acessa `/seller-portfolios` (nav oculta / 404).
- **Operacional sem membership:** Meus pedidos com carteira vazia; **Minha Carteira** oculta / 404.
- **Operacional com membership:** só a(s) sua(s) carteira(s); chip Escopo = identidade.
- **Directory picker (criar carteira / adicionar membro):** só usuários com acesso ao portal (`app=commercial` no diretório).

## Papéis sugeridos (exemplos — criar na Minha Delpi)

| Papel | Codes (exemplo) |
|-------|-----------------|
| Comercial — Operacional | accounts.view + worklist.view + followups.manage (+ membership) |
| Comercial — Vê gestão | operacional + **analytics.view** |
| Comercial — Vê equipe | + accounts.team.view + worklist.team.view |
| Comercial — Emite PDF | + proposals.view + proposals.export |
| Comercial — Admin carteiras | + seller-portfolios.manage |
| Comercial — Auditor | accounts.view + audit.view |

## O que NÃO fazer

- Permission com nome de cargo/persona.
- Exigir `seller-portfolios.manage` para ver Gestão ou equipe.
- Dar CRUD de carteiras a quem só tem `team.view`.
- Usar o MFE como única barreira — API revalida codes.
- Reintroduzir aliases (`api-delpi.access`, PVA, `commercial.propostas.*`) nos OR-lists comerciais.
- Vincular usuário sem acesso ao app `commercial` via picker (API/directory gate).

## Checklist homologação RBAC

- [ ] Sem `analytics.view` → nav Gestão oculta / 404
- [ ] Sem `seller-portfolios.manage` (mesmo com `api-delpi.access`) → sem nav Carteiras / sem unrestricted
- [ ] Sem membership e sem team/manage → sem Minha Carteira
- [ ] Só `accounts.view` + membership → só a(s) carteira(s) próprias
- [ ] `accounts.team.view` sem manage → filtro equipe; sem CRUD Carteiras
- [ ] Sem `proposals.view` → nav Propostas oculta / 404
- [ ] `manage` → Carteiras (lista + detalhe + org) + filtro equipe
- [ ] Usuário em 2+ carteiras → `/me` lista `portfolios[]`; chip Escopo «N carteiras»; filtro «Todas as minhas» união dedupe
- [ ] Membro secundário (não owner) vê clientes da carteira compartilhada
- [ ] Directory picker: usuário sem `app=commercial` não aparece; com acesso aparece
- [ ] Re-grant pós-deploy concluído nos papéis afetados
- [ ] Migration `V005` aplicada (`up` só — nunca `reset`) — [F2C-CUTOVER-RUNBOOK.md](./F2C-CUTOVER-RUNBOOK.md)
