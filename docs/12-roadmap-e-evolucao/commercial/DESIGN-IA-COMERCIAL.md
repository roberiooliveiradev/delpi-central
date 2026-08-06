# Design / IA — Portal Comercial (Wave G / G+)

> **Status:** Wave G+ P0+P1 concluídos no código · ago/2026  
> **Produto:** Portal Comercial · `id` `commercial` · `/apps/commercial`  
> **UI kit:** `@delpi/plugin-ui` · prefixo MFE `cm-` · root `.dashboard-commercial`  
> **Wireframes:** [WIREFRAMES.md](./WIREFRAMES.md) (WF-00, WF-01R, WF-06R) · **Perfis:** [PERFIS-E-PERMISSOES.md](./PERFIS-E-PERMISSOES.md)

O Portal Comercial é o hub operacional da carteira: Início, Meu dia, pedidos em aberto, Conta 360 e admin de carteiras.

## Princípios de informação (Overview → Focus → Detail → Action)

| Camada | Superfície | Objetivo |
|--------|------------|----------|
| **Overview** | Início (`/`) | Hero de saudação, alertas, KPIs, atalhos — sem regra pesada |
| **Focus / Action** | Meu dia (`/my-day`) | Worklist priorizada; criar com prazo/prioridade/cliente; concluir / adiar |
| **Detail** | Pedidos, carteira, conta | Operação e Account 360 (+ CTA follow-up) |
| **Admin** | Carteiras (`/seller-portfolios`) | Configuração (permission manage) |

Analytics pesado (ROL/OTD/BI) permanece em deep link para `dashboard-commercial` / propostas — cards leves de gestão só na Home admin.

## Navegação (Wave G+)

```text
Shell: PageHero (saudação SI) → TopBar flush + UnderlineNav
Início → Meu dia → Pedidos em aberto → Minha carteira → Conta → Carteiras (admin)
```

Hero de saudação no estilo Strategic Indicators (`PageHero` do kit: eyebrow, título azul, descrição, highlights) fica **acima** da `TopBar` flush (`createDashboardTopBar` — sem banda de `--surface`).

- Badge Meu dia = `overdue + today` (padrão Pipedrive).
- Escopo (carteira/vendedor) via `ScopeChipBar` no chrome.
- Pills/`ActionButton` só para **filtros e ações de página** (ex.: buckets do Meu dia).

## Alinhamento mercado

| Tema | Referência | Decisão Delpi |
|------|------------|---------------|
| Nav secundária 3–6 itens | Primer UnderlineNav, SAP | UnderlineNav no kit |
| Sidebar no plugin | HubSpot 2024 | Não (host já tem) |
| Worklist | HubSpot / Gong / Pipedrive | Prazo default hoje EOD + prioridade + cliente |

## Alinhamento `.cursor`

| Regra | Aplicação |
|-------|-----------|
| `plugins-reusable-components` | `UnderlineNav` no kit; MFE só compõe; zero CSS de `.delpi-ui-*` no MFE |
| `plugins-visual-design-system` | Tokens `--cm-*` → `--delpi-ui-*`; dark via `data-theme`; accent `#089bdb` |
| `mfe-modal-host-contained` | Dialogs de tarefa/transferência contidos no host |
| `infra-sequential-container-startup` | Rebuild: `plugin-ui` → `commercial` → `commercial-api` |
| `test-and-commit` | Commit por etapa; testes API + build MFE |

## Componentes kit

| Componente | Uso |
|------------|-----|
| `PageHero` | Hero Início (linguagem SI / IGD) |
| `TopBar` | Faixa sticky flush + UnderlineNav |
| `ViewTransition` | Fade/slide na troca de telas |
| `UnderlineNav` | Nav de áreas do plugin (Wave G+) |
| `AlertQueue` | Home “Precisa de atenção” |
| `ScopeChipBar` | Chrome escopo carteira/vendedor |
| `WorklistItem` | Linha do Meu dia |
| `Timeline` | Activities na conta |
| `EmptyState` + CTA | Onboarding WF-11 |
| `PageHeader` brand | Título do portal |

## UX

- Uma ação primária por seção; ≤ 2 cliques do Início até a ação.
- Loading/erro por seção (`allSettled`); empty states com próximo passo.
- Mobile ≤768: UnderlineNav com scroll; botões ≥44px (WF-12).
- Contraste AA em dark para ações secundárias (ex.: Concluir).
- Semântica de status via `StatusBadge` / tones do kit — sem cores hardcoded.

## Fases Wave G+

| Fase | Entrega | Código |
|------|---------|--------|
| **P0** | Shell UnderlineNav, Meu dia form, Home hero operacional, forms críticos, 403 | Entregue |
| **P1** | Follow-up Conta, Adiar/Abrir/tipo, KPIs gestão, forms restantes, ops/visual QA | Entregue |

## Fora desta wave

F2c (PVA), prospects/pipeline/forecast (Wave H), Start tasks HubSpot, auto-tasks de pedidos, F3–F4 runtime module, rentabilidade.
