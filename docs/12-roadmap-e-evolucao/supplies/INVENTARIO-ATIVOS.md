# Inventário de ativos — Portal Suprimentos

> **Data:** 2026-09-08 · **Status:** baseline de inventário; BIs externos ainda dependem de E1.S1.

Legenda de decisão: `INCORPORAR` · `INTEGRAR` · `DEEP_LINK` · `MANTER_EXTERNO` · `DEPRECIAR_APOS_PARIDADE` · `LEGADO_A_VALIDAR` · `FORA_DO_ESCOPO`.

---

## 1. Aplicações diretamente relacionadas a Suprimentos

| Ativo | Tipo | Owner atual | Função | Permission atual | Decisão Portal | Fase alvo | Evidência |
|---|---|---|---|---|---|---|---|
| Dashboard Suprimentos | MFE | plugin + api-delpi | CPV, OTD, estoque, giro, savings | `dashboard-supplies.view` | DEPRECIAR_APOS_PARIDADE | E5 + E11 + E17 | código/manifest |
| Solicitações de Compras | MFE | purchase-requests-api | SC por CC, detalhe, export | `purchase-requests.*` | DEPRECIAR_APOS_PARIDADE | E6 C1 → E16 C2 → E19 C3 | código/manifest |
| purchase-requests-api | API FastAPI existente | BC Solicitações | escopo CC, mapping, jobs/notificações | aliases `purchase-requests.*` | DEPRECIAR_APOS_PARIDADE | E6 C1 → E16 C2 → E19 C3 | código + ADR-002 |
| Estoque de Segurança | MFE | plugin + api-delpi | saldo×ESTSEG, consumo, fornecedores | `estoque-seguranca.*` | DEPRECIAR_APOS_PARIDADE | E8 + E17 | código/manifest |
| Portal Suprimentos | MFE futuro | novo produto | hub operacional/analítico | `supplies.portal.access` + capabilities mínimas | INCORPORAR | E3+ | ADR-004/007 |
| supplies-api | API futura Flask | novo produto | BFF + estado Minha DELPI + authz | Core-first | INCORPORAR | E2+ | ADR-001 |

### Catálogo canônico alvo de permissions

O inventário não cria permission por tela, botão ou verbo CRUD. Catálogo P0/P1 deliberadamente mínimo:

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

Novas permissions só nascem com justificativa de risco/segregação conforme ADR-007.

---

## 2. BIs / apps externos evidenciados pelo Product Owner

| Ativo | Permission observada | Estado técnico | Sobreposição parcial | Decisão atual | Próxima ação |
|---|---|---|---|---|---|
| Análise - Importações | `importados.access` | não localizado no git | nenhuma nativa confirmada | LEGADO_A_VALIDAR | E1.S1 |
| Onde o item é usado - BI | `onde-e-usado.access` | não localizado no git | `get_product_parents` | LEGADO_A_VALIDAR | E1.S1 + E10 |
| Atraso de Fornecedores - SC - BI | `matriz_atraso-fornecedores.access` | não localizado no git | OTD / PO panel | LEGADO_A_VALIDAR | E1.S1 + E7 |
| Alçada de Compras - BI | `alcada-compras.access` | não localizado no git | campos TOTVS; workflow não comprovado | LEGADO_A_VALIDAR | E1.S1; backlog E20.S3 |
| Controle de Estoques - SC - BI | `controle-estoque-sc.access` | não localizado no git | stock + ESTSEG | LEGADO_A_VALIDAR | E1.S1 + E8 |
| Indicadores de Suprimentos - Sheets | `idd-suprimentos.access` | permission não localizada; integração Sheets existe | dashboard + SI | LEGADO_A_VALIDAR | E1.S1 + E11 |

### Gate

Nenhum desses ativos pode permanecer `LEGADO_A_VALIDAR` no GO. Estado final permitido:

```text
PARIDADE_HOMOLOGADA
MANTER_EXTERNO
DEEP_LINK
FORA_DO_ESCOPO_COM_ACEITE
```

---

## 3. APIs e bounded contexts

| Ativo | Owner | Responsabilidade | Como o Portal consome | Decisão |
|---|---|---|---|---|
| api-delpi `/supplies/*` | api-delpi | SQL/interpretação TOTVS | HTTP via supplies-api | INTEGRAR |
| api-delpi `/products/*` | api-delpi | produto, compras, preço, suppliers, parents, stock | HTTP via supplies-api | INTEGRAR |
| purchase-requests-api | Solicitações | estado/escopo CC/jobs até C2 | HTTP em C1; absorção C2 | DEPRECIAR_APOS_PARIDADE |
| strategic-indicators-api | SI | metas/snapshots | enrich via supplies-api | INTEGRAR |
| financial-api | Financeiro | frete/rateio | deep link/projeção autorizada | DEEP_LINK |
| contexto Qualidade | Qualidade | inspeções/rejeições | projeção autorizada Supplier 360 | INTEGRAR |
| tv-dashboard-api | TV | telas/presets de TV | não absorver superfície | INTEGRAR feed/DEEP_LINK |
| minha-delpi-ai-api | Chat | tools/assistente | reutiliza mesmos contratos; sem acoplamento | INTEGRAR contrato |

