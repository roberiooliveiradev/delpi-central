# Smoke live — turnos complexos + matriz MP/PA + indicadores

**Status:** vigente  
**Harness estrutural:** [`scripts/smoke_complex_consolidated_turns_live.py`](../scripts/smoke_complex_consolidated_turns_live.py) (C1–C5)  
**C4 PA (L1–L4 leve):** [`scripts/smoke_c4_conversation_live.py`](../scripts/smoke_c4_conversation_live.py)  
**C5 MP (L1–L4 leve):** [`scripts/smoke_c5_mp_stock_followup_live.py`](../scripts/smoke_c5_mp_stock_followup_live.py)  
**Wave I indicadores:** [`scripts/smoke_indicators_live.py`](../scripts/smoke_indicators_live.py)  
**Wave B playbook:** [`scripts/smoke_playbook_product_routes.py`](../scripts/smoke_playbook_product_routes.py)  
**Protocolo:** [`chat-ai-flow-families.md`](./chat-ai-flow-families.md) §16.1  

Evidence:

- [`evidence/chat-complex-consolidated-turns-live.json`](./evidence/chat-complex-consolidated-turns-live.json)
- [`evidence/chat-c4-conversation-live.json`](./evidence/chat-c4-conversation-live.json)
- [`evidence/chat-c5-mp-stock-followup-live.json`](./evidence/chat-c5-mp-stock-followup-live.json)
- [`evidence/chat-indicators-live.json`](./evidence/chat-indicators-live.json)
- [`evidence/chat-playbook-product-routes-live.json`](./evidence/chat-playbook-product-routes-live.json)

---

## 1. Harness vs release

```text
HARNESS PASS  =  PASS_ESTRUTURAL
≠  PASS de release / “passou para o usuário”
```

Release exige **L1 ∧ L2 ∧ L3 ∧ L4**.

---

## 2. Fixtures (env)

| Env | Default | Uso |
|-----|---------|-----|
| `SMOKE_PA_CODE` | `90260149` | C1/C2/C4 |
| `SMOKE_MP_CODE` | `10080022` | C5 estoque/vendas |
| `SMOKE_PA_BOM_CODE` | `90261255` | cost-impact playbook |
| `SMOKE_PA_FABRIL_CODE` | `90269002` | factory/shipping/exclusivity |
| `SMOKE_MP_PRICE_CODE` | `10080001` | preço/compras MP |
| `SMOKE_BRANCH` | `01` | ROL/KPI filial |
| `SMOKE_PERIOD` | `agosto 2026` | financial/commercial |

Regra:

```text
BOM / árvore / fabril / cost-impact → PA
estoque / compras / preço MP / parents → MP
ROL / closing-rate / OTD → nenhum produto (filial + período)
```

---

## 3. Wave A — casos C1–C5

| ID | Kind | Pedido | L1 mínimo |
|----|------|--------|-----------|
| **C1** | PA | integrado ficha+estrutura+roteiro+estoque | analyser/structure + stock |
| **C2** | PA | BOM + estoque + open-orders | structure + stock + open-orders/sales |
| **C3 / I2** | none | ROL KPI + série | commercial/financial rol; **forbid** stock-only e department-indicators |
| **C4** | PA | seed estoque → FU estrutura + cobre demanda | stock; FU structure+stock |
| **C5** | MP | seed estoque → FU cobertura/vendas | stock; FU stock e/ou sales (**não** exige structure) |

---

## 4. Wave I — indicadores (I1–I6)

| ID | Path canônico | Nota |
|----|---------------|------|
| **I1** | `/financial/rol` | «ROL filial 01» |
| **I2** | `/commercial/rol/series` (ou summary/financial) | = reforço C3 |
| **I3** | negativo | falha se **só** `/commercial/rol/by-branch` |
| **I4** | `/commercial/closing-rate` | taxa de fechamento |
| **I5** | `/commercial/sales-order-otd` | OTD pedidos |
| **I6** | negativo | **forbid** department-indicators / IDD |

