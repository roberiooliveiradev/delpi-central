# 06 — Knowledge API

Endpoints para ingestão e busca na base de conhecimento.

## POST `/knowledge/documents`

Ingere documento na base de conhecimento.

### Permissão

`minha-delpi.chat.knowledge.manage`

### Rate limit

Bucket `knowledge_writes`, configurado por `RATE_LIMIT_KNOWLEDGE_WRITES_PER_WINDOW`.

### Body

```json
{
  "title": "Visão geral da Minha DELPI",
  "sourceType": "manual",
  "sourceRef": "seed:minha-delpi-visao-geral-v2",
  "content": "Conteúdo do documento...",
  "metadata": {
    "category": "geral"
  }
}
```

### Resposta `201`

Objeto retornado pelo use case de ingestão, normalmente com IDs de documento/chunks e metadados.

---

## POST `/knowledge/search`

Busca semântica na base de conhecimento.

### Permissão

`minha-delpi.chat.access`

### Body

```json
{
  "query": "como funciona o chat?",
  "limit": 6
}
```

### Resposta `200`

Lista/estrutura retornada pelo use case de busca, contendo documentos/chunks relevantes.