---

## 4. Dados e rotas api-delpi reutilizáveis

Famílias existentes que devem ser usadas antes de criar nova rota TOTVS:

- CPV;
- OTD;
- stock value;
- inventory turnover;
- negotiation savings;
- purchase-order OTD/panel/series;
- purchase requests/linked orders/receipts;
- safety stock;
- consumption analysis;
- stock balances;
- product last purchase;
- purchases;
- purchase price history;
- suppliers;
- stock;
- parents/where-used;
- raw-material intelligence.

Catálogo detalhado: [API-ROUTES.md](./API-ROUTES.md).

---

## 5. Ferramentas externas / Sheets / Power BI

| Ativo | Owner atual | Função | Decisão |
|---|---|---|---|
| Planilha IDD | operação atual + composer api-delpi | origem do realizado de savings | INTEGRAR leitura; edição depende P-07 |
| Strategic Indicators | SI | meta canônica | INTEGRAR |
| Power BI/iframes dos 6 apps | a descobrir no Core | superfícies operacionais/analíticas | LEGADO_A_VALIDAR até E1.S1 |

Não copiar planilha ou Power BI para Postgres do Portal apenas para “centralizar”.

---

## 6. Capacidades compartilhadas com outros departamentos

| Capacidade | Owner | Portal faz | Portal não faz |
|---|---|---|---|
| Inspeções de Entrada | Qualidade | projeta indicadores autorizados no Supplier 360 | assume workflow de inspeção |
| Frete de compras | Financeiro | deep link/card contextual | recalcula rateio |
| PCP/open coverage | Produção/PCP | usa apenas dados compartilháveis necessários | toma regra de programação |
| Materiais de Terceiros | contexto próprio | fora do escopo/deep link | trata SB6 como estoque de compra |
| Chat | minha-delpi-ai-api | mantém compatibilidade de contratos | duplica routing/action catalog |
| Lançamento NF | Fiscal | deep link quando útil | incorpora processo fiscal |

---

## 7. Indicadores estratégicos

| Indicador | Owner da regra/realizado | Owner da meta | Portal |
|---|---|---|---|
| CPV | api-delpi | SI | integra |
| OTD | api-delpi | SI | integra |
| Giro | api-delpi | SI | integra |
| Valor de estoque | api-delpi | SI quando houver meta | integra |
| Savings | Sheets/api-delpi para realizado atual | SI | integra sem dual write |

Todo consolidado do Portal respeita somente `allowedUnits`.

---

## 8. Legado e aliases

| Legado | Alvo canônico |
|---|---|
| `dashboard-supplies.view` | `supplies.analytics.access` |
| `purchase-requests.access` | `supplies.purchase-requests.access` |
| `purchase-requests.admin` | `supplies.administration.manage` |
| `estoque-seguranca.access` | `supplies.operations.access` |
| `purchase-requests.unit.filial-01/02` | `supplies.unit.filial-01/02` |
| `estoque-seguranca.view.filial-sc/es` | `supplies.unit.filial-01/02` |
| fixture `supplies.view` | não é contrato; ajustar para `supplies.portal.access` |
| `/analise-consumo` | redirect/alias para `/safety-stock/consumption-analysis` |

Alias no BFF não substitui provisionamento do novo permission set no Core.

---

## 9. Ownership de estado novo

Somente estado criado pela Minha DELPI fica em `supplies-api`, por exemplo:

- preferências do usuário;
- tasks/follow-ups;
- notas internas de fornecedor;
- settings tipados;
- auditoria funcional;
- após C2, ownership do schema/processos `purchase_requests`.

Sem clone de SA2, SB1, SC1, SC7 ou demais tabelas TOTVS.

---

## 10. Fases atualizadas

```text
E1  descoberta/freeze
E2  supplies-api + authz
E3  MFE + RBAC coexistência
E4  Home
E5  Overview
E6  SC C1
E7  PC/entregas
E8  estoque/ESTSEG
E9  Supplier 360
E10 Product 360
E11 negociações/indicadores
E12 Minhas Atividades
E13 administração
E14 ajuda completa
E15 paridade inicial
E16 C2 Purchase Requests
E17 paridade final
E18 preparação cutover
E19 C3 cutover
E20 evoluções futuras
E21 verify final
```
