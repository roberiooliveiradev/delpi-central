# Inventário de ativos — Suprimentos

> **Data:** 2026-09-08 · Decisão Portal = exatamente um valor da enumeração obrigatória.

Legenda de decisão: `INCORPORAR` · `INTEGRAR` · `DEEP_LINK` · `MANTER_EXTERNO` · `DEPRECIAR_APOS_PARIDADE` · `LEGADO_A_VALIDAR` · `FORA_DO_ESCOPO`

---

## A. Aplicações diretamente pertencentes a Suprimentos

| Ativo | ID | Tipo | Owner atual | Usuários | Função | Frontend | Backend | Dados | Permission | Status | Sobreposição | Decisão Portal | Fase | Evidência |
|-------|----|------|-------------|----------|--------|----------|---------|-------|------------|--------|--------------|----------------|------|-----------|
| Dashboard Suprimentos | `dashboard-supplies` | MFE | Plugin + api-delpi | Analista / gestor | Cockpit CPV OTD estoque giro savings | `plugins/dashboard-supplies` | api-delpi `/supplies/*` direto | SD3 SB9 Sheets IDD | `dashboard-supplies.view` | ativo | SI mesmos KPIs | DEPRECIAR_APOS_PARIDADE | E5+E12+E14 | CONFIRMADO_NO_CODIGO manifest |
| Solicitações de Compras | `purchase-requests` | MFE | purchase-requests-api | Solicitante / comprador / admin | Lista SC por CC | `plugins/purchase-requests` | purchase-requests-api | SC1 SC7 SD1 + PG | `purchase-requests.access` (+ view-all, admin, export, filial-01/02) | ativo | — | DEPRECIAR_APOS_PARIDADE | E6 | CONFIRMADO_NO_CODIGO |
| purchase-requests-api | `purchase-requests-api` | API | mesmo BC | MFE SC | Escopo CC, mapping, notif | — | FastAPI `/apps/purchase-requests-api` | schema `purchase_requests` | mesmas | ativo | — | DEPRECIAR_APOS_PARIDADE | E6 C1–C3 | CONFIRMADO_NO_CODIGO ADR-002 |
| Estoque de Segurança | `estoque-seguranca` | MFE | Plugin + api-delpi | Planejamento / compras | Saldo×ESTSEG + simulação | `plugins/estoque-seguranca` | api-delpi safety-stock direto | SB1 SBZ SB2 SC7 SC1 SD4 SD3 SA5 | `estoque-seguranca.access` + filial-sc/es | ativo | BI estoque; dashboard stock | DEPRECIAR_APOS_PARIDADE | E8 | CONFIRMADO_NO_CODIGO |

---

## B. BIs e dashboards

| Ativo | ID | Tipo | Owner atual | Usuários | Função | Frontend | Backend | Dados | Permission | Status | Sobreposição | Decisão Portal | Fase | Evidência |
|-------|----|------|-------------|----------|--------|----------|---------|-------|------------|--------|--------------|----------------|------|-----------|
| Análise - Importações | desconhecido | iframe/BI? | Core prod? | Analista SC/ES | Importações | não no git | ? | ? | `importados.access` (PO) | desconhecido | nenhum nativo | LEGADO_A_VALIDAR | E1.S1 | CONFIRMADO_POR_EVIDENCIA_DO_PRODUCT_OWNER |
| Onde o item é usado - BI | desconhecido | BI | Core prod? | Comprador SC | Estrutura / pais | não no git | ? | BOM? | `onde-e-usado.access` (PO) | desconhecido | `/products/{code}/parents` | LEGADO_A_VALIDAR | E1.S1 + E11 | PO + CONFIRMADO_NO_CODIGO (API chat) |
| Atraso de Fornecedores - SC - BI | desconhecido | BI | Core prod? | Comprador SC | Matriz atraso | não no git | ? | ? | `matriz_atraso-fornecedores.access` (PO) | desconhecido | OTD ranking | LEGADO_A_VALIDAR | E1.S1 + E9 | PO |
| Alçada de Compras - BI | desconhecido | BI | Core prod? | Comprador SC | Alçadas | não no git | ? | C7_APROV? | `alcada-compras.access` (PO) | desconhecido | campo contrato SC | LEGADO_A_VALIDAR | E1.S1 | PO |
| Controle de Estoques - SC - BI | desconhecido | BI | Core prod? | Comprador SC | Estoque SC | não no git | ? | ? | `controle-estoque-sc.access` (PO) | desconhecido | stock + ESTSEG | LEGADO_A_VALIDAR | E1.S1 + E7 | PO |
| Dashboard Suprimentos páginas internas | `dashboard-supplies/{cpv,otd,stock,inventory-turnover,negotiation-savings}` | rotas MFE | mesmo | Analista | Drill KPI | mesmo plugin | api-delpi | ver A | `dashboard-supplies.view` | ativo | SI | INCORPORAR (no Portal) | E5 | CONFIRMADO_NO_CODIGO routes.ts |

