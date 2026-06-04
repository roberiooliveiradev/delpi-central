# Playbook 12 — Admin UI: refatoração de componentes e layout

> **Status (jun/2026):** em andamento — **Fases 1–2 concluídas** no MFE (primitivos `admin/shared/`, migração dos blocos `Admin*Metrics` para `AdminMetricSection` + KPI/ranking/tabela; eyebrows internos removidos da UI). Pendente: Fase 3 (agentes/gráficos), Fase 4 (`AdminTabHeader` nas abas), baseline visual (Fase 0).  
> **Complementa:** [Playbook 11 — reorganização das abas](./11_admin_ux_reorganizacao_abas.md) (navegação 6 seções **já aplicada** no MFE). Este playbook trata **como** cada tela renderiza dados: grid, KPIs, tabelas, gráficos e estados vazios.

## Objetivo

Corrigir e padronizar a **camada visual** do painel administrativo do Minha DELPI Chat (`plugins/minha-delpi-chat`), eliminando blocos “quebrados” (HTML cru sem estilo), layouts que desperdiçam largura e inconsistência entre abas — sem alterar contratos de API nem a árvore de navegação já definida no Playbook 11.

O administrador deve conseguir, em qualquer seção:

1. Ler KPIs em **2–3 segundos** (hierarquia clara, números destacados).
2. Comparar rankings e tabelas **sem adivinhar colunas**.
3. Usar gráficos e filtros **sem sobreposição** em desktop e tablet.
4. Identificar agentes e janelas temporais **por rótulo humano**, não por UUID técnico na UI principal.

---

## Escopo

| Incluído | Excluído |
|----------|----------|
| Componentes React + CSS em `src/ui/components/admin/**` | Reorganizar de novo as 6 abas (já feito) |
| `admin-design-system.css`, `admin-shared.css`, tokens `--mdc-*` | Mudanças de backend / novos endpoints |
| `AgentMiniDashboard` + `ChatRichDashboard` no contexto admin | Absorver `ChatAgentBuilderPage` no admin |
| Blocos em `AdminMetricsTab` e subcomponentes `Admin*Metrics.tsx` | Redesign completo do Portal ou Strategic Indicators |
| Shell (`AdminShellTopbar`, sub-abas, status strip) | |

---

## Diagnóstico (evidência: telas atuais + código)

### Sintomas visíveis (capturas jun/2026)

| Área | Sintoma | Impacto |
|------|---------|---------|
| **Qualidade → Métricas → Roteamento** | Lista “Por intenção” sem separação valor/contagem; tabela “Recentes” sem borda/alinhamento | Dados ilegíveis; parece HTML exportado |
| **Qualidade → Interatividade** | KPIs à esquerda; coluna “Mais clicados” vazia com buraco à direita | Desperdício de tela; hierarquia fraca |
| **Agentes → Uso** | Indicadores em lista vertical sem cards; gráfico com filtros minúsculos; sidebar só com UUID | UX de protótipo, não de produto |
| **Transversal** | Muito espaço vazio à direita em viewports largas | Sensação de layout “mal construído” |
| **Transversal** | Eyebrows “Playbook 07” na UI operacional | Ruído para admin que não lê roadmaps internos |

### Causas raiz no código

1. **Classes CSS inexistentes ou não importadas**  
   Vários blocos usam `mdc-admin-drawing-metrics__status-list` e `mdc-admin-drawing-metrics__recent` (tabela `<table>` nativa), mas **não há regras** em `AdminMetricsTab.css` nem em `admin-design-system.css`. O estilo existe apenas para `mdc-admin-metrics-tab__table*`, que esses componentes **não usam**.

   Arquivos afetados (amostra — padrão repetido):

   - `AdminIntentRoutingMetrics.tsx`
   - `AdminInteractivityMetrics.tsx`
   - `AdminTextTaskMetrics.tsx`, `AdminSqlAdvancedMetrics.tsx`, `AdminDocumentVisionMetrics.tsx`, …

2. **Dois dialetos de UI na mesma aba Métricas**  
   - Blocos “playbook” → `mdc-admin-drawing-metrics` + listas cruas.  
   - Blocos legados → `mdc-admin-metrics-tab__table-wrap` + tabela estilizada.  
   Resultado: mesma aba, aparência de produtos diferentes.

3. **KPI grid com colunas mínimas estreitas**  
   `admin-design-system.css` define `minmax(10.5rem, 1fr)` — em telas largas os cards **não expandem** proporcionalmente; ficam agrupados à esquerda.

