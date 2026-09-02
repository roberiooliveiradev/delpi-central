# financial-api

BFF do **Portal Financeiro**. Dono do catálogo de subplugins, do RBAC de filial, do cache e da agregação da gestão à vista. SQL TOTVS permanece na api-delpi; IDD/IGD vêm do strategic-indicators-api.

O MFE fala **apenas** com esta API (`/apps/financial-api`). SQL TOTVS permanece na api-delpi.

## Endpoints

| Método | Path | Auth |
|--------|------|------|
| GET | `/health` | público |
| GET | `/subplugins` | JWT + `financial.access` |
| GET | `/overview?branch=&startDate=&endDate=` | JWT + acesso + filial |
| GET | `/billing/dashboard?branch=&startDate=&endDate=&granularity=` | JWT + `financial.access` + filial |
| GET | `/billing/invoices?branch=&startDate=&endDate=` | JWT + `financial.export` + filial |
| GET | `/delinquency/{summary,monthly,aging,customers,titles}` | JWT + `financial.delinquency.view` + ambas as filiais |
| GET | `/cost-centers/{filters,summary,series,ranking-cost-centers,ranking-suppliers,entries}` | JWT + `financial.cost-centers.view` + filial |
| GET | `/freight/{dashboard,inconsistencies}` | JWT + `financial.freight.view` + filial |
| GET | `/indicators/department` | JWT + `financial.indicators.view` |
| GET | `/indicators/global` | JWT + `financial.indicators.view` |

Envelope `{ success, message, data }`. Campos de negócio em camelCase.

`GET /overview` agrega em paralelo ROL, EBITDA %, custo fixo %, PMR, resumo de inadimplência, top centros de custo e IDD do Financeiro. Cada bloco falha isoladamente (`blocks[].available` / `blocks[].error`) sem derrubar a tela.

`GET /billing/dashboard` agrega composição da ROL (`/financial/rol`), série e ranking de clientes (`/commercial/rol/series` e `/commercial/rol/by-customer`) e ROL por unidade (`/commercial/rol/by-branch`). Série e ranking degradam isoladamente se a api-delpi falhar; o resumo da ROL é obrigatório.

`GET /billing/invoices` lista as notas de saída (SD2) e devoluções (SD1) que entram no ROL, com os mesmos filtros de `GET /financial/rol`. Serve para extrato Excel de conferência — não são títulos SE1 de cobrança.

### Frete das compras — fórmula do rateio

`GET /freight/dashboard` consome `GET /financial/purchase-freight/links` da api-delpi (vínculos SF8010 × SF1010) e calcula o peso do frete por nota. Toda a aritmética é `Decimal` com `ROUND_HALF_UP`, porque o percentual é comparado com o limite na fronteira exata (3,25%).

```
base(CT-e)        = Σ F1_VALMERC das NFs distintas amarradas ao CT-e
rateio(NF, CT-e)  = bruto(CT-e) × mercadoria(NF) / base(CT-e)
frete(NF)         = Σ rateio(NF, CT-e) de todos os CT-es da NF
% frete(NF)       = frete(NF) / mercadoria(NF) × 100
situação          = acima do limite quando % frete > limite da filial
```

Três decisões sustentam o número:

- **Fecho da base.** A base soma **todas** as NFs do CT-e, inclusive as fora do filtro de data. Ignorá-las inflaria o rateio das notas visíveis e o percentual apareceria maior do que é. Quando isso acontece, o detalhe da nota sinaliza que a base está dividida com notas que a tela não mostra.
- **Resíduo.** O arredondamento de cada parcela deixa centavos sobrando ou faltando; o resto vai para a NF de maior mercadoria, onde tem menor peso relativo. A soma dos rateios fecha com o bruto do CT-e.
- **Inconsistência não vira zero.** Vínculo sem NF, sem CT-e, com valor não positivo, repetido, sem base ou com espécie fora do padrão sai classificado com código, fica **fora** dos totais e aparece em `/freight/inconsistencies`.

Limites por filial, data de corte (`minimumIssueDate`), espécies especiais, TTL de cache e todos os textos ficam em `financial_app/content/freight.json`. A consulta exige um intervalo completo de emissão **ou** de digitação da NF.

EBITDA %, custo fixo % e PMR vêm de **Google Sheets** na api-delpi (`/financial/ebitda_pct`, `/fixed_cost_pct`, `/pmr`). Sem as variáveis abaixo no `infra/.env` da **api-delpi**, esses blocos ficam indisponíveis (ROL e inadimplência continuam, pois leem TOTVS):

```
FINANCIAL_EBITDA_SHEET_ID / FINANCIAL_EBITDA_SHEET_GID
FINANCIAL_FIXED_COST_SHEET_ID / FINANCIAL_FIXED_COST_SHEET_GID
FINANCIAL_RECEIVABLES_SHEET_ID / FINANCIAL_RECEIVABLES_SHEET_GID
```

Depois de preencher, recreate só do `api-delpi` (não resetar schema). O Dashboard Financeiro legado usa as mesmas planilhas.

Inadimplência é consolidada na origem: o BFF exige `financial.view.filial-01` **e** `financial.view.filial-02`. Despesas por centro de custo aceitam `branch=01|02|all`; o consolidado também exige as duas filiais.

IDD/IGD: `shared/strategic_indicators_client` em `/integrations/dashboard-department-indicators?department_id=financial` e o hero do IGD. Degradação graciosa quando o SI responde `partial_success` ou fica fora do ar.

## Migrations

Schema Postgres `financial` em `postgres-plugins`. Runner por checksum (`V001__schema.sql`). Só `up` — nunca `reset` em ambiente com dados.

```bash
FIN_RUN_MIGRATIONS_ON_STARTUP=true
```

## Testes

```bash
cd financial-api
.venv/bin/python -m pytest tests -q
```

## Infra

Serviço `financial-api` nos composes (prod e dev), location `^~ /apps/financial-api/` no nginx, fase `api` dos scripts sequenciais. Env prefixo `FIN_*`. Caller S2S: `DELPI_API_CALLER_APP=financial-api`.
