# TV Dashboard API

API dedicada do plugin **Painéis TV** — programações rotativas, slides, mídia, WebSocket e link público via `public-hub`.

Documentação completa: [`docs/12-roadmap-e-evolucao/tv-dashboard/README.md`](../docs/12-roadmap-e-evolucao/tv-dashboard/README.md)

Power Query M: a [Fase 1](../docs/12-roadmap-e-evolucao/tv-dashboard/FASE-1-STATUS-M-DELPI.md) adicionou domínio tipado, adapter v1, formatter e dual-read v1/v2. `mQuery.enabled` e `mQuery.writeV2Enabled` permanecem `false`; não existem parser, runtime ou endpoints M, e v2 retorna diagnóstico seguro sem execução.

---

## Endpoints

### Público (sem JWT)

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/public/present/{token}` | Payload completo da apresentação (+ view count) |
| `WS` | `/public/present/{token}/ws` | Push `presentation_updated` para a TV |
| `GET` | `/public/present/{token}/media/{assetId}` | Mídia de comunicado (imagem/vídeo/fonte) |
| `POST` | `/public/present/{token}/heartbeat` | Sinal «TV online» para o admin |

### Admin (JWT + RBAC)

| Grupo | Prefixo |
|---|---|
| Programações | `/playlists` |
| Telas | `/playlists/{id}/slides` |
| Histórico | `/playlists/{id}/history` — até 500 versões, detalhes e restauração atômica |
| Mídia | `/playlists/{id}/media` — `GET` lista `{ items }`, `POST` upload de imagem/vídeo/fonte, `GET /{assetId}` serve |
| Tempo real | `WS /playlists/{id}/presentation-ws?access_token=…` |
| Catálogo nativo | `/native-screens` |
| Conteúdo UI / presets | `/content/ui`, `/content/slide-presets`, `/content/branch-scope` |
| **Dados (blocos api-delpi)** | `/data` — catálogo, preview, validação |
| Dados (legado) | `/data-routes` — alias enriquecido do catálogo |

### API `/data` (admin — JWT + RBAC)

| Método | Rota | Permissão | Descrição |
|---|---|---|---|
| `GET` | `/data/routes` | `TV_READ` | Catálogo allowlist com `suggestedDisplayModes` |
| `GET` | `/data/routes/{operationId}` | `TV_READ` | Detalhe de uma rota |
| `GET` | `/data/openapi/candidates` | `TV_MANAGE` | Rotas GET da api-delpi ainda fora da allowlist (curadoria) |
| `POST` | `/data/preview-block` | `TV_READ` | Preview de bloco isolado (merge filtros + RBAC) |
| `POST` | `/data/validate-config` | `TV_READ` | Valida `native_config` antes do save |

Filtros padrão da programação: campo `dataDefaults` em `PATCH /playlists/{id}` (migration `V003__playlist_data_defaults.sql`).

### Histórico persistente

Cada mutação editorial concluída captura no PostgreSQL o estado anterior da
programação e de suas telas. São mantidas as 500 versões mais recentes por
programação; permissões, compartilhamentos, token público e métricas não fazem
parte dos snapshots. Desde a migration `V009`, cada nova versão também preserva
o nome e o e-mail do ator autenticado (`authorName` e `authorEmail`) no instante
da ação; registros anteriores permanecem com esses campos nulos.

| Método | Rota | Permissão | Descrição |
|---|---|---|---|
| `GET` | `/playlists/{id}/history?page=1&pageSize=10` | `TV_READ` | Lista versões e a revisão atual |
| `GET` | `/playlists/{id}/history/{snapshotId}` | `TV_READ` | Retorna o snapshot completo |
| `POST` | `/playlists/{id}/history/{snapshotId}/restore` | `TV_WRITE` | Restaura atomicamente, preservando UUIDs e ordem |

O restore exige `expectedRevision` no corpo. Se a programação tiver sido
alterada desde a leitura, a API retorna `409` com `currentRevision`.

Listagem e detalhe expõem `change`: a versão `R` é comparada ao snapshot
`R+1`, pois ela representa o estado anterior à mutação que produziu `R+1`. O
snapshot mais recente é comparado ao estado atual somente quando
`currentRevision = R+1`. O resumo informa campos da programação alterados,
telas adicionadas/removidas/atualizadas, reordenação e totais. Histórico legado
incompleto ou lacunas de revisão retornam `change.available = false`.

Regras: somente rotas **GET** na allowlist (`tv_data_routes.json`); gates CI:

```bash
python3 scripts/generate_tv_data_routes_from_openapi.py --check   # catálogo = gerador (OpenAPI + overlays)
python3 scripts/check_tv_data_routes.py --check                  # allowlist ⊆ OpenAPI
```

Baseline de 2026-07-16: **232 operationIds GET únicos**, preservados na Fase 1. O cache agora isola por fingerprint SHA-256 de identidade/credencial opaca, permissões e contexto de serviço, sem JWT bruto. O enforcement usa `tvConstraints.requiresBranchPermission` e aliases de filial; rotas ainda sem curadoria mantêm fallback compatível configurável.

### Catálogo a partir do OpenAPI (como o registry do chat)

Fonte de verdade: **api-delpi OpenAPI completo** → `openapi_baseline.json` (v2: `parameters` + `xDelpi`) → gerador TV.

| Artefato | Papel |
|---|---|
| `api-delpi/app/content/openapi_baseline.json` | Inventário GET + query params + `x-delpi.shape` |
| `tv-dashboard-api/.../tv_data_routes.json` | Catálogo servido ao editor (`GET /data/routes`) |
| `tv_data_route_overlays.json` | Curadoria TV (`valueFields`, `valueFieldLabels`, `tvConstraints`, labels, `whenToUse`, `paramStrategy`) |
| `api-delpi/.../tv_route_audience.json` | Audiência TV → `x-delpi.tv` no OpenAPI (gerador lê `whenToUse`/`label`/`description`) |

### Multi-métrica (escalares)

Rotas com vários `valueFields` (ex.: `get_lmps_dashboard_summary`) resolvem `resolved.kpiMetrics[]` no enrichment. O binding aceita `selectedValueFields` (lista) e `valueField` (legado, um campo). Sem seleção = todas as métricas. Views (`kpi_view` / `chart_view` / `table_view`) podem filtrar de novo no cliente sem novo fetch.

Esteira pós-deploy / após mudança de rota na api-delpi:

```bash
# 1) Baseline rico (local ou via container)
docker exec delpi-api-delpi python -c \
  "from app.main import app; import json; open('/tmp/o.json','w').write(json.dumps(app.openapi()))"
