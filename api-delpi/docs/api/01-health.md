# 01 — Health

Endpoints de verificação de disponibilidade. Não exigem permissão RBAC específica além da validação JWT do middleware (se configurada para a rota).

## GET /health

Health check global da API.

**Permissão:** nenhuma decorator explícita.

**Resposta `200`:**

```json
{
  "status": "online"
}
```

---

## GET /strategic-indicators/health

Health do módulo Indicadores Estratégicos.

**Resposta `200`:**

```json
{
  "status": "online",
  "module": "strategic-indicators"
}
```
