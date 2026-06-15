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

> **Atenção — montagem dupla:** em `main.py` o mesmo router é incluído com `prefix="/financial"` e `prefix="/finacial"` (typo legado).  
> **URLs efetivas (equivalentes):** `/financial/rol` e `/finacial/rol` — prefira `/financial/*` em novas integrações.

| Método | Rota (preferida) | Descrição |
|---|---|---|
| GET | `/financial/rol` | Receita Operacional Líquida (ROL). |
| GET | `/financial/ebitda_pct` | EBITDA % (planilha; filial vazia = consolidado). |
| GET | `/financial/fixed_cost_pct` | Custos fixos % (planilha; filial vazia = consolidado). |
| GET | `/financial/pmr` | Prazo médio de recebimento. |

---

## Comercial — `/commercial`

| Método | Rota | Descrição |
|---|---|---|
| GET | `/commercial/head_office_rol_target_pct` | Meta % ROL matriz (filial fixa `01`). |
| GET | `/commercial/branch_rol_target_pct` | Meta % ROL filial (filial fixa `02`). |
| GET | `/commercial/closing-rate` | Taxa de conversão de vendas. |
| GET | `/commercial/sales-order-otd` | OTD de pedidos de venda (linhas SC6 entregues no prazo). |
| GET | `/commercial/new-business-rol-pct` | % ROL de novos negócios (exclui clientes WEG). |
| GET | `/commercial/new-clients-average` | Média mensal de novos clientes. |
| GET | `/commercial/new-clients-rol-pct` | % do ROL de clientes novos. |
| GET | `/commercial/rol/series` | Série temporal de ROL (`granularity`: day, week, month, year). |

---

## RH — `/hr`

**Permissão:** `api-delpi.access` **ou** `dashboard-hr.view`

| Método | Rota | Descrição |
|---|---|---|
| GET | `/hr/branches` | Filiais disponíveis no Portal RH. |
| GET | `/hr/snapshot` | Snapshot agregado (headcount, turnover, PDI, avaliações). |
| GET | `/hr/active-pdi-count` | Contagem/detalhe de PDIs ativos. |
| GET | `/hr/performance-reviews-completion` | Conclusão de avaliações de desempenho. |

Parâmetros comuns: `branch`, `start_date`, `end_date` (normalização de datas Portal RH).

---

## Produção — `/production`

| Método | Rota | Descrição |
|---|---|---|
| GET | `/production/direct_labor_cost_pct` | Custo de mão de obra direta % ROL. |
| GET | `/production/production_cost_pct` | Custo de produção % ROL. |
| GET | `/production/depreciation_pct` | Depreciação % ROL. |
| GET | `/production/overall_equipment_effectiveness_pct` | OEE (%) — média agregada de `H6_ZEFICI` (SH6010). |
| GET | `/production/oee` | OEE produção — resumo, listagem paginada de apontamentos SH6010, filtros `status` (`valid` / `outlier`) e `product_type` (`PA` / `PI`). |
| GET | `/production/oee/appointments/{appointment_id}` | Detalhe do apontamento — roteiro (SG2), estrutura (BOM), análise de tempos e **`time_analysis.findings`** (alertas automáticos). |
| GET | `/production/oee/series` | Série temporal de OEE por filial. |
| GET | `/production/eficiencia-fabril/dashboard` | Dashboard eficiência fabril (agregado SQL + paginação; `items[].appointment_id`). |
| GET | `/production/eficiencia-fabril/appointments` | Apontamentos eficiência fabril (carga bulk; `appointment_id` para detalhe). |
| GET | `/production/on_time_delivery_pct` | OTD produção (%) — apenas OPs de PA (`SB1010.B1_TIPO = 'PA'`). |
| GET | `/production/otd` | OTD produção — resumo, listagem paginada de OPs de PA e filtro `status` (`on_time` / `late`). |
| GET | `/production/otd/series` | Série temporal de OTD por filial. |

**Faixa válida de eficiência (OEE e eficiência fabril):** 0–199% — ver [regras-faixa-eficiencia-producao.md](./regras-faixa-eficiencia-producao.md).

**Listagem OEE (`GET /production/oee`):** mesma view e filtros da eficiência fabril (`build_fabril_view_filters`); `oee_pct` na listagem = `EFICIENCIA_PERCENTUAL`; `appointment_id` via `production_fabril_sh6010_apply` para detalhe.

**Detalhe (`GET /production/oee/appointments/{id}`):** diagnóstico em `time_analysis.findings` via `production_appointment_time_analysis` (faixa 0–199%, tempos, roteiro, divergências).

**Rotas operacionais (Playbook 15):** consumo, OPs, perdas, programação — ver [13-producao-operacional.md](./13-producao-operacional.md).  
**Compras ranking:** `GET /purchases/top-products` — mesma doc.

---

## Suprimentos — `/supplies`

