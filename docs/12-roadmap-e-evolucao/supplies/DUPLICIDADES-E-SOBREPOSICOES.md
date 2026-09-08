# Duplicidades e sobreposições — Suprimentos

> Correlação ≠ identidade de regra. Sem dump do BI, **não** declarar duplicata perfeita.

---

## DRIFTs transversais

| ID | Fontes | Prevalece | Impacto | Ação |
|----|--------|-----------|---------|------|
| D1 | `purchase-requests.unit.filial-01/02` vs `estoque-seguranca.view.filial-sc/es` vs `inspecoes-entrada.view.filial-01/02` | Portal: **eixo B** `supplies.unit.filial-{TOTVS}` (ADR-006); legado vira alias | UX e papéis inconsistentes até cutover | Não criar `{feature}.filial-sc`; nova unidade = um code só |
| D2 | `docs/08-plugins/README.md` omite `purchase-requests` vs Compose ativo | Compose + manifesto | Inventário oficial incompleto | Atualizar README plugins na E3 |
| D3 | Playbook Comercial ainda cita codes granulares vs `PERFIS` com 3 codes | PERFIS + manifest commercial | Não copiar o playbook desatualizado | Seguir condensação **com** justificativa extra para Suprimentos (filial + SC) |
| D4 | Fixture `supplies.view` vs catálogo alvo `supplies.access` | ADR-004 + padrão commercial.access | Colisão semântica no teste | Ajustar fixture E3 |
| D5 | Path `/analise-consumo` PT vs regra EN em rota nova | english-code-identifiers | Alias no cutover | Path novo `/consumption-analysis` |
| D6 | Savings: Sheets IDD (realizado) vs SI (meta/realizado snapshot) | SI = meta canônica; Sheets = origem do realizado de economia via api-delpi | Duas superfícies, uma ficha | KPI-SAVINGS |

---

## 24.1 Atraso de Fornecedores BI × Dashboard OTD

| Dimensão | Dashboard `/otd` | BI «Atraso de Fornecedores - SC» |
|----------|------------------|----------------------------------|
| Universo | Linhas elegíveis MP **ou** código `3019*` | **Desconhecido** (não no git) |
| Fonte | api-delpi `get_supplies_otd` + ranking na própria página | Core/Power BI? |
| Regra atraso | Recebimento **depois** da data prometida | Desconhecida |
| Data prometida | Help: recebimento ≤ prometida = on-time | Desconhecida |
| Recebimento | Linhas recebidas no período | Desconhecida |
| Fornecedor | Chart `lateSuppliers` + amostra entregas | Provável matriz |
| Filial | Filtro `branch` (consolidado possível) | Nome do app: **SC** |
| Período | start/end / competência | Desconhecido |
| Granularidade | % OTD + linhas on-time/late + ranking | Possível matriz fornecedor×tempo |
| Export | PDF/tabular cliente | Desconhecido |
| Detalhe / histórico | Seção na OTD, não rota própria | Desconhecido |

**Veredito:** **complementar / possivelmente especializado (SC)**, não «duplicado comprovado».  
Há também `get_supplies_purchase_order_otd` / `panel` / `series` na api-delpi **sem MFE dedicado**. **CONFIRMADO_NO_CODIGO.** O Portal WF-07 deve consumir essas ops **antes** de inventar SQL.

**HIPOTESE_A_VALIDAR (E1.S1 + E9):** se o BI for só ranking de atraso SC, a página OTD+panel pode ser paridade; se for matriz com regras diferentes (ex. só SC7 aberto), são produtos distintos — BI permanece MANTER_EXTERNO até ficha.

---

## 24.2 Controle de Estoques BI × Dashboard `/stock` × ESTSEG

Separar conceitos (não misturar no mesmo KPI):

| Conceito | Dashboard `/stock` | ESTSEG plugin | BI Controle Estoques SC | `stock-balances` API |
|----------|--------------------|---------------|-------------------------|----------------------|
| Estoque físico / qtd | Sim (qty + locations) | Saldo 01+98+99 vs ESTSEG | ? | Sim items/summary |
| Valor | SB9 valor | Não é o foco | ? | Parcial |
| Local / armazém | Filtro `location` | Locais na regra de déficit | ? | Sim |
| Giro | Página **outra** (`/inventory-turnover`) | Não | ? | Não |
| Cobertura | Giro em **meses** (auxiliar) | Projeção SC7/SD4 no detalhe | ? | Não |
| Estoque de segurança | Não | **Canônico** BZ_ESTSEG | Nome do app PO mistura «análise estoque» | Não |
| Projeção / ruptura | Não | Extrato + simulação consumo | ? | Não |

**Veredito:** **não são o mesmo produto**. Dashboard = valor gerencial. ESTSEG = planejamento de MP. BI SC = **LEGADO_A_VALIDAR**. Portal ganha duas rotas (WF-15 controle, WF-16 segurança) + Produto 360 que **compõe** os três.

---

## 24.3 Indicadores Sheets × Strategic Indicators

| | Sheets IDD (PO + composer) | SI `supplies-*` |
|--|----------------------------|-----------------|
| CPV / OTD / giro / valor | Dashboard calcula no TOTVS e compara meta SI | Snapshot oficial meta×realizado |
| Savings | **Origem do lançamento** = planilha (`get_supplies_negotiation_savings_summary`) | Indicador `supplies-negotiation-savings` |
| Permissão | `dashboard-supplies.view` no git; `idd-suprimentos.access` só no PO | Perms SI |

**Fonte de verdade:**

- **Fórmula TOTVS** (CPV, OTD, estoque, giro) = api-delpi.  
- **Meta** = strategic-indicators-api.  
- **Economia lançada** = Sheets via api-delpi (não copiar para Postgres).  
- **Não** manter segunda meta canônica na planilha.

Se o app «Indicadores de Suprimentos - Sheets» for só a planilha crua, decisão pós-dump: **MANTER_EXTERNO** (edição) + Portal **INTEGRAR** leitura já existente.

---

## 24.4 Onde o item é usado

| Superfície | Contrato | Owner |
|------------|----------|-------|
| Chat / produto | `GET /products/{code}/parents` `get_product_parents` | api-delpi |
| Também | `/{code}/structure`, exclusivity, raw-material-set-shortages | api-delpi |
| Plugin dedicado | **Não** | — |
| BI PO | desconhecido | Core? |

**Decisão:** Portal Produto 360 **consome** `parents` via supplies-api BFF. **Não** duplicar SQL. BI externo = deep link até dump. Chat continua usando o mesmo contrato.

---

## 24.5 Outras sobreposições

| Par | Relação |
|-----|---------|
| `purchase-order-otd` API × página OTD dashboard | API mais rica **sem UI** — Portal deve usar panel/series |
| TV `supplies_stock_alert` × ESTSEG déficit | Provável especialização TV; não absorver TV no MFE |
| Safety-stock suppliers + price-history × `/products/{code}/suppliers` + `purchase-price-history` | Família irmã; BFF do 360 escolhe o envelope mais completo **sem** juntar regras divergentes sem ficha |
| Frete financeiro × custo do item | Complementar; Portal não rateia |

---

## 24.6 O que NÃO está duplicado (falso positivo)

- `materiais-terceiros` (SB6 cliente) ≠ estoque de MP de compra.
- Inspeções de entrada ≠ alçada de compras.
- CPV (custo vendido) ≠ valor de estoque.
- `C7_APROV` (grupo de alçada no PC) ≠ status operacional da SC (`C1_APROV`).
