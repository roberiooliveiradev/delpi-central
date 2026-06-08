# 12 — Reimport OpenAPI no chat após mudanças na api-delpi

Execute sempre que alterar rotas, `operationId`, `summary` ou schemas em `api-delpi`.

## 1. Deploy da api-delpi

Subir o container/serviço com a versão nova da API.

## 2. Reimport no provider (minha-delpi-ai-api)

**Via admin UI:** agente → provider `api-delpi` → importar schema.

**Via script (container):**

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

## 4. Smoke

- `GET /apps/api-delpi/openapi.json` contém `operationId` esperados.
- Turno de chat com action de produto (estoque / estrutura) responde igual ou melhor.
- Plugins MFE: leitura de `response.data` inalterada.

Relacionado: [Playbook 10 — contrato de respostas](../../../minha-delpi-ai-api/docs/roadmap/playbook-10-contrato-respostas-api-delpi.md).
