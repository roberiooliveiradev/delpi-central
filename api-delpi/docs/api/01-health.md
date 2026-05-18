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

## Indicadores Estratégicos

Health do módulo SI: `GET /apps/strategic-indicators-api/health` — ver [05-indicadores-estrategicos.md](./05-indicadores-estrategicos.md).
