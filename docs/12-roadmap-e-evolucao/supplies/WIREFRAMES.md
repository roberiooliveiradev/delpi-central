# WIREFRAMES — Portal Suprimentos

> **Status (2026-09-10):** wireframes alinhados ao modo página-a-página. Início, Visão geral e OTD analytics estão fechados; Solicitações de Compras é o foco atual de revalidação; demais páginas são fila e não autorização de implementação.

Shell comum (padrão Comercial por composição compartilhada, não por cópia de CSS):

```text
┌─ .dashboard-supplies-portal ────────────────────────────────┐
│ TopBar kit  [nav…] [Buscar Ctrl+K] [Favoritos] [Avatar]    │
│ UnderlineNav capability-driven · Ajuda                     │
│ PagePath / PageHero                                        │
├─────────────────────────────────────────────────────────────┤
│ conteúdo · loading · empty · partial · error · 403 · 404   │
└─────────────────────────────────────────────────────────────┘
```

Desktop, tablet, mobile ≤768px, light/dark, teclado/focus. Touch targets adequados. Tabelas no mobile devem usar estratégia explícita de scroll ou cards/stacked.

## Regra visual de help

Quando houver label/título semântico, o **próprio texto é o alvo do tooltip**. Não desenhar `(?)` como componente adicional.

Exemplos corretos:

```text
Visão geral        ← hover/focus no próprio título
Período rápido     ← hover/focus no próprio label
Indicadores        ← hover/focus no próprio título
Meta parcial       ← hover/focus no próprio label
```

O ícone/controle de ajuda separado só é aceitável quando não existir label/título semântico adequado.

---

## Páginas generalistas

| WF | Página | Rota | Capability | Estado |
|---|---|---|---|---|
| Shell | TopBar/nav/busca/Favoritos/avatar | — | `supplies.portal.access` | entregue |
| WF-01 | Início | `/apps/supplies` | `supplies.portal.access` | **FECHADA** |
| WF-02 | Visão geral | `/overview` | `supplies.analytics.access` | **FECHADA** · WF-02R |
| WF-OTD-A | OTD analytics | `/analytics/otd` | `supplies.analytics.access` | **FECHADA** |
| WF-HELP | Ajuda / Manual | `/help` | `supplies.portal.access` | implementada; evolui junto das features |
| WF-USER | Perfil usuário | `/users/:userId` | self portal; terceiros admin | implementada |

Preferências pessoais ficam no WF-USER + `/me/preferences`; não existe página `/preferences` separada. Perfil global Minha DELPI permanece em `/profile` do host.

---

## Regra de RBAC nos wireframes

```text
JWT válido
→ Core effective permissions
→ capability
→ allowedUnits
→ resource scope / ownership
→ ação
```

Não criar permission CRUD por existir novo botão/GET/POST/PATCH.

---

## WF-01 — Início — FECHADA

| Campo | Conteúdo |
|---|---|
| Objetivo | ação e descoberta, não BI |
| Rota | `/apps/supplies` |
| Capability | `supplies.portal.access` |
| Fonte | `/home/attention` + catálogo + favoritos |
| Conteúdo | atenção, busca, favoritos, recentes, cards por capability |
| Partial | bloco auxiliar indisponível não derruba o Hub |
| Ajuda | Início × Overview |

---

## WF-02 — Visão Geral — FECHADA

| Campo | Conteúdo |
|---|---|
| Objetivo | cockpit dos 7 KPIs P0 + série OTD + CTA para WF-OTD-A |
| Rota | `/overview` |
| Capability | `supplies.analytics.access` |
| Unit | MultiSelect das unidades em `allowedUnits`; consolidado = união autorizada |
| KPIs | OTD, STOCK-VALUE, TURNOVER, CPV, SAVINGS, SC-OPEN, CRITICAL-MP |
| Filtros globais | período + `from`/`to` + `branch`; URL shareable |
| Fora do chrome global | cliente/segmento/carteira/vendedor, `location` e `stock_method` quando não suportados por todos os KPIs |
| Metas | tríade SI: `goalValue`, `comparableGoal`, `referenceGoal` + `iddScore` |
| Gráficos | OTD no tempo + comparativo valor×meta conforme natureza temporal |
| Partial | blocos auxiliares podem ficar unavailable sem derrubar tudo |

