# WIREFRAMES — Portal Suprimentos

Shell comum:

```text
┌─ .dashboard-supplies-portal ────────────────────────────────┐
│ TopBar  Portal Suprimentos          [Ajuda] [Ctrl+K]        │
│ UnderlineNav (capability-driven)                            │
│ PagePath                                                   │
├─────────────────────────────────────────────────────────────┤
│ conteúdo · loading · empty · partial · error · 403 · 404   │
└─────────────────────────────────────────────────────────────┘
```

Desktop, tablet, mobile ≤768px, light/dark. Touch ≥44×44. Tabelas no mobile → cards/stacked.

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
| Objetivo | cockpit de 6–8 KPIs |
| Rota | `/overview` |
| Capability | `supplies.analytics.access` |
| Unit | obrigatória para dados TOTVS; consolidado = only allowedUnits |
| KPIs | OTD, estoque, giro, CPV, savings, SC, atrasos, críticos conforme homologação |
| UX temporal | cada card mostra snapshot/estado/período/competência |
| Drill | páginas de foco |
| Partial | KPI auxiliar pode ficar unavailable |

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
