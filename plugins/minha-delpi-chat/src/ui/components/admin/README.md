# Admin Minha DELPI Chat

A área admin é organizada por ambientes isolados. Cada aba ou bloco complexo deve ficar em sua própria pasta, com componente e CSS próprios.

## Estrutura

- `shell/`: topbar, abas e alertas do admin.
- `metrics/` e `metrics-tab/`: resumo operacional e métricas avançadas (janela, custo, série).
- `knowledge/`: base global de conhecimento e pré-visualização de pipeline.
- `guidelines/`: diretrizes globais de comportamento.
- `skills/`: catálogo global de skills (CRUD, policy Markdown).
- `shared/`: formulários e checkboxes alinhados (`AdminFormCheckbox`, `admin-shared.css`).
- `simulate/`: simulação do agente (sessão, sandbox, LLM).
- `evaluations/`: avaliação de respostas e sugestões.
- `agents/`: especialização por agente.
- `security/`: segurança operacional de entrada.
- `tools/`: provider LLM, actions e health (`GET /admin/tools/health`).
- `audit/`: auditoria, timeline, export CSV, trace id.
- `rbac/`: resumo de permissões do admin.

Notificações de plataforma ficam no **Portal** (`/admin` → aba Notificações), não neste plugin.

## Regras

1. Não colocar CSS de aba dentro de `ChatAdminPage.css`.
2. Não usar seletores genéricos compartilhados entre abas quando o componente for isolado.
3. Toda aba deve expor componentes menores para formulário, lista, tabela, filtros e ações.
4. Contratos administrativos ficam centralizados em `data/api/adminApi.ts` e `adminTypes.ts`.
5. Endpoints documentados em `minha-delpi-ai-api/docs/api/08-admin.md`.
6. A base de conhecimento do admin representa contexto global do chat; anexos de conversa não pertencem a essa tela.
