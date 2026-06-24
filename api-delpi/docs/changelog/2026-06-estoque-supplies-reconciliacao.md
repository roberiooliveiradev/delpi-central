# Changelog — estoque Suprimentos (jun/2026)

## Contexto

Gap entre dashboard `GET /supplies/stock-value` e Registro de Inventário TOTVS (filiais 01/02, maio/2026). Playbook: `docs/roadmaps/playbook-correcao-estoque-supplies-inventario.md`.

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

## Pendente

- **W3** EM PROCESSO — decisão de negócio
- Fechamentos SB9 mar–mai/2026 na Controladoria para validar `auto` em produção
