# ADR 005 — HTTP modular com facade

**Status:** Aceito (jun/2026)

## Contexto

`chat_routes.py` (~3150 linhas) misturava sessões, mensagens, agentes, anexos e providers — difícil de revisar e testar.

## Decisão

Pacote `app/interfaces/http/routes/chat/`:

| Módulo | Responsabilidade |
|--------|------------------|
| `shared.py` / `deps.py` | Blueprint, SSE, composers |
| `session_routes`, `message_routes`, `attachment_routes`, `project_routes`, `meta_routes` | Domínios HTTP |
| `agent_routes`, `agent_provider_routes`, `agent_skill_routes` | Agentes (core / providers / skills) |
| `chat_routes.py` (raiz) | Facade que reexporta `chat_bp` |

Handlers: validar DTO → `make_*` → resposta JSON/SSE.

## Consequências

- Maior módulo HTTP: `agent_routes.py` ~548 linhas (meta < 600 por domínio).
- Teste `test_chat_routes_package.py` garante estrutura e ausência de Postgres nas rotas chat.
- Padrão replicável para outros blueprints grandes (admin por domínio, quando necessário).
