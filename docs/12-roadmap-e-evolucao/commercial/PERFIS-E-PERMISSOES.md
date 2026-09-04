# Perfis e permissões — Portal Comercial

> **Objetivo:** catálogo condensado — 3 permission codes. Papéis Minha Delpi agrupam codes (você decide quem recebe o quê).  
> **Modelo:** [permission-resolver.md](../../03-autenticacao-autorizacao/permission-resolver.md)  
> **Manifest:** [commercial.manifest.json](../../../plugins/commercial/commercial.manifest.json)

## Princípio

```text
Usuário → Papel(éis) Minha Delpi → permission codes → API / MFE
```

| É | Não é |
|---|--------|
| `commercial.access` / `commercial.manage` / `commercial.billing.notify` | `commercial.vendedor` / permission por cargo |
| Papel que **agrupa** codes | Fragmentar catálogo com `commercial.<feature>.view` sem justificativa |

## Catálogo (manifest + commercial-api)

| Código | Nome UI | Onde vale |
|--------|---------|-----------|
| `commercial.access` | Acessar Portal Comercial | Início, Meus pedidos, Minhas tarefas, follow-ups, Visão geral / OTD / OV, Propostas + PDF, **sala de interação (global)**, auditoria quando exposta; Minha Carteira só com **membership** ou `manage` |
| `commercial.manage` | Administrar Portal Comercial | **Vê tudo** (todas as carteiras/clientes + salas), Administração (CRUD de carteiras, grupos e **políticas de SLA** em `/settings/sla-policies`), filtro «Todas as carteiras», worklist `scope=team`, jobs ops |
| `commercial.billing.notify` | Receber notificação de faturamento | Destinatário da notificação «Pronto para faturar» — **não** libera telas admin nem escopo |

**Home** e rotas de produto usam `commercial.access`. Administração e `/analytics/team` usam `commercial.manage`.

## Equipe, membership e Pedidos

| Situação | Pedidos em aberto | Topbar «Minha Carteira» | Minha Carteira / Conta |
|----------|-------------------|-------------------------|------------------------|
| Só `access`, **sem** membership | Acessa; vê **todos** os clientes | Oculta | Sem entrada |
| `access` **com** membership | Filtra à(s) carteira(s) | Visível | Só carteiras próprias |
| `manage` (+ tipicamente `access`) | Todas as carteiras | Visível | Todas + CRUD Administração |

- `is_admin` / escopo irrestrito = **somente** `commercial.manage`.
- Grupos operacionais (`commercial_groups`) ≠ RBAC; gestão só com `manage`.
- Membership (`seller_portfolio_members`) continua fora do RBAC.

## Novas funcionalidades — access vs manage vs code específico

Antes de criar permission code:

```text
1. Capacidade transversal do produto (uso no dia a dia)?
   → Preferir commercial.access (não criar code novo).

2. Administração / escopo «vê todas as carteiras» / CRUD estrutural?
   → Preferir commercial.manage.

3. Destinatário ou efeito estreito (notificação, job, integração)
   que NÃO libera telas nem escopo amplo?
   → Avaliar permission específica (ex.: commercial.billing.notify).
   Justificar no PR + atualizar este doc e o manifest.
```

**Proibido:** criar `commercial.<feature>.view` por padrão; fragmentar o catálogo sem justificativa aqui.

Exemplos: OTD/OV → `access`; Administração de grupos → `manage`; notificação pronto para faturar → `billing.notify`; notificações de tarefas → só envolvidos + `access` (sem code novo); **sala de interação (P2-SALA)** → `access` global (inbox e thread para todos com Portal; unfurl de entidade continua por carteira).

## Papéis sugeridos (criar na Minha Delpi)

| Papel | Codes |
|-------|--------|
| Comercial — Operacional | `commercial.access` (+ membership) |
| Comercial — Admin | `commercial.access` + `commercial.manage` |
| Comercial — Faturamento | `commercial.access` + `commercial.billing.notify` — atalhos Início: Pode faturar / board / Postergado |
| Comercial — Orçamentista | `commercial.access` — atalhos Início: Oportunidades + Propostas |
| Comercial — Auditor | `commercial.access` |

## Notificação «pronto para faturar»

| Peça | Onde |
|------|------|
| Destinatários vendedor | Membros das carteiras do cliente |
| Destinatários faturamento | `billingPermissionCodes: ["commercial.billing.notify"]` em `ready_to_invoice_notification.json` |
| Job ops | Exige `commercial.manage` |
| Categoria catálogo | `commercial` · Preferências: «Faturar notas fiscais» |

## Notificação de tarefas (Portal)

| Peça | Onde |
|------|------|
| Destinatários | `userIds` envolvidos (assignees, membros de grupo assignee, criador) — **sem** permission code novo |
| Exclusão | Nunca notifica o ator da mutação |
| Emissor | commercial-api → outbox → Core `category=commercial_tasks` |
| Job prazos | `POST /integrations/jobs/task-due-scan` (`commercial.manage`) — `due_soon` / `overdue` |
| Categoria catálogo | `commercial_tasks` · Preferências: «Tarefas comerciais» (separado de faturar) |
| Deep link | `/apps/commercial/my-tasks` + `bucket` / `q` — **sem** forçar `view=` |

**Não** usar `permissionCodes: ["commercial.access"]` no dispatch (broadcast). Quem não tem o app Comercial não vê a preferência (`kind=app` + `pluginId=commercial`).

## O que NÃO fazer

- Permission com nome de cargo/persona.
- Dual-read / aliases dos codes antigos (`accounts.view`, `analytics.view`, `seller-portfolios.manage`, `commercial.propostas.*`, etc.).
- Usar o MFE como única barreira — API revalida codes.
- Dar `manage` só para «ver equipe sem CRUD» — quem precisa ver todas as carteiras recebe `manage` (e CRUD).

## Checklist homologação RBAC

- [ ] Sem `access` → sem app / menu Portal
- [ ] Só `access` sem membership → Pedidos consolidado; sem Minha Carteira na topbar
- [ ] `access` + membership → Minha Carteira própria
- [ ] Sem `manage` → sem Administração / sem «todas as carteiras»
- [ ] `manage` → vê tudo + CRUD Administração
- [ ] Notificação faturamento só com `billing.notify` (+ membros da carteira)
- [ ] Re-grant no Core **antes** do deploy que remove codes antigos do manifest
- [ ] Deploy na mesma janela: commercial-api + MFE commercial + api-delpi
