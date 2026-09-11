# Inventário de ativos — Portal Suprimentos

> **Revisado em 2026-09-10.** O Portal Suprimentos e a `supplies-api` já existem e possuem E1–E5 + SC C1 funcional implementados. Este inventário não deve descrevê-los como “futuros”. Dump Core produção dos 6 BIs externos continua pendente.

Legenda: `INCORPORAR` · `INTEGRAR` · `DEEP_LINK` · `MANTER_EXTERNO` · `DEPRECIAR_APOS_PARIDADE` · `LEGADO_A_VALIDAR` · `FORA_DO_ESCOPO`.

---

## 1. Aplicações diretamente relacionadas

| Ativo | Tipo | Owner atual | Função | Decisão Portal | Estado/etapa |
|---|---|---|---|---|---|
| Portal Suprimentos | MFE | produto Suprimentos | hub operacional/analítico | INCORPORAR | **implementado**, evolução página-a-página |
| supplies-api | API Flask | produto Suprimentos | BFF + estado Minha DELPI + authz | INCORPORAR | **implementada**, evolução por contratos de página |
| Dashboard Suprimentos legado | MFE + api-delpi | legado | CPV, OTD, estoque, giro, savings | DEPRECIAR_APOS_PARIDADE | Overview novo existe; paridade/cutover pendentes |
| Solicitações de Compras legado | MFE + purchase-requests-api | BC Solicitações | SC por CC, detalhe, export | DEPRECIAR_APOS_PARIDADE | C1 funcional no Portal; C2/C3 futuros |
| purchase-requests-api | API FastAPI | BC Solicitações | escopo CC, mappings, jobs/notificações | DEPRECIAR_APOS_PARIDADE | owner até C2 |
| Estoque de Segurança legado | MFE + api-delpi | legado | saldo×ESTSEG, consumo, fornecedores | DEPRECIAR_APOS_PARIDADE | páginas novas ainda na fila |

### Permissions canônicas alvo

```text
supplies.portal.access
supplies.purchase-requests.access
supplies.operations.access
supplies.analytics.access
supplies.administration.manage
supplies.purchase-requests.view-all
supplies.purchase-requests.export
supplies.unit.filial-01
supplies.unit.filial-02
```

Novas permissions exigem fronteira real de risco/segregação conforme ADR-007.

---

## 2. BIs/apps externos do Product Owner

| Ativo | Estado técnico local | Sobreposição possível | Decisão atual | Próxima ação |
|---|---|---|---|---|
| Análise - Importações | não encontrado no Core local | nenhuma nativa confirmada | LEGADO_A_VALIDAR | dump Core prod; P-05 |
| Onde o item é usado - BI | não encontrado | `get_product_parents` | LEGADO_A_VALIDAR | dump prod + comparação antes de depreciação |
| Atraso de Fornecedores - SC - BI | não encontrado | OTD/PO panel | LEGADO_A_VALIDAR | dump prod + P-03 |
| Alçada de Compras - BI | não encontrado | campos TOTVS; workflow não comprovado | LEGADO_A_VALIDAR | dump prod + P-06 |
| Controle de Estoques - SC - BI | não encontrado | stock + ESTSEG | LEGADO_A_VALIDAR | dump prod + página Estoque |
| Indicadores de Suprimentos - Sheets | não encontrado; leitura atual existe via api-delpi/SI | Overview/Savings | LEGADO_A_VALIDAR | dump prod + P-07 |

Nenhum desses ativos pode chegar ao GO como `LEGADO_A_VALIDAR`.

---

## 3. APIs e bounded contexts

| Ativo | Owner | Responsabilidade | Como Portal consome | Decisão |
|---|---|---|---|---|
| `api-delpi /supplies/*` | api-delpi | SQL/interpretação TOTVS | HTTP via supplies-api | INTEGRAR |
| `api-delpi /products/*` | api-delpi | produto/compras/preços/suppliers/stock/parents | HTTP via supplies-api | INTEGRAR |
| purchase-requests-api | Solicitações | estado/CC/mappings/jobs até C2 | HTTP C1; absorção C2 | DEPRECIAR_APOS_PARIDADE |
| strategic-indicators-api | SI | metas/IDD | composição via supplies-api | INTEGRAR |
| Core API | plataforma | identidade/governança/effective permissions/apps/rotas | supplies-api + Portal | INTEGRAR |
| contexto Qualidade | Qualidade | inspeções/rejeições | somente projeção autorizada | P-11 aberto; fora do Supplier 360 P0 enquanto não fechado |
| Financeiro | Financeiro | frete/rateio | deep link/projeção autorizada | DEEP_LINK |

---

## 4. Estado novo owned pela supplies-api

Somente estado Minha DELPI, por exemplo:

- preferências do usuário;
- tasks/follow-ups;
- notas internas de fornecedor;
- settings tipados;
- auditoria funcional;
- após C2, ownership do schema/processos `purchase_requests`.

Não clonar SA2, SB1, SC1, SC7 ou demais tabelas TOTVS.

---

## 5. Situação de rotas/experiências

### Implementadas

- Home `/apps/supplies`;
- Overview `/overview`;
- OTD analytics `/analytics/otd`;
- Perfil `/users/:userId`;
- Ajuda `/help`;
- SC `/purchase-requests` C1 funcional.

### Próxima em foco somente após WF-04 fechar

- Pedidos de Compra `/purchase-orders`.

### Fila posterior

- detalhe do pedido;
- Entregas;
- Estoque;
- ESTSEG;
- Análise de Consumo;
- Fornecedores/Supplier 360/OTD;
- Produtos/Product 360/where-used/preços;
- Negociações;
- Indicadores se jornada distinta for comprovada;
- Minhas Atividades;
- Administração.

---

## 6. Legado e aliases

| Legado | Alvo canônico |
|---|---|
| `dashboard-supplies.view` | `supplies.analytics.access` |
| `purchase-requests.access` | `supplies.purchase-requests.access` |
| `purchase-requests.admin` | `supplies.administration.manage` |
| `estoque-seguranca.access` | `supplies.operations.access` |
| units legadas | `supplies.unit.filial-01/02` |
| `/analise-consumo` | alias/redirect futuro somente após decisão de migração |

Alias não substitui provisionamento do permission set canônico.

---

## 7. Fases atualizadas do programa

```text
E1–E5  concluídas
E6     SC C1: funcional concluída; GATE-FEATURE WF-04 em revalidação
E7     Pedidos de Compra
E8     Detalhe do Pedido
E9     Entregas/Atrasos
E10    Estoque
E11    Estoque de Segurança
E12    Análise de Consumo
E13    Fornecedores
E14    Fornecedor 360
E15    OTD Fornecedores
E16    Produtos/MP
E17    Produto/MP 360
E18    drills de produto (uma superfície por vez)
E19    Negociações
E20    decisão/Indicadores
E21    Minhas Atividades
E22    Administração
E23    auditoria Help/onboarding
E24    paridade inicial C1
E25    Purchase Requests C2
E26    paridade final
E27    preparação cutover
E28    C3
E29    verify-final
```

Backlog P1+ não faz parte da linha causal P0 e não bloqueia E29.