---

## C. APIs

| Ativo | ID | Tipo | Owner atual | Usuários | Função | Frontend | Backend | Dados | Permission | Status | Sobreposição | Decisão Portal | Fase | Evidência |
|-------|----|------|-------------|----------|--------|----------|---------|-------|------------|--------|--------------|----------------|------|-----------|
| api-delpi supplies | `/supplies/*` | API TOTVS | api-delpi | vários MFEs + SI + chat | SQL canônico | — | FastAPI | Protheus | `dashboard-supplies.view` / ESTSEG / SC / `api-delpi.access` | ativo | — | INTEGRAR (gateway) | E2+ | OpenAPI inventory |
| api-delpi products purchase | `/products/{code}/purchases` etc. | API | api-delpi | chat + futuros 360 | Histórico compra, pais, estoque item | — | FastAPI | SD1 SA5 SB2 SG | perms produto | ativo | BI onde-usado | INTEGRAR | E10–E11 | OpenAPI |
| strategic-indicators-api | dept `supplies` | API | SI | gestores / TV | Meta vs realizado | MFE SI | SI → DelpiSuppliesGateway | snapshots | SI | ativo | dashboard KPIs | INTEGRAR | E14 | si_indicator_tv_catalog.json |
| financial-api freight | `/freight/*` | API | financial-api | financeiro | Rateio frete compras | `plugins/financial` | financial-api → api-delpi | SF8 SF1 | `financial.freight.view` | ativo | — | DEEP_LINK | — | CONFIRMADO_NO_CODIGO |
| tv-dashboard-api | `supplies_stock_*` | API+MFE | TV | TV / gestão | Telas nativas estoque | tv-dashboard | tv-dashboard-api | api-delpi | TV | ativo | dashboard stock | INTEGRAR (não absorver TV) | — | native_screens.json |
| supplies-api | — | — | — | — | — | — | — | — | — | **inexistente** | — | INCORPORAR (criar) | E2 | CONFIRMADO_NO_CODIGO |

---

## D. Dados e rotas api-delpi (catálogo de reuso)

Ver tabela completa em [API-ROUTES.md](./API-ROUTES.md) § Reuso. Resumo: **30** ops `/supplies/*` estáveis + família `/products/{code}/last-purchase|purchases|purchase-price-history|suppliers|stock|parents|raw-material-*`.

**Não propor rota TOTVS nova** sem provar insuficiência destas.

---

## E. Ferramentas externas / iframe / Sheets / Power BI

