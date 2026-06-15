# Mapeamento API — Dashboard LMPs

Base no browser (via gateway):

```text
/apps/api-delpi
```

Prefixo de engenharia:

```text
/engineering
```

**Permissões:** `dashboard-lmps.view` ou `api-delpi.access`  
**Envelope:** `{ "success": true, "message": "...", "data": { ... }, "meta": { ... } }`

Router backend: `api-delpi/app/interface/http/routes/engineering/engineering_router.py`

---

## Endpoints consumidos pelo plugin

| Função (`lmpApi.ts`) | Método | Rota | Uso na UI |
|----------------------|--------|------|-----------|
| `getLmpsDashboardSummary` | GET | `/engineering/lmps/dashboard/summary` | KPIs |
| `getLmpsDashboardCharts` | GET | `/engineering/lmps/dashboard/charts` | Gráficos |
| `getLmpsDashboardItems` | GET | `/engineering/lmps/dashboard/items` | Tabela |
| `getLmpBySaleNumber` | GET | `/engineering/lmps/{sale_number}` | Detalhe da OV — cabeçalho, produtos, KPIs (`list_history: []`) |
| `getLmpHistoryEvents` | GET | `/engineering/lmps/{sale_number}/history/events` | Eventos AIJ010 (timeline/tabela) |
| `getLmpHistoryFlow` | GET | `/engineering/lmps/{sale_number}/history/flow` | Transições engenharia (idas/voltas) |
| `getLmpsDashboard` | GET | `/engineering/lmps/dashboard` | Legado (fallback monolítico) |
| `listLmps` | GET | `/engineering/lmps` | Listagem paginada (não usada na página atual) |

**Detalhe da OV:** o MFE chama **`getLmpBySaleNumber`** + **`getLmpHistoryEvents`** + **`getLmpHistoryFlow`** em paralelo (`useLmpDetail`) e mescla fluxo nos eventos para badges na timeline.

---

## GET /engineering/lmps/dashboard/items

### Query parameters

| Parâmetro | Tipo | Default | Descrição |
|-----------|------|---------|-----------|
| `date_start` | string | — | Início do período |
| `date_end` | string | — | Fim do período |
| `branch` | string | — | Filial (`01`, `02`) |
| `listing_type` | string | — | `Todos`, `LMP`, `Amostra`, `Outro` |
| `status` | string | `Todos` | Classificação (`Pontual`, `Atrasado`, …) |
| `page` | int | `1` | Paginação |
| `page_size` | int | `50` | Tamanho da página (máx. 500) |

---

## GET /engineering/lmps/{sale_number}

Detalhe de uma OV/proposta — **sem histórico** (performance).

| Parâmetro | Descrição |
|-----------|-----------|
| `sale_number` | Path — número da proposta/OV |
| `date_start`, `date_end` | Opcional — mesmo escopo de período do dashboard |
| `branch` | Opcional — filial (`01`/`02`) |

### Resposta `data` (campos principais)

Campos de `LmpItem` + classificação calculada (`nivel`, `dias_uteis_sla`, `data_limite`, `lead_time_util`, `status`, `sla_minutos`) + `list_products[]` + **`list_history: []`**.

---

## GET /engineering/lmps/{sale_number}/history/events

Eventos AIJ010 para timeline/tabela. Query lite (sem LEAD/LAG por linha).

Mesmos query params do detalhe + opcional `revision`.

### Resposta `data`

| Campo | Descrição |
|-------|-----------|
| `sale_number`, `branch` | Identificação |
| `reference_revision`, `panel_start_date` | Contexto do painel (escopo de filtros na UI) |
| `items[]` | Eventos enriquecidos (`LmpHistoryEvent`) |
| `total` | Quantidade de itens |

### `items[]` — evento `LmpHistoryEvent`

