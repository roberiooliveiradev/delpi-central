# Projetos colaborativos — implementação futura

> **Status:** desabilitado (jun/2026)  
> **Flag:** `app/domain/features/chat_project_collaboration.py` → `PROJECT_COLLABORATION_ENABLED = False`

## Escopo adiado

Funcionalidades **não expostas** na UI e **bloqueadas** na API enquanto a flag estiver `False`:

| Recurso | Frontend | API |
|---------|----------|-----|
| Compartilhar projeto com outro usuário (viewer/editor) | Removido do modal de configurações | `POST/GET/DELETE …/projects/{id}/share(s)` → **501** |
| Contexto entre conversas do mesmo projeto (`shareConversationContext`) | Removido do modal de configurações | Ignorado no PATCH; pipeline trata como desligado |
| Projetos visíveis só por compartilhamento | Não listados | `list_accessible` não inclui `ai_chat_project_shares` |

## O que permanece

- Projetos **privados do proprietário** (criar, renomear, ícone, instruções, fontes, conversas).
- Projetos com `visibility: public` (acesso leitura conforme regras atuais).
- Compartilhamento de **agentes** (fluxo separado no builder de agentes).

## Reativar (checklist)

1. Definir `PROJECT_COLLABORATION_ENABLED = True` em `chat_project_collaboration.py`.
2. Restaurar seções no `ChatProjectSettingsModal` (compartilhamento + contexto entre conversas).
3. Revisar testes em `tests/unit/domain/features/test_chat_project_collaboration.py`.
4. Atualizar `docs/api/05-projetos-fontes-anexos-artefatos.md` (rotas de share deixam de retornar 501).
5. Validar RBAC, busca de usuário (`ChatUserSearchField`) e papéis viewer/editor na listagem de projetos.

## Referências

- Rotas HTTP: `app/interfaces/http/routes/chat/project_routes.py`
- Repositório: `PostgresChatProjectRepository.list_accessible` / `_can_access`
- Metadata: `ChatProjectSettingsService` (`shareConversationContext`)
- Pipeline RAG/memória: `ChatProjectConversationContextService`, `ChatKnowledgeScopeService`