| Ativo | ID | Tipo | Owner atual | Usuários | Função | Frontend | Backend | Dados | Permission | Status | Sobreposição | Decisão Portal | Fase | Evidência |
|-------|----|------|-------------|----------|--------|----------|---------|-------|------------|--------|--------------|----------------|------|-----------|
| Planilha IDD Suprimentos | env `SUPPLIES_IDD_SHEET_ID` | Sheets | Operações IDD + api-delpi composer | Analista (via dashboard) | Economia negociações | dashboard savings | `get_supplies_negotiation_savings_summary` | Google Sheets | `dashboard-supplies.view` (git) / `idd-suprimentos.access` (PO) | ativo no composer | SI `supplies-negotiation-savings` | INTEGRAR (já integrado); perm PO = LEGADO_A_VALIDAR | E12 E1.S1 | CONFIRMADO_NO_CODIGO supplies_composer.py |
| Power BI genérico TV | allowlist `powerbi.com` | iframe | TV | — | Embed genérico | tv-dashboard | — | — | TV | ativo genérico | — | MANTER_EXTERNO | — | INF: não é app de suprimentos |
| Seis apps PO | ver B | iframe/BI/Sheets | Core prod | ver personas | ver B | Core | ? | ? | ver B | ? | ver duplicidades | LEGADO_A_VALIDAR | E1.S1 | PO; ausência git |

---

## F. Capacidades compartilhadas com outros departamentos

| Ativo | ID | Tipo | Owner atual | Usuários | Função | Frontend | Backend | Dados | Permission | Status | Sobreposição | Decisão Portal | Fase | Evidência |
|-------|----|------|-------------|----------|--------|----------|---------|-------|------------|--------|--------------|----------------|------|-----------|
| Inspeções de Entrada | `inspecoes-entrada` | MFE Qualidade | Qualidade | Qualidade (+ compras vê fornecedor) | Pendências / ranking fornecedor | `plugins/inspecoes-entrada` | api-delpi inspecoes-entrada | QER views | `inspecoes-entrada.view` + filial-01/02 | ativo | Fornecedor 360 | INTEGRAR (projeção) | E10 | CONFIRMADO_NO_CODIGO |
| Frete das compras | `financial` freight | MFE Financeiro | Financeiro | Financeiro | Vínculo NF×frete | `/apps/financial/freight` | financial-api | SF8 SF1 | `financial.freight.view` | ativo | custo item | DEEP_LINK | E10 opcional | CONFIRMADO_NO_CODIGO |
| PCP open-coverage | production-control | consumidor | PCP | PCP | SC1 × ESTSEG | production-control | api-delpi open-coverage | SC1 SBZ | PCP | ativo | ESTSEG | FORA_DO_ESCOPO (PCP consome; Portal não toma) | — | CONFIRMADO_NO_CODIGO |
| Reports shortage 30d | `reports` | relatório | Reports | vários | Provider safety_stock_shortage | reports | api-delpi | ESTSEG | reports | ativo | ESTSEG | DEEP_LINK | — | INF confirmada no inventário explore |
| Chat produto | minha-delpi-ai-api | chat | Chat | todos com chat | Consulta item / purchases / parents | chat MFE | AI API → api-delpi | produtos | chat | ativo | Produto 360 | INTEGRAR (não duplicar contrato) | E11 | CONFIRMADO_NO_CODIGO |
| Lançamento NF / PC | `lancamento-notas-fiscais` | MFE | Fiscal | fiscal | Link PC / fornecedor | plugin | api-delpi | SD1 SC7 | NF | ativo | Pedido 360 | DEEP_LINK | — | CONFIRMADO_NO_CODIGO |

---

## G. Indicadores estratégicos

