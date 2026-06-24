# Estoque Suprimentos — reconciliação e alinhamento MATR460 (jun/2026)

Gap entre dashboard `GET /supplies/stock-value` e Registro de Inventário TOTVS (filiais 01/02, maio/2026).

**Resumo executivo:** [estoque-supplies-matr460-resumo-jun2026.md](../roadmaps/estoque-supplies-matr460-resumo-jun2026.md)  
**Playbook:** [playbook-correcao-estoque-supplies-inventario.md](../roadmaps/playbook-correcao-estoque-supplies-inventario.md)

## W0 — Reconciliação

- Script `scripts/reconcile_stock_value.py` + SQL `scripts/sql/reconcile_stock_value_period.sql`
- Evidências: `docs/roadmaps/evidencias/estoque-reconciliacao-20260531.{md,json}`
- Achado: SB9010 sem fechamento após `20260228`; estimativa SD3 subestima vs. inventário

## W1 — Transparência

- `estimation` e `by_branch[]` com breakdown (base SB9, ponte, período, fechamento oficial)
- `data_quality_warning` quando base SB9 &lt; `end_date`
- MFE: `StockEstimationBreakdown` na aba Estoque

## W2 — `stock_method`

- Query `stock_method=auto|estimated|official_closure` (default `auto`)
- SQL `stock_value_official_closure_sql.py` — leitura SB9 em `B9_DATA = end_date`
- Fan-out consolidado para histórico (summary e bundle)
- MFE: banner de fechamento oficial quando `method=sb9_closure_on_end_date`

## W4 — IDD e payload compartilhado

- `stock_value_estimation_payload_service.py` — montagem única de `estimation` / `stock_estimation`
- `GET /supplies/inventory-turnover` herda o mesmo contrato de estoque (`stock_method=auto`)

## Investigação MATR460 no TOTVS (24/jun/2026)

- Script `scripts/investigate_matr460_inventory.py` + SQL `scripts/sql/investigate_matr460_inventory.sql`
- Evidências: `docs/roadmaps/evidencias/matr460-investigacao-totvs.{md,json}`
- Resumo executivo: `docs/roadmaps/estoque-supplies-matr460-resumo-jun2026.md`
- Achados: sem SB9 em 31/05/2026; SB2 ≈ EM ESTOQUE MATR460; proxy SC2 WIP << EM PROCESSO; sem view SQL do MATR460

## W5 — Modo híbrido (`register_snapshot`)

- `auto` / `hybrid`: sem SB9 na `end_date` → SB2 + proxy EM PROCESSO (locais 99/50/98)
- `estimated` mantém Kardex para análise
- Doc: [estoque-supplies-modo-hibrido.md](../roadmaps/estoque-supplies-modo-hibrido.md)

## Pendente

- **W3** EM PROCESSO — decisão de negócio; investigação TOTVS indica SC2 não basta (ver [resumo MATR460](../roadmaps/estoque-supplies-matr460-resumo-jun2026.md))
- Fechamentos SB9 mar–mai/2026 na Controladoria para validar `auto` em produção
- Script `investigate_matr460_inventory.py` + evidências `matr460-investigacao-totvs.*`
