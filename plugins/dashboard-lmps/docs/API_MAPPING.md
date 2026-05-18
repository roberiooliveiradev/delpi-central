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
**Envelope:** `{ "success": true, "message": "...", "data": { ... } }`

Router backend: `api-delpi/app/interface/http/routes/engineering/engineering_router.py`

---

## Endpoints consumidos pelo plugin

| Função (`lmpApi.ts`) | Método | Rota | Uso na UI |
|----------------------|--------|------|-----------|
| `getLmpsDashboard` | GET | `/engineering/lmps/dashboard` | Tela principal (KPIs, gráficos, tabela) |
| `listLmps` | GET | `/engineering/lmps` | Disponível no cliente; não usado na página atual |

---

## GET /engineering/lmps/dashboard

### Query parameters

| Parâmetro | Tipo | Default | Descrição |
|-----------|------|---------|-----------|
| `date_start` | string | — | Início do período (formato aceito pelo backend) |
| `date_end` | string | — | Fim do período |
| `branch` | string | — | Filial (ex.: `01`, `02`) |
| `status` | string | `Todos` | Filtro de classificação |
| `page` | int | — | Paginação (opcional) |
| `page_size` | int | — | Tamanho da página (opcional) |

### Resposta `data` (resumo)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `items` | `LmpDashboardItem[]` | Linhas da tabela |
| `total` | number | Total de registros |
| `page`, `page_size` | number | Paginação |
| `summary.total_lmps` | number | Total de propostas |
| `summary.percent_dentro_prazo` | number | % dentro do prazo |
| `summary.avg_lead_time` | number | Lead time médio útil (dias) |
| `charts.levelData` | `{ name, value }[]` | Pizza por nível |
| `charts.statusData` | `{ name, value }[]` | Pizza por status |
| `charts.leadByLevel` | `{ nivel, valor }[]` | Barras — média lead por nível |
| `charts.evolutionData` | `{ periodo, mediaLead, propostas }[]` | Linha — evolução temporal |

### Item `LmpDashboardItem` (campos principais)

| Campo | Descrição |
|-------|-----------|
| `branch` | Filial |
| `sale_number` | Nº da proposta/ordem |
| `sale_description` | Descrição |
| `start_date`, `end_date` | Datas (`YYYYMMDD`) |
| `engineering_status` | Status na engenharia |
| `qtd_pi` | Quantidade PI |
| `nivel` | `Nível 1` \| `Nível 2` \| `Nível 3` |
| `dias_uteis_sla` | Dias úteis de SLA |
| `data_limite` | Data limite (`YYYYMMDD`) |
| `lead_time_util` | Lead time útil (dias) |
| `status` | `Pontual` \| `Atrasado` \| `Andamento` \| `Retornada` |

Tipos TypeScript: `src/types/lmp.ts`.

---

## GET /engineering/lmps

Listagem paginada de LMPs (sem agregados de dashboard).

| Query | Descrição |
|-------|-----------|
| `date_start`, `date_end`, `branch` | Filtros de período/filial |
| `page`, `page_size` | Paginação |

Retorno: `Page<LmpItem>` em `data`.

---

## Exemplos de URL completas

```text
GET /apps/api-delpi/engineering/lmps/dashboard?date_start=2025-01-01&date_end=2026-05-18&status=Todos
GET /apps/api-delpi/engineering/lmps/dashboard?branch=01&status=Pontual
GET /apps/api-delpi/engineering/lmps?date_start=2026-01-01&page=1&page_size=20
```

---

## Não consumir neste plugin

| Rota | Motivo |
|------|--------|
| `GET /engineering/lmps/{sale_number}` | Sem tela de detalhe |
| `GET /engineering/transforma-mais/*` | Outro produto / futuro MFE |

---

## Implementação de referência

- Use cases: `api-delpi/app/composition/engineering_composer.py`
- DTOs: `api-delpi/app/application/dto/lmp/`
