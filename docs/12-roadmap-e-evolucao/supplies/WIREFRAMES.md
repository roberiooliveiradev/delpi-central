# WIREFRAMES — Portal Suprimentos

Shell comum (padrão Comercial — chrome WF-00):

```text
┌─ .dashboard-supplies-portal ────────────────────────────────┐
│ TopBar kit  [nav…] [Buscar Ctrl+K] [Favoritos] [Avatar]    │
│   UnderlineNav (capability-driven) · Ajuda na nav           │
│ PagePath / PageHero (Início)                               │
├─────────────────────────────────────────────────────────────┤
│ conteúdo · loading · empty · partial · error · 403 · 404   │
└─────────────────────────────────────────────────────────────┘
```

**Entrega:** uma página wireframe por vez até DoD (ver README § Protocolo). Não planejar a próxima tela enquanto a atual estiver aberta.

Desktop, tablet, mobile ≤768px, light/dark. Touch ≥44×44. Tabelas no mobile → cards/stacked.

## Páginas generalistas (padrão Comercial)

Espelham o Portal Comercial: shell + hub + Ajuda + perfil — **não** são jornadas TOTVS.

| WF | Página | Rota | Capability | Status doc |
|---|---|---|---|---|
| Shell comum | chrome TopBar / nav / busca / Favoritos / avatar | — | `supplies.portal.access` | entregue E3 + Favoritos TopBar |
| WF-01 | Início (hub) | `/apps/supplies` | `supplies.portal.access` | **EM FOCO** — fechar DoD |
| WF-02 | Visão geral | `/overview` | `supplies.analytics.access` | entregue E5; revalidar após WF-01 |
| **WF-HELP** | Ajuda / Manual | `/help` | `supplies.portal.access` | esqueleto E4; completo E14 |
| **WF-USER** | Perfil usuário | `/users/:userId` | self: portal · outros: admin | **implementado** (E4.S4) |

Preferências pessoais (tema, filial padrão) **não** são página separada: ficam no **WF-USER** + `GET/PATCH /me/preferences` (Comercial também não tem `/preferences` dedicado).

Referência: [commercial/WIREFRAMES.md](../commercial/WIREFRAMES.md) (Shell, Início, WF-USER) + `/help` no MFE Comercial.

## Regra de RBAC nos wireframes

O campo **Capability** abaixo é a capability funcional mínima. Dado TOTVS exige também unit scope e, quando aplicável, resource scope/ownership.

```text
JWT válido
→ Core effective permissions
→ capability
→ allowedUnits
→ resource scope / ownership
→ ação
```

Não criar permissions de leitura/escrita separadas só porque a UI possui GET/POST/PATCH.

---

## WF-01 — Início

| Campo | Conteúdo |
|---|---|
| Objetivo | ação e descoberta, não BI |
| Rota | `/apps/supplies` |
| Capability | `supplies.portal.access` |
| Fonte | `/home/attention` + catálogo + favoritos |
| Filtro | unidade dentro de `allowedUnits` |
| Conteúdo | atenção, busca, favoritos, recentes, cards por capability |
| Partial | bloco auxiliar indisponível não derruba Hub inteiro |
| Ajuda | Início vs Overview |

---

## WF-02 — Visão Geral

| Campo | Conteúdo |
|---|---|
| Objetivo | cockpit dos **7 KPIs P0** ([KPI-FICHAS](./KPI-FICHAS.md)) |
| Rota | `/overview` |
| Capability | `supplies.analytics.access` |
| Unit | obrigatória para dados TOTVS; consolidado = only allowedUnits |
| KPIs | OTD, STOCK-VALUE, TURNOVER, CPV, SAVINGS, SC-OPEN, CRITICAL-MP |
| Fora P0 | KPI-PO-LATE (atrasos), cobertura, price-var |
| UX temporal | cada card mostra snapshot/estado/intervalo |
| Drill | páginas de foco quando existirem |
| Partial | KPI auxiliar pode ficar unavailable |

---

## WF-HELP — Ajuda / Manual `/help`

| Campo | Conteúdo |
|---|---|
| Objetivo | Manual in-app (padrão Comercial): conceitos, Quero→onde, FAQ, glossário |
| Rota | `/apps/supplies/help` |
| Capability | `supplies.portal.access` |
| Fonte | `userManualContent.ts` · `userManualToolLinks.ts` · `glossaryContent.ts` · tooltips |
| Nav | atalho TopBar **Ajuda** + item catálogo; sempre visível com portal |
| Não traz | path/`operationId` nos textos; espelho markdown = E16 |