| Método | Rota | Descrição |
|---|---|---|
| GET | `/supplies/cpv` | Custo de produto vendido (top fornecedores). |
| GET | `/supplies/otd` | On-Time Delivery compras. |
| GET | `/supplies/stock-value` | Valor total de estoque (atual ou histórico estimado). Ver [supplies-estoque-historico.md](./supplies-estoque-historico.md). |
| GET | `/supplies/inventory-turnover` | Giro de estoque (IDD). |
| GET | `/supplies/negotiation-savings/summary` | Economia em negociações de compras (Google Sheets `idd_suprimentos`). |

Parâmetros adicionais:

| Rota | Parâmetro extra |
|---|---|
| `/cpv`, `/otd` | `top_limit` (default `5`, máx. `20`) |
| `/otd` | `details_limit` (default `20`, máx. `100`) |
| `/stock-value` | `start_date`, `end_date` (histórico estimado SB9+SD3; ambos obrigatórios juntos), `location` (só modo atual), `top_limit` |
| `/inventory-turnover` | `location`, `strict_idd_period` (bool) |

---

## Engenharia — `/engineering`

**Permissão:** `api-delpi.access` **ou** `dashboard-lmps.view`

### LMP (Lista de Materiais de Projeto / ordens especiais)

| Método | Rota | Descrição |
|---|---|---|
| GET | `/engineering/lmps` | Lista LMPs com filtros de data/filial. |
| GET | `/engineering/lmps/dashboard` | Dashboard agregado (`status` default `Todos`). Dados completos com items paginados. |
| GET | `/engineering/lmps/dashboard/summary` | Apenas KPIs (`total_lmps`, `total_items`, `percent_dentro_prazo`, `avg_lead_time`). Query leve (`eng_resumo_lite`, sem `ORDER BY`). Fase 1 do carregamento progressivo. |
| GET | `/engineering/lmps/dashboard/items` | Itens paginados do dashboard (tabela). |
| GET | `/engineering/lmps/dashboard/charts` | Dados de gráficos (levelData, statusData, leadByLevel, evolutionData). Fase 2 do carregamento progressivo. |
| GET | `/engineering/lmps/{sale_number}` | Detalhe por número de venda/ordem (OV). Mesmo escopo de classificação do dashboard quando informados `date_start`, `date_end` e `branch`. |

**MFE `dashboard-lmps`:** tabela via `/dashboard/items` (ou carregamento progressivo legado `/dashboard`); clique na linha abre `/apps/dashboard-lmps/ov/{sale_number}` no frontend, que consome **`GET /engineering/lmps/{sale_number}`** (não há rota duplicada de detalhe).

| Query (detalhe `/lmps/{sale_number}`) | Descrição |
|---|---|
| `date_start`, `date_end` | Período — alinha candidatos ao dashboard. |
| `branch` | Filial — recomendado quando a OV existe em mais de uma filial. |

| Resposta `meta.relatedRoutes` (detalhe) | Descrição |
|---|---|
| `detail` | Esta OV (`/engineering/lmps/{sale_number}`). |
| `dashboardItems`, `dashboardSummary`, `dashboardCharts` | Rotas agregadas do painel. |
| `list` | Listagem paginada `/engineering/lmps`. |

> **Carregamento progressivo:** o frontend chama `/summary` → `/charts` → `/items` (ou `/dashboard` legado). A página renderiza KPIs/gráficos antes da tabela; detalhe da OV é rota separada acima.

| Query (listagem) | Descrição |
|---|---|
| `date_start`, `date_end` | Período. |
| `branch` | Filial. |
| `listing_type` | `Todos` (default), `LMP`, `Amostra` ou `Outro`. Com `LMP`, a SQL omite OVs «Outro» sem âncora de listagem (`EngSupportOvRef`). |
| `status` | Filtro de status do dashboard (`Todos`, `Pontual`, `Atrasado`, …). |
| `page`, `page_size` | Paginação (apenas `/dashboard` e `/items`). |

**Performance (`/dashboard/summary`):**

- Repositório: batch com temp tables, `eng_resumo_lite=True`, sem ordenação final.
- Integradores que só precisam de KPI de LMP (ex.: Strategic Indicators) devem enviar `listing_type=lmp`.
- Cache: resposta final em `query_cache` (namespace `lmp-dashboard`, chave `|summary-response`) + linhas em `|summary-rows` (TTL alinhado ao `QUERY_CACHE_TTL_SECONDS`, default 300s).
- Console: `operation_id=get_lmps_dashboard_summary`; alerta `slow_sql` acima de 2500 ms — validar após deploy com caller `strategic-indicators-api` e aba Cache.

### Transforma Mais

| Método | Rota | Descrição |
|---|---|---|
| GET | `/engineering/transforma-mais/processes` | Lista processos de melhoria. |
| GET | `/engineering/transforma-mais/processes/summary` | Resumo agregado. |

Filtros de processos: `id`, `name_process`, `filial_id`, `sector_name`, `status`, `start_date`, `end_date`.

---

## Qualidade (métricas TOTVS) — `/quality`

**Permissão:** `api-delpi.quality.access` **ou** `dashboard-quality.view`

Consultas analíticas (TOTVS Protheus e Google Sheets).