### Hero

```text
┌─ TopBar ─────────────────────────────────────────────────────────────────────────┐
┌─ PagePath: Início › Visão geral ─────────────────────────────────────────────────┐
┌─ PageHero compact ────────────────────────────────────────────────────────────────┐
│ Portal Suprimentos                                                               │
│ Visão geral                 [badge de escopo]                        [Atualizar] │
│ Indicadores do período no seu escopo.                                            │
│ Período rápido: [Hoje] [Esta semana] [Este mês] [Mês passado] [Tri] [Ano] [12m] │
│ [De] [Até] [Unidade ▾ MultiSelect]                                               │
└───────────────────────────────────────────────────────────────────────────────────┘
```

### Conteúdo

```text
[StateBanner partial, se necessário]

SectionCard "Indicadores"
  7 KPI cards; help no próprio título/labels de meta

SectionCard "OTD no tempo"                                  [Abrir OTD]
  ChartViewShell + série

SectionCard "Comparativo no período"
  somente KPIs comparáveis no recorte
```

---

## WF-OTD-A — OTD analytics — FECHADA

| Campo | Conteúdo |
|---|---|
| Objetivo | gauges por unidade + evolução temporal |
| Rota | `/analytics/otd` |
| Capability | `supplies.analytics.access` |
| Entrada | Overview/catálogo/deep link |
| Fontes | `/analytics/otd` + `/analytics/otd/series` |
| Filtros | mesmo contrato de período/unidade do Overview |
| Não traz | ranking fornecedor ou painel operacional de entregas |

```text
PagePath: Início › Visão geral › OTD
PageHero: OTD — pontualidade de compras      [escopo] [Visão geral] [Atualizar]
FilterBar: Período rápido · De · Até · Unidade

SectionCard "Pontualidade no período"
  SpeedometerGauge por unidade

SectionCard "OTD no tempo"
  ChartViewShell
```

---

## WF-HELP — Ajuda / Manual

| Campo | Conteúdo |
|---|---|
| Rota | `/help` |
| Fonte | `userManualContent.ts`, `userManualToolLinks.ts`, `glossaryContent.ts`, tooltips |
| Layout | PagePath + PageHero + TOC + SectionCards |
| Regra | conteúdo evolui na mesma entrega de cada feature; etapa final só audita cobertura |

---

## WF-USER — Perfil usuário

| Campo | Conteúdo |
|---|---|
| Rota | `/users/:userId` |
| Fonte | Core person-profile/photo + BFF profile/preferences |
| Conteúdo | identidade read-only, units/capabilities, atalhos, preferências |
| Edição P0 | somente preferências do próprio usuário |
| Preferências atuais | filial padrão + densidade de tabela conforme schema vigente |
| Foto/cargo/contatos | edição somente no `/profile` global do host |

---

## WF-04 — Solicitações de Compras — EM FOCO

| Campo | Conteúdo |
|---|---|
| Rota | `/purchase-requests` |
| Capability | `supplies.purchase-requests.access` |
| Unit | obrigatório |
| Resource scope | CC fail-closed; `view-all` amplia CC, nunca unidade |
| Export | `supplies.purchase-requests.export` + scopes |
| Fonte | PR-api C1; supplies-api/PG somente após C2 |
| Estado | C1 funcional implementado; revalidar GATE-FEATURE atual antes de promover WF-05 |
| DoD pendente | kit-first, estados, Help, filtros/URL, tema/mobile/a11y, positive+sibling+negative, smoke |

---

## Fila futura — promover uma página por vez

