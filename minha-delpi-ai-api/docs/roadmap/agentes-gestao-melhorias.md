# Gestão de agentes — melhorias

**Status:** ondas 1 e 2 implementadas (maio/2026)

## Onda 1 — edição confiável

| # | Entrega | Status |
|---|---------|--------|
| 1.1 | `GET /chat/agents/{agentId}` com `system_prompt` para owner/editor | Concluído |
| 1.2 | PATCH com `maxToolCalls` e `requiresConfirmationForWrite` | Concluído |
| 1.3 | Builder carrega detalhes via GET (instruções, limites) | Concluído |
| 1.4 | Toggle agente ativo + compartilhamento no builder (owner) | Concluído |
| 1.5 | Lista com badges de papel e inativo | Concluído |

## Onda 2 — compartilhamento, preview e listagem

| # | Entrega | Status |
|---|---------|--------|
| 2.1 | `GET/DELETE /chat/agents/{id}/shares` — listar e revogar acessos | Concluído |
| 2.2 | Busca de usuário para compartilhar (em vez de UUID manual) | Pendente |
| 2.3 | Preview real (`POST /chat/agents/{id}/preview`) no builder | Concluído |
| 2.4 | Especialização RAG acessível do builder (admin, aba Agentes) | Concluído |
| 2.5 | Listar agentes desativados (`?includeDisabled=true`) | Concluído |
| 2.6 | Colisão de `key` com HTTP 409 | Concluído |