| Ativo | ID | Tipo | Owner atual | Usuários | Função | Frontend | Backend | Dados | Permission | Status | Sobreposição | Decisão Portal | Fase | Evidência |
|-------|----|------|-------------|----------|--------|----------|---------|-------|------------|--------|--------------|----------------|------|-----------|
| CPV | `supplies-cpv` | SI | SI + api-delpi | gestão | Meta×realizado | SI + dashboard | SI gateway | CPV TOTVS | SI / dashboard-supplies.view | ativo | dashboard CPV | INTEGRAR | E5 E14 | catalog JSON |
| OTD compras | `supplies-otd` | SI | SI | gestão | Meta OTD | SI + dashboard | SI | OTD | idem | ativo | OTD page | INTEGRAR | E5 E9 | catalog |
| Giro | `supplies-stock-turnover` | SI | SI | gestão | Giro vezes | SI + dashboard | SI | CPV÷estoque | idem | ativo | turnover page | INTEGRAR | E5 E7 | catalog |
| Valor estoque | `supplies-stock-value` | SI | SI | gestão | Valor | SI + dashboard + TV | SI | SB9 | idem | ativo | stock page | INTEGRAR | E5 E7 | catalog |
| Savings | `supplies-negotiation-savings` | SI | SI | gestão | Economia | SI + dashboard | SI + Sheets | IDD | idem | ativo | Sheets | INTEGRAR; **fonte de meta = SI** | E12 E14 | catalog + composer |
| TV valor estoque | `supplies_stock_value` | TV nativa | TV | TV | Tela | tv-dashboard | tv-api | estoque | TV | ativo | SI | INTEGRAR (feed, não UI) | — | native_screens |
| TV itens críticos | `supplies_stock_alert` | TV nativa | TV | TV | Críticos | tv-dashboard | tv-api | ESTSEG? | TV | ativo | ESTSEG | INTEGRAR | — | native_screens |

---

## H. Documentação

| Ativo | ID | Tipo | Owner atual | Decisão Portal | Fase | Evidência |
|-------|----|------|-------------|---------------|------|-----------|
| Contrato SC Fase 0.2 | `docs/12-roadmap-e-evolucao/solicitacoes-compras/` | doc | Compras | INCORPORAR princípios (não reescrever SQL) | E6 | CONFIRMADO_EM_DOCUMENTACAO_CANONICA |
| ESTSEG README + api doc | `plugins/estoque-seguranca/README.md`, `api-delpi/docs/api/estoque-seguranca.md` | doc | — | INCORPORAR regras | E8 | CONFIRMADO_EM_DOCUMENTACAO_CANONICA |
| Help dashboard | `plugins/dashboard-supplies/src/content/helpTooltips.ts` | Ajuda | — | INCORPORAR textos no help do Portal | E16 | CONFIRMADO_NO_CODIGO |
| Inventário plugins | `docs/08-plugins/README.md` | doc | — | Atualizar na E3 (hoje omite purchase-requests) | E3 | DRIFT |
| Esta pasta | `docs/12-roadmap-e-evolucao/supplies/` | doc | Portal | canônico | E0 | este trabalho |

---

## I. Legado / fixture / nomenclatura

| Ativo | ID | Tipo | Owner atual | Função | Permission | Status | Decisão Portal | Fase | Evidência |
|-------|----|------|-------------|--------|------------|--------|----------------|------|-----------|
| Fixture RBAC Portal | `supplies` / `supplies.view` | teste | portal | fixture árvore RBAC | `supplies.view` | só teste | FORA_DO_ESCOPO (ajustar teste na E3) | E3 | rbacAccessTree.test.ts |
| Path PT ESTSEG | `/analise-consumo` | rota | estoque-seguranca | análise consumo | access | ativo | Alias no Portal `/consumption-analysis`; path novo EN | E8 | english-code-identifiers · legado PT |
| Perms `filial-sc/es` | estoque + terceiros | RBAC | manifests | filial | — | ativo | Alias → `filial-01/02` | E3 | DRIFT vs purchase-requests |
| `materiais-terceiros` | plugin | MFE | Produção/beneficiamento | SB6 cliente | access + filial | ativo | FORA_DO_ESCOPO | — | README: materiais de **clientes** |

---

## Contagens

| Classe | Qtd |
|--------|-----|
| MFEs nativos de compras/estoque (A) | 3 (+ 1 terceiros fora) |
| BIs PO sem git | 6 |
| APIs a gateway | api-delpi, SI, purchase-requests-api, (qualidade/financeiro HTTP) |
| `supplies-api` | 0 |
