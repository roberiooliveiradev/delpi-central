# E5 — Defaults + create canônicos

**Status:** IMPLEMENTED

- `blockDefaults` reconciliado com FE (`chart_view` y:28/w:80/h:45; heading fontSize 56).
- Entries novas: `icon`, `canvas_table`, `input`, `data_metric`.
- `_with_block_defaults` materializa frame/style/**kpiParts/chartOptions/tableOptions/input**.
- Op `create_block` → upsert + defaults.
- Editor: `commitCreateBlock` → `POST …/presentation-mutations`.

Gate: create por tipo registrado coberto em `test_create_all_registered_default_types`.
