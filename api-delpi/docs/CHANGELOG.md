# CHANGELOG — api-delpi

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
