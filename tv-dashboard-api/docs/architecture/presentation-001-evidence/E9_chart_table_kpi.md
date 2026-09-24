# E9 — Chart / table / KPI visual config

**Status:** IMPLEMENTED

- `chartOptions` / `kpiParts` / `kpiOptions` materializados em create defaults.
- Deep-merge em upsert para `chartOptions|chartParts|tableOptions|tableParts|kpiOptions|kpiParts`.
- Projeção de dados já BE (`serverProjectionApplied`); visual config agora também canônica no create/mutation.