| Campo | Descrição |
|-------|-----------|
| `revision`, `process_code`, `stage_code` | Chaves do AIJ010 |
| `process_label`, `stage_label` | Rótulos PT (AC1010/AC2010; fallback estático) |
| `start_date`, `start_time`, `limit_date`, `limit_time`, `end_date`, `end_time` | Datas/horas TOTVS (`YYYYMMDD`, `HH:MM`) |
| `duration_minutes` | Minutos calculados no SQL |
| `duration_display` | Texto legível (ex.: `Em andamento · 12 dia(s)`) |
| `status` | Código `AIJ_STATUS` |
| `status_label` | Rótulo (`Em andamento`, `Encerrado`, …) |
| `history_flag` | `AIJ_HISTOR` |
| `is_engineering` | Métrica SQL (par processo+estágio configurado) |
| `is_engineering_flow` | Exibição badge Engenharia (inclui estágios técnicos) |
| `is_open`, `is_late`, `is_current` | Flags derivadas em `GetLmpHistoryEventsUseCase` |

Enriquecimento: `api-delpi/app/domain/services/lmp_history_event_enrichment.py`.

---

## GET /engineering/lmps/{sale_number}/history/flow

Somente eventos de engenharia com contexto anterior/próximo (LEAD/LAG) para idas, voltas e avanços.

Resposta no mesmo formato de `/history/events`. Campos adicionais por item:

| Campo | Descrição |
|-------|-----------|
| `is_engineering_entry` | Primeira entrada na engenharia na sequência |
| `flow_transition` | `advanced_from_engineering`, `returned_from_engineering`, … |
| `flow_transition_label`, `flow_transition_labels` | Rótulos PT para badges na timeline |

Enriquecimento: `api-delpi/app/domain/services/lmp_history_flow_transition.py`. O MFE mescla estes campos nos eventos via `mergeHistoryFlowIntoEvents()`.

### UI do histórico (MFE)

- Toggle **Linha do tempo** (padrão) / **Tabela** — preferência salva em `localStorage`
- Filtros client-side: Todos, Engenharia, Em aberto, Revisão atual
- Mini-Gantt por evento + **visão global** na timeline
- Filtros do dashboard sincronizados na URL
- Tooltips em ações, paginação, colunas e nós da BOM (`title` nativo)
- Impressão básica via `@media print`

### `meta.relatedRoutes`

| Chave | Destino |
|-------|---------|
| `detail` | Esta OV |
| `historyEvents` | `/engineering/lmps/{sale_number}/history/events` |
| `historyFlow` | `/engineering/lmps/{sale_number}/history/flow` |
| `dashboardItems` | `/engineering/lmps/dashboard/items` |
| `dashboardSummary` | `/engineering/lmps/dashboard/summary` |
| `dashboardCharts` | `/engineering/lmps/dashboard/charts` |
| `list` | `/engineering/lmps` |

---

## Item `LmpDashboardItem` (tabela)

| Campo | Descrição |
|-------|-----------|
| `branch` | Filial |
| `sale_number` | Nº da proposta/ordem |
| `sale_description` | Descrição |
| `listing_kind` | `LMP` \| `AMOSTRA` \| `OUTRO` |
| `start_date`, `end_date` | Datas (`YYYYMMDD`). Com filtro de período, `start_date` é o **início do ciclo âncora** no painel (`ANCHOR_START_DATE`), não a primeira entrada histórica na engenharia. `lead_time_util` = dias úteis entre essas duas datas. |
| `engineering_status` | Status na engenharia |
| `qtd_pi` | Quantidade PI |
| `nivel` | `Nível 1` \| `Nível 2` \| `Nível 3` |
| `dias_uteis_sla` | Dias úteis de SLA |
| `data_limite` | Data limite (`YYYYMMDD`) |
| `lead_time_util` | Lead time útil (dias) |
| `status` | `Pontual` \| `Atrasado` \| `Andamento` \| `Retornada` |

Tipos TypeScript: `src/types/lmp.ts`.

---

## Exemplos de URL completas

```text
GET /apps/api-delpi/engineering/lmps/dashboard/items?date_start=20260501&date_end=20260531&status=Todos
GET /apps/api-delpi/engineering/lmps/003578?date_start=20260501&date_end=20260531&branch=01
GET /apps/api-delpi/engineering/lmps?date_start=2026-01-01&page=1&page_size=20
```

---

## Implementação de referência

- Helpers HTTP (sem duplicar DTO): `api-delpi/app/interface/http/routes/engineering/lmp_route_helpers.py`
- Use cases: `api-delpi/app/composition/engineering_composer.py`
- DTOs: `api-delpi/app/application/dto/lmp/`
- Doc API: `api-delpi/docs/api/06-modulos-departamentais.md` (Engenharia — LMP)
