# MyWEG → Demanda PCP — Etapa 3 (integração)

> **TASK_ID:** `PCP-DEMAND-MYWEG-E3-INTEGRATION`  
> **Status:** integrado em `GET /demand` + UI · consolidação oficial **bloqueada** (ADR)  
> **Owner:** `production-control-api` + `plugins/production-control`  
> **EXISTING_EQUIVALENT:** `YES` · **REUSE_DECISION:** `EXTEND`

## Contrato HTTP

`GET /demand` (compatível):

| Query | Default | Notas |
|---|---|---|
| `origin` | `protheus` | `protheus` \| `myweg` \| `both` |
| demais | iguais à Demanda atual | search inclui código/loja/origem |

Sem `origin` → comportamento anterior (carteira Protheus + OP).

Resposta aditiva: `source`/`planning` por item; `filters.origin`; `summary.official_aggregate` / `by_origin`; `horizon.open_quantity_*`; bloco `myweg` (batch, ADR, OP status).

## Regras

- Filial `02` + `myweg-needs.view` para `myweg`/`both`.
- MyWEG = última coleta aceita · cliente `000001`/`09` · UN→MI ÷1000.
- Pool único estoque; Linhares Protheus aberto → overlap (não soma).
- OP MyWEG: `OP_UNIT_UNVERIFIED` (somente estoque).
- `summary.official_aggregate=false` em myweg/both; banner na UI.
- Em `origin=both`, falha MyWEG **degrada** para Protheus (`myweg_degraded`) — não derruba a tela.
- Necessidade MyWEG sem SB2 consultável **permanece** na tabela (estoque 0 / descoberta), sem omitir volume.
- Cache por `filial|origem` reutilizado entre filtros/páginas (TTL Demanda).

## UI

Filtro Origem (filial 02), badge, KPI planejado MyWEG, gráfico empilhado por origem, última coleta, Ajuda (`helpTooltips.demand`).

## Pendências

1. ADR consolidação ACCEPTED.
2. Unidade da OP comprovada.
3. Validação funcional final pelo Product Master.
