# Admin Minha DELPI Chat

A área admin é organizada por ambientes isolados. Cada aba ou bloco complexo deve ficar em sua própria pasta, com componente e CSS próprios.

## Estrutura

- `shell/`: topbar, 6 seções, sub-abas, status strip e alertas.
- `overview/`: painel inicial (KPIs, RBAC, navegação rápida).
- `metrics/` e `metrics-tab/`: resumo operacional e métricas avançadas (janela, custo, série).
- `knowledge/`: base global de conhecimento e pré-visualização de pipeline.
- `guidelines/`: diretrizes globais de comportamento.
- `skills/`: catálogo global de comportamentos/skills (CRUD, policy Markdown) — sub-aba Conhecimento.
- `shared/`: formulários, `admin-shared.css`, `admin-workspace-theme.css`, **`admin-design-system.css`** e **`admin-primitives.css`**; primitivos `AdminTabHeader`, `AdminSummaryStrip`, `AdminMetricSection`, `AdminKpiCard`, `AdminRankedList`, `AdminDataTable`.
- `simulate/`: simulação do agente (sessão, sandbox, LLM).
- `evaluations/`: avaliação de respostas e sugestões.
- `agents/`: especialização por agente (`agentDisplay`, `AgentMiniDashboard` com `AdminKpiGrid` + `ChatRichDashboard variant="admin"`).
- `security/`: segurança operacional de entrada.
- `tools/`: provider LLM, actions e health (`GET /admin/tools/health`).
- `audit/`: auditoria, timeline, export CSV, trace id.
- `rbac/`: resumo de permissões do admin.

Notificações de plataforma ficam no **Portal** (`/admin` → aba Notificações), não neste plugin.

## Roadmap de UI

- Navegação (6 seções): `minha-delpi-ai-api/docs/roadmap/melhorias/playbooks_melhoria_minha_delpi_chat/11_admin_ux_reorganizacao_abas.md`
- Componentes e layout (primitivos, métricas, tabelas): `12_admin_ui_refatoracao_componentes.md` (mesma pasta)

## Regras

1. Não colocar CSS de aba dentro de `ChatAdminPage.css`.
2. Não usar seletores genéricos compartilhados entre abas quando o componente for isolado.
3. Toda aba deve expor componentes menores para formulário, lista, tabela, filtros e ações.
4. Contratos administrativos ficam centralizados em `data/api/adminApi.ts` e `adminTypes.ts`.
5. Endpoints documentados em `minha-delpi-ai-api/docs/api/08-admin.md`.
6. A base de conhecimento do admin representa contexto global do chat; anexos de conversa não pertencem a essa tela.
