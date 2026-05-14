# 07 — Tools internas

## POST `/tools/execute`

Executa uma tool interna registrada na aplicação.

### Permissão

`minha-delpi.chat.tools.use`

### Rate limit

Bucket `tool_calls`, configurado por `RATE_LIMIT_TOOL_CALLS_PER_WINDOW`.

### Body

```json
{
  "tool": "nome_da_tool",
  "arguments": {
    "parametro": "valor"
  }
}
```

### Validações

- `tool` é obrigatório e não pode ser vazio.
- `arguments` deve ser objeto JSON.

### Resposta `200`

```json
{
  "tool_name": "nome_da_tool",
  "ok": true,
  "result": {},
  "error": null
}
```

O formato exato depende de `ExecuteToolResult`.