| Método | Rota | Descrição |
|---|---|---|
| GET | `/quality/branches` | Filiais disponíveis para filtros. |
| GET | `/quality/nonconformities` | Lista NC do Protheus. |
| GET | `/quality/nonconformities/series` | Série temporal de NC. |
| GET | `/quality/kaizens/summary` | Resumo de kaizens. |
| GET | `/quality/kaizens/{kaizen_id}` | Detalhe de um kaizen. |
| GET | `/quality/audit-5s/summary` | Resumo auditorias 5S. |
| GET | `/quality/ppm/internal/summary` | PPM interno (resumo). |
| GET | `/quality/ppm/external/summary` | PPM externo (resumo). |
| GET | `/quality/ppm/internal/series` | Série PPM interno. |
| GET | `/quality/ppm/external/series` | Série PPM externo. |
| GET | `/quality/ppm/internal` | PPM interno (detalhado). |
| GET | `/quality/ppm/external` | PPM externo (detalhado). |

### GET /quality/nonconformities

| Query | Descrição |
|---|---|
| `type` | `internal`, `external` ou `all` (default). |
| `branch`, `date_start`, `date_end` | Filtros. |
| `status`, `item_code`, `description` | Filtros adicionais. |
| `page`, `page_size` | Paginação. |

### GET /quality/kaizens/summary

**Fonte:** Google Sheets (`QUALITY_SHEET_ID` + `QUALITY_KAIZEN_SHEET_GID`). Não usa TOTVS.

| Query | Descrição |
|---|---|
| `title` | Filtro parcial no título (`descricao`). |
| `status` | Filtro exato de status (ex.: `implantado`). |
| `branch` | Filial (`filial`). |
| `date_start`, `date_end` | Intervalo de datas (`DD-MM-YYYY`, `YYYY-MM-DD` ou `DD/MM/YYYY`). Opcionais — omitidos, `list_kaizen` traz todos os implantados. |

**Contagem (`total_kaizens`):** kaizens com status *implantado* cuja data de implantação (`data`) cai no intervalo (quando `date_start`/`date_end` informados).

**Ganhos (`total_savings`):** para cada kaizen *implantado* com dias ativos no período, soma `daily_savings × dias ativos`. Kaizens implantados antes do `date_start` continuam gerando ganho nos dias do intervalo (desde a data de implantação até `date_end`).

**Listagem (`list_kaizen`):** itens com `id`, `annual_savings` (`daily_savings × 365`) e demais campos cadastrais. O dashboard de qualidade usa chamada sem datas para catálogo completo na tabela.

#### Planilha — colunas lidas

| Coluna (header) | Campo API | Observação |
|---|---|---|
| `filial` | `branch` | |
| `descricao` | `title` | |
| `responsavel` | `accountable` | |
| `area_setor` | `sector` | |
| `custo_investimento` | `investment` | |
| `segudos_por_ocorrecia` / `segundos_por_ocorrencia` | — | Entrada do cálculo (aliases aceitos). |
| `ocorrecias_por_dia` / `ocorrencias_por_dia` | — | Entrada do cálculo (aliases aceitos). |
| `custo_hora` | — | Entrada do cálculo. |
| `status` | `status` | |
| `data` | `date_implemented` | Data de implantação. |
| `deleted` | — | Linhas marcadas são ignoradas. |

**Não ler da planilha:** `horas_poupadas_dia` e `ganho_diario` — removidas da planilha; a API calcula o ganho diário.

#### Cálculo

```
horas_poupadas_dia = (segundos_por_ocorrencia × ocorrencias_por_dia) / 3600
daily_savings      = horas_poupadas_dia × custo_hora   # arredondado em 2 casas
annual_savings     = daily_savings × 365               # arredondado em 2 casas
```

Se alguma das três entradas estiver ausente, `daily_savings` e `annual_savings` são `null` e o kaizen não contribui para `total_savings`.

#### Exemplo de resposta (`data`)

```json
{
  "date_start": "01-01-2026",
  "date_end": "31-01-2026",
  "total_kaizens": 1,
  "total_savings": 22.62,
  "list_kaizen": [
    {
      "id": "01-16/01/2026-App resina CT-16",
      "title": "App resina CT-16",
      "date_implemented": "16/01/2026",
      "status": "implantado",
      "accountable": "Ossamu",
      "sector": "Produção",
      "investment": 620.0,
      "daily_savings": 7.54,
      "annual_savings": 2752.10,
      "branch": "01"
    }
  ]
}
```

### GET /quality/kaizens/{kaizen_id}

**Fonte:** mesma planilha. Path: `kaizen_id` = `list_kaizen[].id` (ex.: `01-16/01/2026-App resina CT-16`).

Retorna ficha completa com entradas do cálculo: `seconds_per_occurrence`, `occurrences_per_day`, `hourly_cost`, `hours_saved_per_day`, além dos campos do resumo.

**operationId:** `get_kaizen_by_id` · **meta.entity:** `kaizen` · **meta.shape:** `scalar`

Testes unitários: `api-delpi/tests/test_kaizen_repository.py`. Integração Sheets: [12-testes-sem-totvs-google-sheets.md](./12-testes-sem-totvs-google-sheets.md).