Backlog I-ext (documentado, não obrigatório nesta entrega): invoices, by-customer/product, new-business, SI TV, OTD irmãos.

---

## 5. Wave B — playbook produto (L1 path)

Fixture por rota: MP preço/compras; PA BOM/fabril. Inclui **MP7** negativo (cost-impact com MP não pode ok).

---

## 6. Wave C — gaps `/products` (backlog)

| Path | Fixture |
|------|---------|
| `/parents` | MP |
| `/internal-movements` | MP/PA |
| `/inbound-invoice-items` | MP |
| `/outbound-invoice-items` | PA |
| `/raw-material-set-shortages` | PA |
| `/sales` / `/sales/billing` | PA (código ≠ ROL) |
| `/customers` | PA |
| `/suppliers` | MP |
| `/guide` | PA `90260142` |
| `/inspection` | PA |
| `/products/search` | ambos |
| `/summary` | negativo anti-estoque |

---

## 7. Rubrica L1–L4

| Camada | Fail típico |
|--------|-------------|
| **L1** | estoque→`/summary`; C5 sem stock/sales; ROL filial→só by-branch; department-indicators no comercial |
| **L2** | prosa nega estoque com tool ok; inventa meta |
| **L3** | tree `—`/`unknown`; BOM duplicado; markdown `##` colado |
| **L4** | subtarefa pedida ausente |

---

## 8. Execução

```bash
# Wave A estrutural C1–C5
SMOKE_BASE_URL=http://localhost \
SMOKE_AGENT_ID=4f9c225b-0414-40d3-a462-040889719b83 \
python3 -u scripts/smoke_complex_consolidated_turns_live.py

# reexecução parcial
SMOKE_CASE_IDS=C5-mp-stock-sales-followup python3 -u scripts/smoke_complex_consolidated_turns_live.py

# C4 PA + C5 MP (L leve)
python3 -u scripts/smoke_c4_conversation_live.py
python3 -u scripts/smoke_c5_mp_stock_followup_live.py

# Wave I
python3 -u scripts/smoke_indicators_live.py

# Wave B (latência default 90s; refresh token por cenário)
SMOKE_BASE_URL=http://localhost python3 -u scripts/smoke_playbook_product_routes.py
```

Reiniciar `delpi-minha-delpi-ai-api` após mudanças de código (Flask sem `--reload`).
Em host com pouca RAM (~8 Gi), o gateway pode cair em turnos longos — aguardar recovery antes da próxima wave.

Placar:

```text
CASO | kind | L1 | L2 | L3 | L4 | HARNESS | RELEASE
```

## 9. Placar desta bateria (2026-09-08)

| CASO | kind | HARNESS | RELEASE | Notas |
|------|------|---------|---------|-------|
| C1 | PA | PASS | WARN | analyser+stock |
| C2 | PA | PASS | PASS | structure+stock+open-orders |
| C3 | none | PASS | PASS | rol/series |
| C4 | PA | PASS | PASS | smoke_c4 L1–L4 leve OK |
| C5 | MP | PASS | WARN | stock ok; structure indesejada; vendas ausentes |
| I1 | none | FAIL | FAIL | by-branch em vez de financial/rol |
| I2 | none | PASS | PASS | series |
| I3 | none | FAIL | FAIL | negativo: ainda by-branch-only |
| I4 | none | PASS | PASS | closing-rate |
| I5 | none | PASS | PASS | sales-order-otd |
| I6 | none | PASS | PASS | sem department-indicators |
| Wave B | mix | 8/12 | FAIL | F1/F2 path errado; cost-impact/pricing miss; MP7 OK |

Release global desta bateria: **FAIL** (I1/I3 + gaps Wave B + WARN C5).
Harness Wave A estrutural: **5/5 PASS_ESTRUTURAL**.
