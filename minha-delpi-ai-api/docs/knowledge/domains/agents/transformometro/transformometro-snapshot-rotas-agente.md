# Transformômetro — Guia de rotas snapshot para agentes

**Uso:** anexar à base de conhecimento / RAG do agente Transformômetro ou colar trechos no `system_prompt`.

**Provider:** `transformometro-api` · **Base:** `/apps/transformometro-api` · **OpenAPI (chat):** `transformometro-api/docs/openapi-snapshot-chat.json`

Após mudanças nas rotas snapshot, rode `scripts/sync_transformometro_openapi.py` e reindexe este documento.

---

## Regras gerais

1. Para KPIs de economia, ROI e ranking de processos, use **`execute_external_action`** nas rotas **`/dashboard/snapshot/*`** — leitura rápida sobre o cache `dashboard_calculos`.
2. O cache é atualizado automaticamente após CRUD (`TM_DASHBOARD_AUTO_RECALC=true`) e manualmente via `POST /dashboard/recalcular`.
3. Se `GET /dashboard/snapshot/meta` retornar `row_count=0`, informe que o cache ainda não foi populado e sugira recálculo administrativo.
4. **Não confunda** snapshot (cache materializado) com `GET /dashboard/resumo` (cálculo live). Para o chat analítico, **prefira snapshot**.
5. Competências usam formato **`YYYY-MM`**. Filiais válidas: `01`, `02`.

---

## Mapa rápido: intenção → rota

| O usuário quer | Rota | operationId |
|----------------|------|-------------|
| Ver se o cache está atualizado / quantas linhas existem | `GET /transformometro/dashboard/snapshot/meta` | `get_dashboard_snapshot_meta` |
| KPIs totais (economia líquida, bruta, investimento, horas) | `GET /transformometro/dashboard/snapshot/resumo` | `get_dashboard_snapshot_resumo` |
| Ranking / lista de processos por mês | `GET /transformometro/dashboard/snapshot/processos` | `get_dashboard_snapshot_processos` |
| Detalhe por revisão (breakdown fino) | `GET /transformometro/dashboard/snapshot/linhas` | `get_dashboard_snapshot_linhas` |

---

## Parâmetros comuns

| Parâmetro | Descrição |
|-----------|-----------|
| `filial_id` | `01` ou `02` |
| `setor_id` | Setor cadastral do processo |
| `familia_processo` | Família/agrupamento de processos |
| `processo_id` | UUID do processo |
| `revisao_id` | UUID da revisão (somente em `/snapshot/linhas`) |
| `competencia_inicio` / `competencia_fim` | Intervalo mensal `YYYY-MM` |
| `limit` | Máximo de linhas (processos: 200 default; linhas: 500 default) |

---

## Exemplos de frases → rota

- «Qual a economia líquida total da filial 01 em 2025?» → `get_dashboard_snapshot_resumo` (`filial_id=01`, `competencia_inicio=2025-01`, `competencia_fim=2025-12`)
- «Quais processos mais economizaram em junho/2025?» → `get_dashboard_snapshot_processos` (`competencia_inicio=2025-06`, `competencia_fim=2025-06`, ordenar por `economia_liquida_mes` na resposta)
- «Detalhe mensal do processo X» → `get_dashboard_snapshot_processos` com `processo_id` ou filtrar por `codigo_processo` nos items
- «Quanto cada revisão contribuiu no mês?» → `get_dashboard_snapshot_linhas` com `processo_id` e competência
- «O dashboard está calculado?» → `get_dashboard_snapshot_meta`

---

## Campos úteis na resposta

### `/snapshot/processos` (view `processo_competencia_snapshot`)

- `codigo_processo`, `nome_processo`, `competencia`
- `economia_bruta`, `economia_liquida_mes`
- `investimento_total_mes`, `horas_economizadas_mes`
- `calculated_at` — freshness da linha

### `/snapshot/resumo`

- `summary.economia_liquida_total`, `summary.economia_bruta_total`
- `summary.investimento_total`, `summary.horas_economizadas_total`
- `meta.latest_calculated_at`

---

## Cadastro do provider (uma vez)

Na UI **Actions do agente** ou via API `POST /chat/agents/{id}/providers/create`:

```json
{
  "providerKey": "transformometro-api",
  "name": "Transformômetro API",
  "type": "openapi",
  "baseUrl": "https://www.minhadelpi.com.br/apps/transformometro-api",
  "authMode": "user_token",
  "allowRead": true,
  "allowWrite": false,
  "allowAdmin": false,
  "schema": "<conteúdo de transformometro-api/docs/openapi-snapshot-chat.json>"
}
```

Depois:

```bash
docker exec delpi-minha-delpi-ai-api python scripts/sync_transformometro_openapi.py
```
