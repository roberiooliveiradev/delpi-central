# Admin Minha DELPI Chat

A área admin é organizada por ambientes isolados. Cada aba ou bloco complexo deve ficar em sua própria pasta, com componente e CSS próprios.

## Estrutura

- `shell/`: topbar, 6 seções, sub-abas, status strip e alertas.
- `overview/`: painel inicial (KPIs, RBAC, navegação rápida).
- `metrics-tab/`: resumo operacional e métricas avançadas (janela, custo, série).
- `knowledge/`: base global de conhecimento e pré-visualização de pipeline.
- `guidelines/`: diretrizes globais de comportamento.
- `skills/`: catálogo global de comportamentos/skills — sub-aba Conhecimento.
- `learning/`: aprendizagem contínua (candidatos, vocabulário, memória, regressão, ajuste fino).
- `shared/`: design system + primitivos (`AdminTabHeader`, `AdminSummaryStrip`, `AdminMetricSection`, `AdminKpiCard`, `AdminRankedList`, `AdminDataTable`, `admin-primitives.css`).
- `simulate/`: simulação do agente.
- `evaluations/`: avaliação de respostas.
- `agents/`: especialização e uso (`agentDisplay`, `AgentMiniDashboard` com `variant="admin"`).
- `security/`: segurança operacional de entrada.
- `tools/`: LLM, saúde e catálogo de ações.
- `audit/`: auditoria, timeline, exportação, trace id.
- `rbac/`: permissões do admin.

Notificações de plataforma ficam no **Portal** (`/admin` → aba Notificações), não neste plugin.

## Primitivos (Playbook 12)

| Componente | Uso |
|------------|-----|
| `AdminTabHeader` | Título + descrição + faixa KPI + ações por aba |
| `AdminSummaryStrip` | Grid de `AdminKpiCard` com `aria-label` |
| `AdminMetricSection` | Bloco de métricas em Qualidade |
| `AdminDataTable` | Tabelas (métricas, auditoria) |
| `AdminRankedList` | Rankings label/valor |

Estilos escopados em `.mdc-admin-root` (ver `ChatAdminPage.tsx`).

Todas as seções do admin usam `AdminTabHeader` no topo da sub-aba (Painel, Conhecimento, Agentes, Qualidade, Plataforma, Governança).

## Roadmap de UI

- Navegação (6 seções): [11_admin_ux_reorganizacao_abas.md](../../../minha-delpi-ai-api/docs/roadmap/melhorias/playbooks_melhoria_minha_delpi_chat/11_admin_ux_reorganizacao_abas.md)
- Componentes e layout: [12_admin_ui_refatoracao_componentes.md](../../../minha-delpi-ai-api/docs/roadmap/melhorias/playbooks_melhoria_minha_delpi_chat/12_admin_ui_refatoracao_componentes.md)
- Baseline visual: `12_admin_ui_refatoracao_componentes/baseline/`

## QA manual (smoke)

Após alterações no admin, validar em tema escuro (1440px):

| Seção | Sub-abas | Verificar |
|-------|----------|-----------|
| Painel | — | KPIs, links rápidos |
| Conhecimento | Documentos, Diretrizes, Comportamentos, Aprendizagem | `AdminTabHeader`, filtros KPI, listas |
| Agentes | Especialização, Simulação | Nome legível, badge, UUID em `<code>`, gráfico de uso |
| Qualidade | Métricas, Avaliações | Blocos `AdminMetricSection`, tabelas legíveis |
| Plataforma | Ferramentas, Inteligência | Strip de saúde, catálogo de ações |
| Governança | Segurança, Auditoria | Scan, tabela + paginação `AdminDataTable` |

Comando: `cd plugins/minha-delpi-chat && npm run build && npm test -- --run src/ui/components/admin/`

## Regras

1. Não colocar CSS de aba dentro de `ChatAdminPage.css`.
2. Preferir primitivos em `shared/` a markup legado (`mdc-admin-drawing-metrics__*`).
3. Toda aba expõe componentes menores (formulário, lista, tabela, filtros).
4. Contratos em `data/api/adminApi.ts` e `adminTypes.ts`.
5. API documentada em `minha-delpi-ai-api/docs/api/08-admin.md`.
6. Copy da UI em português; siglas técnicas (LLM, UUID, CSV) só quando inevitáveis.
