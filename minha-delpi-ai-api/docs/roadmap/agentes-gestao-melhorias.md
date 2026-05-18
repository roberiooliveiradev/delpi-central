# Gestão de agentes — melhorias

**Status:** onda 1 implementada (maio/2026)

## Onda 1 — edição confiável

| # | Entrega | Status |
|---|---------|--------|
| 1.1 | `GET /chat/agents/{agentId}` com `system_prompt` para owner/editor | Concluído |
| 1.2 | PATCH com `maxToolCalls` e `requiresConfirmationForWrite` | Concluído |
| 1.3 | Builder carrega detalhes via GET (instruções, limites) | Concluído |
| 1.4 | Toggle agente ativo + compartilhamento no builder (owner) | Concluído |
| 1.5 | Lista com badges de papel e inativo | Concluído |

## Onda 2 — planejada

| # | Entrega |
|---|---------|
| 2.1 | `GET/DELETE /chat/agents/{id}/shares` — listar e revogar acessos |
| 2.2 | Busca de usuário para compartilhar (em vez de UUID manual) |
| 2.3 | Preview real do agente (`POST /admin/agent/simulate` no builder) |
| 2.4 | Especialização RAG acessível do builder para admins |
| 2.5 | Listar agentes desativados para gestores (`?includeDisabled=true`) |
| 2.6 | Tratar colisão de `key` com HTTP 409 |
