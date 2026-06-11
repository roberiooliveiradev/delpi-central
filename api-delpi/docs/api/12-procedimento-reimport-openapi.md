# 12 — Reimport OpenAPI no chat após mudanças na api-delpi

Execute sempre que alterar rotas, `operationId`, `summary` ou schemas em `api-delpi`.

## 1. Deploy da api-delpi

Subir o container/serviço com a versão nova da API.

## 2. Reimport no provider (minha-delpi-ai-api)

**Job pós-deploy (recomendado em homolog/prod):**

```bash
# Na máquina com Docker Compose (gateway local ou BASE_URL público)
./scripts/homologacao/sync-api-delpi-openapi.sh

# Homolog/prod com URL pública
BASE_URL=https://homolog.exemplo.com ./scripts/homologacao/sync-api-delpi-openapi.sh
```

O script aguarda `GET /apps/api-delpi/health`, executa o sync no container `delpi-minha-delpi-ai-api` e valida o JSON de saída (exit ≠ 0 em falha).

**GitHub Actions (manual):** workflow `sync-api-delpi-openapi` (`workflow_dispatch`) — requer secrets `DEPLOY_SSH_*` e variável `DEPLOY_BASE_URL` no Environment `homolog` ou `prod`.

**Via admin UI:** agente → provider `api-delpi` → importar schema.

**Via script (container, manual):**

```bash
docker exec delpi-minha-delpi-ai-api python3 scripts/sync_api_delpi_openapi.py
```

Com arquivo exportado:

```bash
docker exec delpi-minha-delpi-ai-api python3 scripts/sync_api_delpi_openapi.py --from-file /tmp/openapi.json
```

O script atualiza o schema do provider, reindexa embeddings das actions e regenera  
`minha-delpi-ai-api/docs/knowledge/_generated/api-delpi-openapi-catalog.md`.

## 3. Reindex RAG (opcional mas recomendado)

Reindexar na base de conhecimento do agente o documento:

`minha-delpi-ai-api/docs/knowledge/api-delpi-rotas-agente.md`

## 4. Smoke (pós-padronização envelope + meta)

### API

- `GET /apps/api-delpi/openapi.json` contém `operationId` esperados.
- `GET /apps/api-delpi/financial/rol` retorna `meta.operationId`, `meta.shape` e `data` inalterado.
- `pytest api-delpi/tests/test_envelope_consumer_compat.py` passa no container.

### Chat (minha-delpi-ai-api)

```bash
docker exec delpi-minha-delpi-ai-api pytest \
  tests/unit/domain/services/test_external_action_result_presenter_api_delpi_profiles.py \
  tests/unit/application/use_cases/test_execute_external_action_api_delpi_meta.py -q
```

- Turno real: «Qual o estoque do 90269001?» — tabela de estoque; metadata com `apiDelpiResponseMeta`.

### Plugins MFE (leem `response.data`; `meta` é opcional)

| Plugin | Smoke manual |
|--------|----------------|
| `dashboard-financial` | KPI ROL carrega |
| `dashboard-supplies` | CPV / OTD |
| `dashboard-lmps` | Dashboard summary |
| `dashboard-delpi` | Busca de produtos |
| `central-agendamento` | Lista recursos |
| `auditoria-5s` | Lista áreas |

Build rápido (opcional):

```bash
cd plugins/dashboard-lmps && npm run build
cd plugins/dashboard-supplies && npm run build
```

Tipos TS: `shared/api-delpi-envelope/types.ts` (espelhado em `plugins/*/src/types/api.ts`).

Relacionado: [Playbook 10 — contrato de respostas](../../../minha-delpi-ai-api/docs/roadmap/playbook-10-contrato-respostas-api-delpi.md).