4. **`ChatRichDashboard` reutilizado no admin sem variante dedicada**  
   `AgentMiniDashboard` herda toolbars e grid do chat (`mdc-rich-dashboard`). Modo `--compact` esconde controles, mas filtros (Eixo Y, Categoria, Top) continuam pequenos e o painel “Indicadores” não usa `mdc-admin-kpi-card`.

5. **Identidade de agente na lista**  
   `AdminAgentsTab` prioriza `agent.id` (UUID) na sidebar quando `label`/`name` não está em destaque — típico em ambientes de teste, inaceitável em produção.

6. **Playbook 11 entregue; polish não**  
   Navegação 6 seções (`ChatAdminPage.tsx`, `adminNavigation.ts`) está estável; o débito é **componente a componente**, não falta de abas.

---

## Princípios de refatoração

### 1. Um design system admin, não CSS por tela

Toda métrica, tabela e ranking deve consumir primitivos em `admin/shared/`:

- Tokens já existentes: `--mdc-card-bg`, `--mdc-card-border`, `--mdc-space-*`, `--mdc-radius-*`.
- Escopo: **sempre** `.mdc-admin-root` (já usado em `ChatAdminPage`).

### 2. Bloco de métrica único (`AdminMetricSection`)

Substituir o padrão espalhado `mdc-admin-drawing-metrics` por um wrapper com contrato fixo:

```tsx
<AdminMetricSection
  eyebrow="Qualidade"           // opcional; NÃO usar "Playbook NN" na UI
  title="Roteamento de intenção"
  description="…"
  windowHours={24}
  isLoading={…}
  isEmpty={…}
>
  <AdminKpiGrid>…</AdminKpiGrid>
  <AdminRankedList title="Por intenção" items={…} />
  <AdminDataTable columns={…} rows={…} />
</AdminMetricSection>
```

### 3. Layout responsivo com largura útil

| Breakpoint | Regra |
|------------|--------|
| ≥1280px | Conteúdo principal `max-width: none`; grids `auto-fit` com `minmax(12rem, 1fr)` para KPIs |
| 768–1279px | 2 colunas para rankings; tabelas em `overflow-x: auto` |
| &lt;768px | 1 coluna; sidebar de agentes vira drawer ou select |

Evitar colunas irmãs onde uma está vazia (ex.: “Mais clicados” sem dados → **ocultar coluna** ou mostrar empty state centralizado).

### 4. Rótulos para humanos

- Agentes: `label || name || id curto` na lista; UUID só em tooltip/cópia técnica.
- Métricas: português consistente (“Tarefas mistas”, não “Mixed tasks”).
- Eyebrow operacional: domínio (“Qualidade”, “Agentes”), não número de playbook.

### 5. Não duplicar lógica de dados

Refatoração **só UI**: props e hooks atuais (`adminApi`, `useChatAdmin`) permanecem; mudam marcação e classes.

### 6. Acessibilidade mínima

- Tabelas com `<thead>`, `scope="col"`, caption ou `aria-label`.
- Listas de ranking com `role="list"` e contraste label/valor.
- Estados loading: skeleton ou texto + `aria-busy`, não só “sumir” conteúdo.

---

## Inventário de componentes-alvo

### Shell (manutenção leve)

| Componente | Pasta | Ação |
|------------|-------|------|
| `AdminShellTopbar` | `shell/` | Revisar truncamento do subtítulo (revision hash) |
| `AdminSubTabNav` | `shell/` | Garantir scroll horizontal acessível em mobile |
| `AdminShellStatusStrip` | `shell/` | OK; manter alinhado ao design system |

### Conhecimento

| Componente | Problemas conhecidos | Ação |
|------------|---------------------|------|
| `AdminKnowledgeTab` | Denso; filtros curadoriais | Auditar grid de cards vs tabela |
| `AdminLearningTab` | KPI strip cresceu | Usar `AdminKpiGrid` unificado |
| `AdminGuidelinesTab` / `AdminSkillsTab` | Padrões diferentes de toolbar | Unificar `AdminTabHeader` |

### Agentes

| Componente | Problemas conhecidos | Ação |
|------------|---------------------|------|
| `AdminAgentsTab` | Split layout + UUID | `AdminEntitySidebar` + label amigável |
| `AgentMiniDashboard` | Rich dashboard compacto quebrado | Variante `variant="admin"` no rich dashboard ou KPI nativo admin |

### Qualidade (prioridade alta — capturas do usuário)