```text
┌─ PagePath: Início / Ajuda ──────────────────────────────────────────────────┐
┌─ PageHero: Manual do usuário ───────────────────────────────────────────────┐
┌─ TOC sticky | Conceitos | Quero→onde | Mapa | FAQ | Glossário ──────────────┐
```

Satélite: [HELP-AND-ONBOARDING.md](./HELP-AND-ONBOARDING.md).

---

## WF-USER — Perfil usuário `/users/:userId`

Padrão Comercial (`WF-USER`), adaptado ao domínio Suprimentos (sem carteiras/OV).

| Campo | Conteúdo |
|---|---|
| Objetivo | identidade + preferências do Portal Suprimentos + atalhos por capability |
| Rota | `/apps/supplies/users/:userId` (EN; SPA — mesmo padrão Comercial, fora do menu launcher) |
| Capability | self: `supplies.portal.access` · outro usuário: `supplies.administration.manage` |
| Fonte | Core identidade + `GET/PATCH /users/{id}/profile` (BFF) + `/me/preferences` |
| Conteúdo | avatar (Portal/Core quando disponível) · filiais `allowedUnits` · capabilities · preferências (tema, `default_branch` ∈ allowedUnits) · atalhos Início / Overview† / SC† / Ajuda |
| Edição | preferências só no **próprio** perfil; admin não altera prefs de terceiros na P0 |
| Não traz | cargo comercial, carteiras, volume de foto dedicado (P0); perfil global Minha DELPI continua em `/profile` do shell |

```text
┌─ PagePath: Portal / Usuário / {nome} ───────────────────────────────────────┐
┌─ PageHero: Nome · e-mail · badges units / capabilities ─────────────────────┐
┌─ Identidade | Atalhos ──────────────────────────────────────────────────────┐
│ Identidade (read-only Core) · Atalhos por cap (Início, Overview†, SC†…)     │
└─────────────────────────────────────────────────────────────────────────────┘
┌─ Preferências (só self): tema · filial padrão ──────────────────────────────┐
┌─ Acesso: capabilities sessão + units (só self ou admin) ────────────────────┘
```

† conforme capability. BFF: [API-ROUTES](./API-ROUTES.md). Roadmap: **E4.S4 concluída**.

---

## WF-03 — Minhas Atividades

| Campo | Conteúdo |
|---|---|
| Rota | `/my-tasks` |
| Capability base | `supplies.portal.access` |
| Regra fina | capability do recurso referenciado + unit + ownership/equipe |
| Ações | criar, editar, concluir, cancelar conforme regra de recurso |
| Permission CRUD extra | **não na P0** |
| Fonte | `supply_tasks` + referências TOTVS |

---

## WF-04 — Solicitações de Compras

| Campo | Conteúdo |
|---|---|
| Rota | `/purchase-requests` |
| Capability | `supplies.purchase-requests.access` |
| Unit | sim |
| Resource scope | CC fail-closed; `view-all` só amplia CC |
| Export | exige `supplies.purchase-requests.export` enquanto segregação for necessária |
| Fonte | PR-api C1; supplies-api/PG C2 |

---

## WF-05 — Pedidos de Compra

| Campo | Conteúdo |
|---|---|
| Rota | `/purchase-orders` |
| Capability | `supplies.operations.access` |
| Unit | sim |
| Fonte | PO-OTD/panel |
| Ações | abrir detalhe, criar follow-up autorizado |

---

## WF-06 — Detalhe do Pedido

| Campo | Conteúdo |
|---|---|
| Rota | `/purchase-orders/:branch/:number` |
| Capability | `supplies.operations.access` |
| Unit/resource | pedido precisa pertencer ao recorte |
| Conteúdo | itens, prometida, recebimentos, SC origem |
| Ações | follow-up; deep links irmãos |

---

## WF-07 — Entregas / Atrasos

| Campo | Conteúdo |
|---|---|
| Rota | `/deliveries` |
| Capability | `supplies.operations.access` |
| Unit | sim |
| Conteúdo | atrasos operacionais, ranking, drill PC/fornecedor |
| Gate | regra BI atraso precisa ser comparada antes de depreciação |

---

## WF-08 — Importações

| Campo | Conteúdo |
|---|---|
| Rota | `/imports` |
| Status | **BLOQUEADO** até E1.S1/P-05 |
| Capability | não criar antes de entender a jornada/risco |
| Coexistência | manter app atual se confirmado |

---

## WF-09 — Fornecedores

| Campo | Conteúdo |
|---|---|
| Rota | `/suppliers` |
| Capability | `supplies.operations.access` |
| Unit | conforme disponibilidade/recorte da fonte |
| Conteúdo | busca/lista, código, loja, nome, indicadores contextuais |

