# Design / IA — Portal Comercial (Wave G / G+)

> **Status:** Wave G+ P0+P1 concluídos · UX polish Home/Meu dia (ago/2026) · backlog tarefas em [UX-E-TASKS-EVOLUTION.md](./UX-E-TASKS-EVOLUTION.md)  
> **Produto:** Portal Comercial · `id` `commercial` · `/apps/commercial`  
> **UI kit:** `@delpi/plugin-ui` · prefixo MFE `cm-` · root `.dashboard-commercial`  
> **Wireframes:** [WIREFRAMES.md](./WIREFRAMES.md) (WF-00, WF-01R, WF-06R) · **Perfis:** [PERFIS-E-PERMISSOES.md](./PERFIS-E-PERMISSOES.md)

O Portal Comercial é o hub operacional da carteira: Início, Meu dia, pedidos em aberto, Conta 360 e admin de carteiras.

## Princípios de informação (Overview → Focus → Detail → Action)

| Camada | Superfície | Objetivo |
|--------|------------|----------|
| **Overview** | Início (`/`) | Hero de saudação, alertas, KPIs — sem regra pesada |
| **Focus / Action** | Meu dia (`/my-day`) | Worklist **própria**; criar com prazo/prioridade/cliente; concluir / adiar |
| **Detail** | Pedidos, carteira, conta | Operação e Account 360 (+ CTA follow-up) |
| **Admin** | Carteiras (`/seller-portfolios`) | Configuração (permission manage) |

Analytics pesado (ROL/OTD/BI) permanece em deep link para `dashboard-commercial` / propostas — cards leves de gestão só na Home admin.

## Navegação (Wave G+)

```text
Shell: TopBar flush + UnderlineNav
Início → Meu dia → Pedidos em aberto → Minha carteira → Conta → Carteiras (admin)
```

- **Início:** `PageHero` (saudação + highlights vivos) **acima** da TopBar.
- **Meu dia:** `PageHero` próprio (contagens da fila) **dentro** da página (abaixo da TopBar).
- Badge Meu dia na nav = `overdue + today` (padrão Pipedrive).
- Escopo (carteira/vendedor) via `ScopeChipBar` no chrome da TopBar.
- Pills/`ActionButton` só para **filtros e ações de página**.

### Início (ordem e anti-redundância)

Atenção → Seus números (KPIs clicáveis + Atualizar) → Gestão/Equipe (admin) → Analytics externos.  
Sem barra de chips sob a nav nem atalhos que dupliquem a UnderlineNav.

### Meu dia (ordem)

`PageHero` (atrasadas / hoje / depois) → Fila (`ScopeChipBar` + Atualizar) → Nova tarefa (form em grid).  
Empty compacto com CTA para o form. Detalhe do MVP vs. backlog de CRM: **[UX-E-TASKS-EVOLUTION.md](./UX-E-TASKS-EVOLUTION.md)**.

### Carteiras admin (ordem)

`PageHero` (totais vivos) → Lista (`ScopeChipBar` Todas/Ativas/Inativas + Atualizar) → Nova carteira → Gerenciar → Transferir.  
Empty compacto com CTA para o form de criação.

## Alinhamento mercado

| Tema | Referência | Decisão Delpi |
|------|------------|---------------|
| Nav secundária 3–6 itens | Primer UnderlineNav, SAP | UnderlineNav no kit |
| Sidebar no plugin | HubSpot 2024 | Não (host já tem) |
| Worklist própria | HubSpot Tasks queue / Pipedrive Activities | Prazo default hoje EOD + prioridade + cliente; **assignee = self** no MVP |
| Notes / assignee / anexos | HubSpot, Pipedrive, Salesforce | Modelo/API parcial; UI backlog P0–P2 — ver UX-E-TASKS-EVOLUTION |

## Alinhamento `.cursor`

| Regra | Aplicação |
|-------|-----------|
| `plugins-reusable-components` | `UnderlineNav` / `PageHero` / `TopBar` no kit; MFE só compõe; zero CSS de `.delpi-ui-*` no MFE |
| `plugins-visual-design-system` | Tokens `--cm-*` → `--delpi-ui-*`; dark via `data-theme`; accent `#089bdb` |
| `mfe-modal-host-contained` | Dialogs de tarefa/transferência contidos no host |
| `persistent-upload-storage` | Anexos futuros: volume Compose obrigatório |
| `infra-sequential-container-startup` | Rebuild: `plugin-ui` → `commercial` → `commercial-api` |
| `test-and-commit` | Commit por etapa; testes API + build MFE |

## Componentes kit

| Componente | Uso |
|------------|-----|
| `PageHero` | Hero Início + Meu dia |
| `TopBar` | Faixa sticky flush + UnderlineNav |
| `ViewTransition` | Fade/slide na troca de telas / buckets |
| `UnderlineNav` | Nav de áreas do plugin |
| `AlertQueue` | Home “Precisa de atenção” |
| `ScopeChipBar` | Escopo no chrome + filas do Meu dia |
| `WorklistItem` | Linha do Meu dia |
| `SimpleKpiCard` (clicável) | KPIs Home / Gestão |
| `Timeline` | Activities na conta |
| `EmptyState` + CTA | Empty compacto / onboarding |
| `PageHeader` brand | Título do portal (outras páginas) |

## UX

- Uma ação primária por seção; ≤ 2 cliques do Início até a ação.
- Loading/erro por seção (`allSettled`); empty states com próximo passo.
- Mobile ≤768: UnderlineNav com scroll; botões ≥44px (WF-12); grids KPI/form em 1 coluna.
- Contraste AA em dark para ações secundárias (ex.: Concluir).
- Semântica de status via `StatusBadge` / tones do kit — sem cores hardcoded.

## Fases Wave G+

| Fase | Entrega | Código |
|------|---------|--------|
| **P0** | Shell UnderlineNav, Meu dia form, Home hero operacional, forms críticos, 403 | Entregue |
| **P1** | Follow-up Conta, Adiar/Abrir/tipo, KPIs gestão, forms restantes, ops/visual QA | Entregue |
| **UX polish** | PageHero/TopBar/ViewTransition; Home + Meu dia + Carteiras | Entregue (ago/2026) — detalhe em UX-E-TASKS-EVOLUTION |

## Fora desta wave / próximo

| Item | Doc |
|------|-----|
| F2c (PVA), prospects/pipeline/forecast (Wave H) | IMPLEMENTATION-PLAN |
| Observação, responsável, anexos, reminder… | [UX-E-TASKS-EVOLUTION.md](./UX-E-TASKS-EVOLUTION.md) § 3 |
| Start tasks HubSpot, auto-tasks de pedidos | UX-E-TASKS-EVOLUTION P3 + HOMOLOGACAO gaps |
| F3–F4 runtime module, rentabilidade | Playbook |