| Componente | Problemas | Ação |
|------------|-----------|------|
| `AdminMetricsTab` | Orquestra muitos sub-blocos | Container com índice/âncoras ou accordion por domínio |
| `AdminIntentRoutingMetrics` | Lista + tabela sem CSS | Migrar para `AdminRankedList` + `AdminDataTable` |
| `AdminInteractivityMetrics` | Grid 2 colunas desbalanceado | Layout condicional + ranked lists |
| Demais `Admin*Metrics.tsx` | Mesmas classes mortas | Migrar em lote na Fase 3 |

### Plataforma / Governança

| Componente | Ação |
|------------|------|
| `AdminToolsTab` | Alinhar toolbar ao `AdminTabHeader` |
| `AdminSecurityTab` / `AdminAuditTab` | Tabelas já parcialmente estilizadas — reutilizar `AdminDataTable` |

---

## Biblioteca de primitivos (novos ou consolidados)

Criar em `plugins/minha-delpi-chat/src/ui/components/admin/shared/`:

| Primitivo | Responsabilidade |
|-----------|------------------|
| `AdminTabHeader` | Título, descrição, ações (Atualizar, export), seletor de janela |
| `AdminKpiGrid` / `AdminKpiCard` | Extrair do CSS global; props: `label`, `value`, `hint`, `tone?` |
| `AdminRankedList` | Label + contagem alinhados (`space-between`), barra opcional de proporção |
| `AdminDataTable` | Wrapper `__table-wrap` + estilos unificados; colunas tipadas |
| `AdminMetricSection` | Card seção + header + estados loading/empty/error |
| `AdminSplitLayout` | Aside lista + main (agentes, auditoria) |
| `AdminEmptyState` | Ícone + texto + CTA opcional |

**CSS:** um arquivo `admin-primitives.css` importado em `ChatAdminPage.css` após `admin-design-system.css`.

**Deprecar gradualmente:** classes `mdc-admin-drawing-metrics__status-list` e `__recent` (remover após migração).

---

## Fases de implementação

### Fase 0 — Baseline e checklist (0,5–1 dia)

- [ ] Screenshots por seção/sub-aba em 1440px e 768px (tema escuro atual).
- [ ] Planilha: componente × problema × severidade (bloqueante / cosmético).
- [ ] Listar todas as ocorrências de `drawing-metrics__status-list` e `__recent` (grep).

**Entregável:** pasta `12_admin_ui_refatoracao_componentes/baseline/` com PNG + `CHECKLIST.md`.

### Fase 1 — Fundação CSS + primitivos (2–3 dias)

- [ ] `admin-primitives.css` com estilos de tabela, ranked list, metric section.
- [ ] Implementar `AdminMetricSection`, `AdminKpiGrid`, `AdminRankedList`, `AdminDataTable`.
- [ ] Ajustar `admin-design-system.css`: KPI `minmax(12rem, 1fr)`; seção métrica `width: 100%`.
- [ ] Testes de snapshot leves ou Storybook opcional (se já houver padrão no plugin).

**Critério de aceite:** Storybook ou página demo interna mostra os 4 primitivos em tema claro/escuro.

### Fase 2 — Qualidade → Métricas (3–4 dias) — **prioridade das capturas**

Migrar nesta ordem:

1. `AdminIntentRoutingMetrics` (lista + tabela — caso mais visível).
2. `AdminInteractivityMetrics` (grid desbalanceado).
3. `AdminFeedbackMetrics`, `AdminWebSearchMetrics`, … (lote com mesmo padrão).

- [ ] Remover eyebrow “Playbook NN” da UI; usar “Qualidade” ou nome do bloco.
- [ ] `AdminMetricsTab`: agrupar blocos com `<h2>` índice ou nav lateral sticky (opcional).

**Critério de aceite:** em 1440px, blocos ocupam largura útil; tabela Recentes legível; Por intenção com label e número separados.

### Fase 3 — Agentes (2–3 dias)

- [ ] Sidebar: nome amigável + badge de status; UUID em `<code>` secundário.
- [ ] `AgentMiniDashboard`: painel Indicadores via `AdminKpiGrid`; gráfico com toolbar legível (min-height 36px nos selects).
- [ ] Avaliar `variant="admin"` em `ChatRichDashboard` (CSS em `ChatRichDashboard.css` scoped sob `.mdc-admin-root`).

**Critério de aceite:** admin identifica agente sem copiar UUID; gráfico não sobrepõe KPIs em split view.

### Fase 4 — Conhecimento, Plataforma, Governança (3–5 dias)