---

## WF-10 — Fornecedor 360

| Campo | Conteúdo |
|---|---|
| Rota | `/suppliers/:code/:store` |
| Capability | `supplies.operations.access` |
| Unit | sim para dados unit-scoped |
| Blocos | identidade, produtos, PCs, entregas, preço, OTD, Qualidade autorizada, notas/tasks |
| Nota | mesma capability operacional + unit + fornecedor + ownership; sem `notes.write` preventivo |
| Partial | Qualidade indisponível não derruba identidade TOTVS |

---

## WF-11 — OTD Fornecedores

| Campo | Conteúdo |
|---|---|
| Rota | `/suppliers/otd` |
| Capability | `supplies.analytics.access` |
| Unit | sim |
| Conteúdo | OTD, meta, evolução, ranking |
| Gate | comparar BI atraso |

---

## WF-12 — Produtos / Matérias-primas

| Campo | Conteúdo |
|---|---|
| Rota | `/products` |
| Capability | `supplies.operations.access` |
| Fonte | busca produto/part number |
| Ação | abrir Produto 360 |

---

## WF-13 — Produto / MP 360

| Campo | Conteúdo |
|---|---|
| Rota | `/products/:code` |
| Capability | `supplies.operations.access` |
| Unit | sim para estoque/ESTSEG/PC/SC |
| Conteúdo | cadastro, saldo, ESTSEG, onde usado, fornecedores, última compra, preço, SC/PC |
| Partial | blocos independentes sinalizam indisponibilidade |

---

## WF-14 — Onde o Item é Usado

| Campo | Conteúdo |
|---|---|
| Rota | `/products/:code/where-used` |
| Capability | `supplies.operations.access` |
| Fonte | `get_product_parents` |
| Gate | não declarar paridade do BI antes do dump/comparação |

---

## WF-15 — Controle de Estoques

| Campo | Conteúdo |
|---|---|
| Rota | `/inventory` |
| Capability | `supplies.operations.access` |
| Unit | sim |
| Conteúdo | saldo/valor/localização; não misturar ESTSEG |
| Analytics | Overview pode consumir agregados com `supplies.analytics.access` via contrato próprio |

---

## WF-16 — Estoque de Segurança

| Campo | Conteúdo |
|---|---|
| Rota | `/safety-stock` |
| Capability | `supplies.operations.access` |
| Unit | sim |
| Conteúdo | saldo × ESTSEG, déficit, extrato, fornecedores, SC abertas |
| Ações | read-only neste roadmap |

---

## WF-17 — Análise de Consumo

| Campo | Conteúdo |
|---|---|
| Rota | `/safety-stock/consumption-analysis` |
| Capability | `supplies.operations.access` |
| Unit | sim |
| Conteúdo | consumo, lead time, comparativos, memória de cálculo |
| Legado | alias `/analise-consumo` somente na migração |

---

## WF-18 — Savings / Negociações

| Campo | Conteúdo |
|---|---|
| Rota | `/negotiations` |
| Capability | `supplies.analytics.access` |
| Unit | sim |
| Fonte | Sheets via api-delpi + meta SI |
| Regra | Portal lê; não cria segunda meta |

---

## WF-19 — Histórico de Preços

| Campo | Conteúdo |
|---|---|
| Rota | `/products/:code/price-history` ou seção do 360 |
| Capability | `supplies.operations.access` |
| Unit | quando contrato exigir |
| Fonte | purchase-price-history |
| Ajuda | última compra ≠ média ≠ orçamento |

---

## WF-20 — Indicadores

| Campo | Conteúdo |
|---|---|
| Rota | `/indicators` |
| Capability | `supplies.analytics.access` |
| Fonte | mesmos KPIs homologados + deep link SI |
| Regra | SI continua owner de metas |

---

## WF-21 — Administração

| Campo | Conteúdo |
|---|---|
| Rota | `/administration` |
| Capability | `supplies.administration.manage` |
| Unit | quando administrar configuração/escopo unit-scoped |
| Conteúdo | mappings, visibility scopes, settings tipados |
| Auditoria | obrigatória |
| Não concede | acesso automático a todas as units |

---

## Estados obrigatórios por tela

- loading;
- empty;
- partial/unavailable quando composição permitir;
- error;
- 403 capability/unit/resource;
- 404 recurso;
- retry quando seguro.

## Regra visual de permission minimization

A UI pode ter vários botões para uma mesma capability. Novo botão/endpoint não implica nova permission. Só criar code adicional quando houver fronteira material de risco/segregação conforme ADR-007.