### WF-05 — Pedidos de Compra

| Campo | Conteúdo |
|---|---|
| Rota | `/purchase-orders` |
| Capability | `supplies.operations.access` |
| Unit | sim |
| Fonte | PO/OTD via `api-delpi` através de `supplies-api` |
| Ações | abrir detalhe; follow-up somente quando autorizado |
| Gate | só promover após WF-04 fechado + autorização PO |

### WF-06 — Detalhe do Pedido

| Campo | Conteúdo |
|---|---|
| Rota | `/purchase-orders/:branch/:number` |
| Capability | `supplies.operations.access` |
| Resource | pedido deve pertencer ao recorte autorizado |
| Conteúdo | itens, prometida, recebimentos, SC origem |

### WF-07 — Entregas / Atrasos

| Campo | Conteúdo |
|---|---|
| Rota | `/deliveries` |
| Capability | `supplies.operations.access` |
| Conteúdo | atrasos operacionais e drills autorizados |
| Paridade | BI atraso só pode ser depreciado após comparação real; P-03 continua residual de cutover/paridade |

### WF-08 — Importações

**BLOQUEADO_COM_EVIDENCIA** até contrato/jornada real serem confirmados. Não criar capability/rota funcional nova por suposição.

### WF-09 — Fornecedores

Busca/lista; contrato de busca fornecedor precisa estar comprovado ao promover.

### WF-10 — Fornecedor 360

Identidade/TOTVS + blocos operacionais + notas/tasks. **Qualidade fica fora do P0 enquanto P-11 estiver aberto**; não deixar “Qualidade autorizada” como decisão implícita de implementação.

### WF-11 — OTD Fornecedores

Página analítica distinta de OTD geral e Entregas; OTD/meta/evolução/ranking somente após contrato promovido.

### WF-12 — Produtos / MP

Busca/lista e abertura do 360.

### WF-13 — Produto / MP 360

Cadastro + blocos autorizados de estoque/ESTSEG/SC/PC/fornecedores/preços; partial explícito por bloco.

### WF-14 — Onde o Item é Usado

Fonte `get_product_parents`; não declarar paridade do BI antes de comparação real.

### WF-15 — Controle de Estoques

Saldo/valor/localização. Não misturar ESTSEG. Política de capability do stock-value deve ser fechada no plano da página.

### WF-16 — Estoque de Segurança

Saldo × ESTSEG, déficit, extrato, fornecedores, SC abertas; read-only neste roadmap.

### WF-17 — Análise de Consumo

Consumo/lead time/comparativos/memória; decidir ao promover se é página independente ou satélite inseparável do WF-16.

### WF-18 — Savings / Negociações

SI continua owner de meta; Portal não cria segunda meta.

### WF-19 — Histórico de Preços

Ao promover, decidir com evidência se permanece seção do Product 360 ou página própria. Não executar junto de WF-14 por conveniência.

### WF-20 — Indicadores

Antes de promover `/indicators`, provar jornada distinta da Overview/deep link SI; caso contrário marcar fora do escopo com justificativa.

### WF-03 — Minhas Atividades

Tasks/follow-ups com capability do recurso + unit quando aplicável + ownership/equipe; sem CRUD permissions preventivas.

### WF-21 — Administração

Mappings, visibility scopes e settings tipados; audit obrigatório; administração não concede todas as units.

---

## Estados obrigatórios por tela

- loading;
- success;
- empty;
- partial/unavailable quando composição permitir;
- error;
- 403 capability/unit/resource;
- 404 recurso;
- retry/recovery quando seguro.

## Definition of Done visual

- `@delpi/plugin-ui` primeiro;
- help no próprio label/título sempre que houver alvo semântico;
- sem override estrutural `.delpi-ui-*` no MFE;
- desktop/mobile e light/dark;
- teclado/focus;
- nenhum dado/regra de negócio inventado no frontend;
- Ajuda sincronizada no mesmo deliverable.