- [ ] Unificar toolbars (`AdminTabHeader`) em Knowledge, Tools, Security, Audit.
- [ ] `LearningSummaryStrip` / strips similares → `AdminKpiGrid`.
- [ ] Auditoria: tabela e paginação no mesmo `AdminDataTable`.

### Fase 5 — Polish, i18n e QA (1–2 dias)

- [ ] Passagem de copy PT (eliminar inglês desnecessário na UI).
- [ ] `npm run build` + teste manual das 6 seções × sub-abas.
- [ ] Atualizar `plugins/minha-delpi-chat/src/ui/components/admin/README.md`.

---

## Matriz de migração (métricas → primitivo)

| Padrão atual | Substituir por |
|--------------|----------------|
| `<div className="mdc-admin-drawing-metrics__status-list"><ul>…` | `<AdminRankedList items={[{label, value}]} />` |
| `<div className="mdc-admin-drawing-metrics__recent"><table>` | `<AdminDataTable columns rows />` |
| `<div className="mdc-admin-kpi-grid">` + artigos manuais | `<AdminKpiGrid><AdminKpiCard …/></AdminKpiGrid>` |
| Header duplicado em cada `Admin*Metrics` | `<AdminMetricSection title=…>` |

---

## Relação com Playbook 11

| Playbook 11 | Playbook 12 |
|-------------|-------------|
| **Onde** clicar (6 seções, sub-abas, deep links) | **Como** cada sub-aba aparece |
| `adminNavigation.ts`, `AdminSectionNav` | `admin/shared/*`, `AdminMetricsTab/*` |
| Status: parcial / mockups | Status: proposta |

Ordem recomendada: **12 após 11 estável** — situação atual (jun/2026).

---

## Riscos e mitigação

| Risco | Mitigação |
|-------|-----------|
| Regressão visual em tema claro | Testar `.mdc-admin-root` nos dois temas do chat |
| `ChatRichDashboard` difícil de isolar | Variante admin só com CSS; não forkar lógica de gráfico |
| Escopo infinito (10+ métricas) | Fase 2 obrigatória; Fase 4 por prioridade de uso |
| Conflito com deploy MFE | Um PR por fase; feature flag CSS opcional `admin-ui-v2` |

---

## Critérios de aceite globais

1. **Zero** uso de `mdc-admin-drawing-metrics__status-list` / `__recent` sem estilo equivalente nos primitivos.
2. Nenhuma tabela de métricas admin fora de `AdminDataTable` (ou wrap documentado).
3. Em viewport ≥1280px, conteúdo principal usa **≥70%** da largura útil (sem faixa vazia >40% à direita em blocos de KPI).
4. Lista de agentes exibe **nome legível** como texto primário.
5. Build MFE verde; README admin atualizado.
6. Documentação API inalterada (`08-admin.md`).

---

## Referências no repositório

| Recurso | Caminho |
|---------|---------|
| Página admin | `plugins/minha-delpi-chat/src/ui/pages/ChatAdminPage.tsx` |
| Design system | `plugins/minha-delpi-chat/src/ui/components/admin/shared/admin-design-system.css` |
| Métricas (problema) | `plugins/minha-delpi-chat/src/ui/components/admin/metrics-tab/` |
| Mini dashboard agente | `plugins/minha-delpi-chat/src/ui/components/admin/agents/AgentMiniDashboard.tsx` |
| Rich dashboard (chat) | `plugins/minha-delpi-chat/src/ui/components/ChatRichDashboard.css` |
| Navegação 6 abas | `plugins/minha-delpi-chat/src/navigation/adminNavigation.ts` |
| Playbook navegação | [11_admin_ux_reorganizacao_abas.md](./11_admin_ux_reorganizacao_abas.md) |
| README admin | `plugins/minha-delpi-chat/src/ui/components/admin/README.md` |

---

## Resumo executivo

O painel admin **já tem a navegação certa** (6 seções), mas a **camada de apresentação** ficou pela metade: blocos de métricas de playbooks internos usam markup sem CSS, gráficos do chat foram reaproveitados sem variante admin, e grids de KPI não escalam em telas largas. Este playbook prioriza **primitivos compartilhados** e migração em 5 fases, começando por **Qualidade → Métricas** (onde as capturas mostram o pior estado) e **Agentes → Uso**.

**Próximo passo sugerido:** Fase 3 — `AdminAgentsTab` + `AgentMiniDashboard` (KPI cards admin, filtros legíveis); Fase 4 — adotar `AdminTabHeader` em Conhecimento, Aprendizagem e cabeçalhos de sub-abas; Fase 0 opcional — screenshots de baseline antes/depois.