docker cp delpi-api-delpi:/tmp/o.json /tmp/openapi_full.json
cd api-delpi && .venv/bin/python scripts/sync_openapi_baseline.py --from-json /tmp/openapi_full.json

# 2) Catálogo TV
cd ..
python3 scripts/generate_tv_data_routes_from_openapi.py --write
python3 scripts/enrich_tv_data_routes_pt.py --write   # labels PT (preservados no generate)
python3 scripts/generate_tv_data_routes_from_openapi.py --check
python3 scripts/check_tv_data_routes.py --check

# 3) (chat) registry operacional — mesmo baseline
cd minha-delpi-ai-api && .venv/bin/python scripts/generate_operational_route_registry.py --write --check
```

O gerador monta `paramSchema` / `paramStrategy` (`date_range` quando há par de datas
OpenAPI — `date_start`+`date_end` ou `start_date`+`end_date`) e `dateRangeKeys` com os
nomes HTTP canônicos; overlays sobrescrevem só o que é específico do TV. Seed inicial de overlays: `--seed-overlays`.


---

## Períodos relativos e séries temporais

- `dateRangePreset` é interno ao bloco TV: o gateway o converte para as chaves de data canônicas da rota e não o envia à api-delpi.
- Presets: `today`, `this_week`, `this_month`, `this_quarter`, `this_year`, `previous_week`, `previous_month`, `previous_quarter`, `previous_year`, `last_7_days`, `last_30_days`, `last_90_days`, `last_n_days` e `custom`.
- Presets relativos são recalculados em cada fetch; `custom` mantém as datas fixas informadas.
- A granularidade definida pela rota é preservada. Uma rota com `granularity=day` retorna e apresenta um ponto por dia, sem agrupamento automático em semanas ou faixas de datas.
- Rotas com `seriesField` normalizam `points` para tabela `{ periodo, value }`, sem expor metadados internos (`granularity`, `truncated`, `sort_key`) nem duplicar `label`.
- A tabela de série consome todos os pontos retornados pela api-delpi (até 366 para um ano diário); `table_view` usa scroll interno para navegar pelas linhas.

---

## Mídia persistente

| Variável | Container | Host |
|---|---|---|
| `TV_DASHBOARD_MEDIA_UPLOAD_DIR` | `/app/data/tv-dashboard/media` | `${DELPI_DATA_HOST_DIR}/tv-dashboard/media` |

Migrations: `V002__media_assets.sql`, `V006__media_assets_font_kind.sql`

---

## WebSocket

Salas por `playlist_id`. Evento típico:

```json
{
  "type": "presentation_updated",
  "reason": "slide_updated",
  "playlistId": "…",
  "revision": "2026-07-16T12:00:00+00:00|3|2026-07-16T12:05:00+00:00"
}
```

Disparado após CRUD de slides, upload de mídia, alterações na programação e exclusão.

**Editor admin:** sincronização exclusivamente via WebSocket — `presentation_updated` após persistência na API, `slide_draft` para edição ao vivo sem esperar o autosave e `selection_update` para destacar os blocos selecionados por outros editores. A identidade e o papel publicados vêm do JWT validado no servidor; o socket público é somente leitura.

`selection_update` contém `slideId`, `selectedIds`, `clientId`, `displayName` e `updatedAt`. Seleção vazia limpa o chrome remoto; desconexão remove a seleção por meio do `presence_update`. O estado é transitório e não é persistido no slide.

**Gateway:** `proxy_pass` estático para `tv-dashboard-api:8000` (variável `$upstream` quebra upgrade WebSocket).

---

## Desenvolvimento

```bash
cd tv-dashboard-api
pip install -r requirements.txt
pip install -e ../shared[fastapi]
pytest tests/ -q
```

---

## Testes

```bash
pytest tests/ -q
# público: tests/test_public_present.py
# realtime: tests/test_presentation_realtime.py
# comunicado/mídia: tests/test_comunicado_media.py
```

---

## Container

- Compose: `tv-dashboard-api` → `delpi-tv-dashboard-api`
- Depende: `postgres-plugins`, `keycloak`, `api-delpi`
- Gateway: requer headers WebSocket (`Upgrade`, `Connection`) em `/apps/tv-dashboard-api/`
