# 06 — Módulos departamentais

Métricas e consultas analíticas por área, alimentadas principalmente pelo **TOTVS Protheus**.

**Permissão padrão:** `api-delpi.access` (exceto engenharia e qualidade, indicados abaixo).

**Formato:** envelope `{ success, message, data }`.

Parâmetros comuns de período:

| Parâmetro | Descrição |
|---|---|
| `branch` | Filial (2 caracteres quando validado). |
| `start_date` / `end_date` | Intervalo de análise. |

---

## Financeiro

> **Atenção — prefixo duplicado:** em `main.py` o router é montado com `prefix="/finacial"` (typo) e o router interno usa `prefix="/financial"`.  
> **URL efetiva:** `/finacial/financial/{endpoint}`

| Método | Rota completa | Descrição |
|---|---|---|
| GET | `/finacial/financial/rol` | Receita Operacional Líquida (ROL). |
| GET | `/finacial/financial/ebitda_pct` | EBITDA % (planilha; filial vazia = consolidado). |
| GET | `/finacial/financial/fixed_cost_pct` | Custos fixos % (planilha; filial vazia = consolidado). |
| GET | `/finacial/financial/pmr` | Prazo médio de recebimento. |

---

## Comercial — `/commercial`

| Método | Rota | Descrição |
|---|---|---|
| GET | `/commercial/head_office_rol_target_pct` | Meta % ROL matriz (filial fixa `01`). |
| GET | `/commercial/branch_rol_target_pct` | Meta % ROL filial (filial fixa `02`). |
| GET | `/commercial/closing-rate` | Taxa de conversão de vendas. |
| GET | `/commercial/new-clients-average` | Média mensal de novos clientes. |
| GET | `/commercial/new-clients-rol-pct` | % do ROL de clientes novos. |

---

## Produção — `/production`

| Método | Rota | Descrição |
|---|---|---|
| GET | `/production/direct_labor_cost_pct` | Custo de mão de obra direta % ROL. |
| GET | `/production/production_cost_pct` | Custo de produção % ROL. |
| GET | `/production/depreciation_pct` | Depreciação % ROL. |
| GET | `/production/overall_equipment_effectiveness_pct` | OEE. |
| GET | `/production/on_time_delivery_pct` | On-Time Delivery (OTD produção). |

---

## Suprimentos — `/supplies`

| Método | Rota | Descrição |
|---|---|---|
| GET | `/supplies/cpv` | Custo de produto vendido (top fornecedores). |
| GET | `/supplies/otd` | On-Time Delivery compras. |
| GET | `/supplies/stock-value` | Valor total de estoque. |
| GET | `/supplies/inventory-turnover` | Giro de estoque (IDD). |

Parâmetros adicionais:

| Rota | Parâmetro extra |
|---|---|
| `/cpv`, `/otd` | `top_limit` (default `5`, máx. `20`) |
| `/otd` | `details_limit` (default `20`, máx. `100`) |
| `/stock-value` | `location`, `top_limit` |
| `/inventory-turnover` | `location`, `strict_idd_period` (bool) |

---

## Engenharia — `/engineering`

**Permissão:** `api-delpi.access` **ou** `dashboard-lmps.view`

### LMP (Lista de Materiais de Projeto / ordens especiais)

| Método | Rota | Descrição |
|---|---|---|
| GET | `/engineering/lmps` | Lista LMPs com filtros de data/filial. |
| GET | `/engineering/lmps/dashboard` | Dashboard agregado (`status` default `Todos`). |
| GET | `/engineering/lmps/{sale_number}` | Detalhe por número de venda/ordem. |

| Query (listagem) | Descrição |
|---|---|
| `date_start`, `date_end` | Período. |
| `branch` | Filial. |
| `page`, `page_size` | Paginação. |

### Transforma Mais

| Método | Rota | Descrição |
|---|---|---|
| GET | `/engineering/transforma-mais/processes` | Lista processos de melhoria. |
| GET | `/engineering/transforma-mais/processes/summary` | Resumo agregado. |

Filtros de processos: `id`, `name_process`, `filial_id`, `sector_name`, `status`, `start_date`, `end_date`.

---

## Qualidade (métricas TOTVS) — `/quality`

**Permissão:** `api-delpi.quality.access` **ou** `dashboard-quality.view`

Consultas analíticas; **não** confundir com o módulo NC PostgreSQL ([07-qualidade-nc.md](./07-qualidade-nc.md)).

| Método | Rota | Descrição |
|---|---|---|
| GET | `/quality/nonconformities` | Lista NC do Protheus. |
| GET | `/quality/kaizens/summary` | Resumo de kaizens. |
| GET | `/quality/audit-5s/summary` | Resumo auditorias 5S. |
| GET | `/quality/ppm/internal/summary` | PPM interno (resumo). |
| GET | `/quality/ppm/external/summary` | PPM externo (resumo). |
| GET | `/quality/ppm/internal` | PPM interno (detalhado). |
| GET | `/quality/ppm/external` | PPM externo (detalhado). |

### GET /quality/nonconformities

| Query | Descrição |
|---|---|
| `type` | `internal`, `external` ou `all` (default). |
| `branch`, `date_start`, `date_end` | Filtros. |
| `status`, `item_code`, `description` | Filtros adicionais. |
| `page`, `page_size` | Paginação. |
