# CHANGELOG — api-delpi

**Código:** `LmpPeriodInclusionSemanticsService`, `period_inclusion_policy` — default **`work_month_lmp`**.

---

## 2026-07 — Datas de calendário na resposta → ISO (`YYYY-MM-DD`)

Contrato HTTP: datas de calendário (sem hora) serializadas como **`YYYY-MM-DD`** via `ResponseDateFormatService`. Inclui LMP, playbook/produto (`reference_date` primário), produção operacional (`period` / `reference_date` / `loss_date`), supplies (estoque/giro/estimation), despesas CC e propostas comerciais. Companions `*_iso` no playbook permanecem como alias deprecado (remoção planejada 2027-06). SQL/TOTVS e query params inalterados. `meta.dataVersion` → `2026-07`.

Gate: `scripts/audit_response_calendar_dates.py --check`.

---

## 2026-06 — Modelo `work_month_lmp` (padrão)

Listagem por **revisão com trabalho LMP no mês** (`first_eng` ou âncora na revisão) + **fallback âncora OV** (`anchor_in_period`) para não perder OVs do controle.

| Métrica | Jan–Jun/2026 vs RQ-060 |
|---------|-------------------------|
| Recall | **79/93 (84,9%)** |
| Jun/2026 | **12/12** interseção, 0 só-RQ |
| Abr/2026 | 12/16 (antes 8/16 com só âncora) |

Gate antes de merge: `scripts/validate_lmp_period_policies_vs_rq060.py`.

**Módulo:** `LMPQueryRepository._sql_work_month_lmp_candidates_cte`.

**Frontend (jun/2026):** colunas **Revisão** e **Ciclo** nos dashboards `dashboard-lmps` e `dashboard-engineering` (consomem `homolog_revision`, `measurement_revision`, `cycle_index`).

---

## 2026-06 — Modelo `homolog_cycles_in_period` (não padrão)

Implementação de listagem **por ciclo de homologação 000012** (`cycle_index`, revisão do ciclo). **Não** é o padrão: filtra pelo **mês da homolog** no Protheus, o que desalinha do controle RQ (ex.: jun/2026 8 vs 12 pastas). Substituído por **`work_month_lmp`**.

**Módulo:** `LMPQueryRepository._sql_homolog_cycle_candidates_cte`.

---

## 2026-06 — Filtro LMP por âncora no período (`anchor_in_period`)

Correção do dashboard/listagem LMP: o período passa a usar **âncora LMP** (`ListingAnchorEventos`) em vez de `anchor OR first_eng`, eliminando OVs que só tocaram engenharia no mês sem homologação/âncora no período.

Documentação: [lmp-2026-rq060-vs-dashboard-auditoria.md](./investigation/lmp-2026-rq060-vs-dashboard-auditoria.md) §6.

**Impacto:** mai/2026 23→20 OVs; jun/2026 mantém 12 (alinhado RQ-060).

**Módulo:** `LmpPeriodInclusionSemanticsService` + `LMPQueryRepository._sql_candidate_period_where_clause`.

---

## 2026-06 — Auditoria LMP: RQ-060 vs dashboard

Investigação de divergência entre controle interno (pastas LMP Ano + RQ-060) e `GET /engineering/lmps/dashboard/items` (jan–jun/2026). Extração automatizada de OVs dos Word, scripts de cruzamento e SQL de homologação (foco mai/jun).

Documentação: [lmp-2026-rq060-vs-dashboard-auditoria.md](./investigation/lmp-2026-rq060-vs-dashboard-auditoria.md).

**Scripts:** `scripts/investigate_lmp_period_vs_rq060.py`, `scripts/extract_rq060_via_powershell.ps1`, `scripts/sql/lmp_may2026_*`.

**Código preparatório (opt-in):** `LmpPeriodInclusionSemanticsService`, `period_inclusion_policy` (`anchor_or_first_eng` | `homolog_in_period`).

---

## 2026-06 — Vigência completa da BOM (SG1010)

Todas as rotas de produto que percorrem estrutura passam a usar filtro de **intervalo de vigência** (`G1_INI` + `G1_FIM`), não apenas `G1_FIM > hoje` nem ausência de filtro.

Detalhes: [bom-validity-filter-changelog-jun2026.md](./api/bom-validity-filter-changelog-jun2026.md).

**Módulo canônico:** `ProductBomValidityFilterService`.

**Rotas afetadas:** `/structure`, `/structure/excel`, `/structure/exclusivity`, `/analyser`, `/parents`, `/guide`, `/inspection`, `/directives`, `/factory-status`, `/production-status`, `/cost-impact-simulation`, catálogo `/exclusive-raw-materials/catalog`.

---

## 2026-06 — Conversão de unidades Protheus (MI / BOM / fiscal)

Playbook transversal para interpretação de `B1_UM`, BOM (`SG1010`), fiscal (`SB5010`) e convenção **1 MI = 1000 peças** nas rotas de produto.

Documentação: [playbook-conversao-unidades-protheus.md](./roadmaps/playbook-conversao-unidades-protheus.md).

**Módulo canônico:** `ProductPaBomReferenceService` + `app/content/product_pa_bom_reference.json`.

**Rotas afetadas:** `/structure`, `/structure/exclusivity`, `/cost-impact-simulation`, `/stock` (playbook), `/directives`, `/factory-status`.

---

## 2026-06 — Compras válidas de MP (NF de frete)

Última compra, diretivas e ranking de compras passam a excluir linhas de `SD1010` com `D1_QUANT = 0` (notas de frete alocadas no código da MP), além do filtro existente de transportadoras por nome.

Detalhes: [compras-validas-frete-mp-changelog-jun2026.md](./api/compras-validas-frete-mp-changelog-jun2026.md).

**Módulo canônico:** `PurchaseValidityFilterService.valid_purchase_filter_sql()`.

---

## 2026-06 — Contrato de respostas (Fase 5)

Normalização de campos Protheus na origem. Use `?legacy=true` para manter o formato antigo durante a transição.

| Campo antigo | Campo novo | Remoção prevista |
|---|---|---|
| `exclusive_raw_material: "SIM"/"NAO"` | `exclusive_raw_material: bool` + `exclusive_raw_material_label` | 2026-12 (com `legacy=true` até lá) |
| `has_stock_for_one_pa: "SIM"/"NAO"` | `has_stock_for_one_pa: bool` + `has_stock_for_one_pa_label` | 2026-12 |
| `production_started: "SIM"/"NAO"/"SIM_SC2"` | `production_started: bool` + `production_started_label` | 2026-12 |
| `pa_production_started` / `pi_production_started` (string) | bool + `*_label` em `summary` | 2026-12 |
| `reference_date` (YYYYMMDD) | mantido + `reference_date_iso` (ISO 8601) | `_iso` permanece; YYYYMMDD removível em 2027-06 |
| Query `location` (estoque) | Query `warehouse` (preferido; `location` aceito) | `location` removível em 2027-06 |
| `GET /products/{code}` (dump completo) | `?view=summary` (~15 campos) | opt-in; default `full` inalterado |

**Rotas afetadas:** `/structure/exclusivity`, `/production-status`, `/shipping-status`, `/factory-status`, `/stock`, `/products/{code}`.
