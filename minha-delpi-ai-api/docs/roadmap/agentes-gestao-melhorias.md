# Gestão de agentes — melhorias

**Status:** ondas 1–7 implementadas (maio/2026)

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
| 2.2 | Busca de usuário para compartilhar (em vez de UUID manual) | Movido para Onda 3 |
| 2.3 | Preview real (`POST /chat/agents/{id}/preview`) no builder | Concluído |
| 2.4 | Especialização RAG acessível do builder (admin, aba Agentes) | Concluído |
| 2.5 | Listar agentes desativados (`?includeDisabled=true`) | Concluído |
| 2.6 | Colisão de `key` com HTTP 409 | Concluído |

## Onda 3 — colaboração e produtividade

| # | Entrega | Status |
|---|---------|--------|
| 3.1 | Busca de usuários (`GET /chat/users/search` → core-api `/me/directory/users`) | Concluído |
| 3.2 | Compartilhar com autocomplete no builder (sem UUID manual) | Concluído |
| 3.3 | Duplicar agente (`POST /chat/agents/{id}/duplicate`) | Concluído |
| 3.4 | Mensagem amigável para colisão de `key` na criação | Concluído |

## Onda 4 — compartilhamento unificado

| # | Entrega | Status |
|---|---------|--------|
| 4.1 | Lookup de usuários (`POST /me/directory/users/lookup`) e nomes na lista de shares | Concluído |
| 4.2 | `GET/DELETE /chat/projects/{id}/shares` | Concluído |
| 4.3 | Compartilhamento de projeto nas configurações + busca de usuário | Concluído |
| 4.4 | Aba Actions: feedback de sucesso e navegação mais clara | Concluído |

## Onda 5 — uso e duplicação avançada

| # | Entrega | Status |
|---|---------|--------|
| 5.1 | `GET /chat/agents/{id}/stats?hours=168` — sessões/mensagens no período | Concluído |
| 5.2 | Duplicar com `copyActions` (providers/actions) | Concluído |
| 5.3 | Builder: painel de estatísticas e opção ao duplicar | Concluído |

## Onda 6 — governança e visibilidade

| # | Entrega | Status |
|---|---------|--------|
| 6.1 | `GET /chat/agents?includeStats=true` — resumo de uso na listagem | Concluído |
| 6.2 | `POST /chat/agents/{id}/transfer` — transferir propriedade | Concluído |
| 6.3 | Duplicar com `copySources` (fontes de conhecimento do agente) | Concluído |
| 6.4 | Builder: editar papel de shares, transferir dono, métricas na lista | Concluído |

## Onda 7 — portabilidade e admin

| # | Entrega | Status |
|---|---------|--------|
| 7.1 | `GET /chat/agents/{id}/export` — JSON portável (sem segredos) | Concluído |
| 7.2 | `POST /chat/agents/import` — criar agente a partir do export | Concluído |
| 7.3 | Builder: exportar/importar JSON | Concluído |
| 7.4 | Admin Agentes: painel de estatísticas de uso | Concluído |
