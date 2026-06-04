# Admin — shell, navegação e busca

Documentação da camada de navegação do painel administrativo do Minha DELPI Chat (MFE `plugins/minha-delpi-chat`), após a migração **admin-v3-sidebar** (jun/2026).

Complementa o [Playbook 11](../../../minha-delpi-ai-api/docs/roadmap/melhorias/playbooks_melhoria_minha_delpi_chat/11_admin_ux_reorganizacao_abas.md) (domínios e seções) e o [Playbook 12](../../../minha-delpi-ai-api/docs/roadmap/melhorias/playbooks_melhoria_minha_delpi_chat/12_admin_ui_refatoracao_componentes.md) (primitivos visuais).

---

## Layout do shell

```
┌─────────────────────────────────────────────────────────────┐
│ AdminShellTopbar — voltar · breadcrumb · atualizar          │
├──────────────┬──────────────────────────────────────────────┤
│ AdminSidebar │ Conteúdo (AdminShellStatusStrip + aba ativa) │
│ (árvore +    │                                              │
│  busca)      │                                              │
└──────────────┴──────────────────────────────────────────────┘
```

| Componente | Arquivo | Responsabilidade |
|------------|---------|------------------|
| `AdminShellTopbar` | `src/ui/components/admin/shell/AdminShellTopbar.tsx` | Uma única barra superior; breadcrumb via `getAdminNavBreadcrumb` |
| `AdminShellLayout` | `src/ui/components/admin/shell/AdminShellLayout.tsx` | Flex sidebar + main; botão **Menu do admin** em viewport &lt;1024px |
| `AdminSidebar` | `src/ui/components/admin/shell/AdminSidebar.tsx` | Busca, resultados de conteúdo, árvore expansível |
| Revisão visível | `adminShellRevision.ts` | Ex.: `admin-v3-sidebar` — confirma deploy do bundle |

**Removidos do fluxo principal:** `AdminSectionNav`, `AdminSubTabNav` (barras horizontais duplicadas).

Orquestração: `src/ui/pages/ChatAdminPage.tsx` → `navigateTo` + `buildAdminHref`.

---

## Modelo de navegação

Estado canônico (`AdminNavState`):

```ts
type AdminNavState = {
  section: AdminSection;   // overview | knowledge | agents | quality | platform | governance
  subTab?: AdminSubTab;    // ex.: documents, metrics, learning
  page?: string;           // 3º nível quando a sub-aba tem páginas internas
};
```

| Nível | Exemplo | Slug na URL |
|-------|---------|-------------|
| Seção | Conhecimento | `conhecimento` |
| Sub-aba | Aprendizagem | `aprendizagem` |
| Página | Vocabulário | `vocabulario` |

### URLs

| Rota | `AdminNavState` |
|------|-----------------|
| `/apps/minha-delpi-chat/admin` | `{ section: "overview" }` |
| `/apps/minha-delpi-chat/admin/qualidade/metricas` | `{ section: "quality", subTab: "metrics" }` |
| `/apps/minha-delpi-chat/admin/conhecimento/aprendizagem/vocabulario` | `{ section: "knowledge", subTab: "learning", page: "vocabulary" }` |
| `/apps/minha-delpi-chat/admin/agentes/especializacao/:uuid` | Rota especial `admin-agent` (fora do slug de sub-aba) |

Funções em `src/navigation/adminNavigation.ts`:

- `buildAdminHref(nav)` — monta path
- `parseAdminPathSegments(segments)` — interpreta segmentos após `/admin/`
- `normalizeAdminNav(partial)` — preenche sub-aba padrão e página padrão quando aplicável

Integração com rotas do chat: `src/navigation/chatRoutes.ts` (`kind: "admin"`).

---

## Árvore da sidebar

Construída em `src/navigation/adminNavTree.ts` a partir de `ADMIN_SECTIONS` (`adminNavigation.ts`).

```
Painel (item único)
Conhecimento ▾
  ├─ Documentos
  ├─ Diretrizes
  ├─ Comportamentos
  └─ Aprendizagem ▾
       ├─ Candidatos
       ├─ Vocabulário
       ├─ Memória
       ├─ Regressão
       └─ Ajuste fino
Agentes ▾ …
```

### Páginas aninhadas (3º nível)

Configuração em `src/navigation/adminNavPages.ts` → `ADMIN_NESTED_PAGES`.

Hoje apenas **Aprendizagem** declara páginas; novas sub-abas com abas internas seguem o mesmo padrão:

1. Entradas em `ADMIN_NESTED_PAGES` (`key`, `label`, `slug`).
2. Entradas de conteúdo em `adminNavSearchIndex.ts` (opcional, para busca).
3. Aba React recebe `page` via props (ex.: `AdminLearningTab` com `page={nav.page}`).
4. Remover controles segmentados duplicados no corpo da tela quando a sidebar for a navegação primária.

---

## Busca na sidebar

Placeholder: **Buscar seção, página ou conteúdo…**

Dois mecanismos (`src/navigation/adminNavSearch.ts`):

| Camada | Função | Comportamento |
|--------|--------|---------------|
| **Navegação** | `filterAdminNavTree` | Filtra nós da árvore; `searchText` inclui rótulos + texto do índice de conteúdo do alvo |
| **Conteúdo** | `searchAdminContentHits` | Lista blocos indexados (título, path, snippet) acima da árvore |

Índice estático: `src/navigation/adminNavSearchIndex.ts` → `ADMIN_NAV_CONTENT_INDEX`.

Cada entrada define:

- `target` — para onde navegar ao clicar
- `title` — rótulo do bloco (ex.: «Interatividade (chips)»)
- `path` — breadcrumb exibido no hit
- `searchText` — termos indexados (título, descrição, sinônimos, jargão técnico)

### Exemplos de busca

| Termo | Resultado típico |
|-------|------------------|
| `chips` | Conteúdo «Interatividade (chips)» + árvore Qualidade → Métricas |
| `rbac` | Conteúdo «Permissões administrativas» → Painel |
| `vocabulário` | Árvore Aprendizagem → Vocabulário + hits de aprendizagem |
| `injeção` | Governança → Segurança |

Ao clicar em um hit de conteúdo, a busca é limpa e `onNavigate(target)` atualiza URL e painel.

### Manutenção do índice

Ao adicionar ou renomear blocos em uma aba:

1. Incluir entrada em `ADMIN_NAV_CONTENT_INDEX` com `id` único.
2. Reutilizar `getContentSearchTextForTarget` — agrega textos por `section/subTab/page` para enriquecer a árvore automaticamente.
3. Cobrir com teste em `adminNavSearch.test.ts`.

---

## Tema claro / escuro

Tokens do admin em `.mdc-admin-root` (`admin-design-system.css`):

| Token | Uso |
|-------|-----|
| `--mdc-admin-surface` | Fundo elevado (segmentos, cards internos) |
| `--mdc-admin-surface-muted` | Fundo de KPI / listas |
| `--mdc-admin-border` | Bordas |
| `--mdc-admin-accent` / `--mdc-admin-accent-soft` | Destaque e seleção |
| `--mdc-admin-danger` / `--mdc-admin-success` | Feedback |

Evitar fallbacks `#fff` ou cores fixas em CSS de abas; herdam `--mdc-card-bg`, `--mdc-text`, etc. do tema do chat.

Classe utilitária: `.mdc-admin-segmented` para grupos de botões tipo aba (se ainda necessários no corpo da página).

---

## Testes

```bash
cd plugins/minha-delpi-chat
npm test -- --run src/navigation/
npm run build
```

| Arquivo | Cobertura |
|---------|-----------|
| `adminNavigation.test.ts` | Href, parse, slugs PT |
| `adminNavTree.test.ts` | Árvore, filtro, breadcrumb |
| `adminNavSearch.test.ts` | Hits de conteúdo |
| `adminNavPages.test.ts` | Slugs do 3º nível |

---

## QA manual (navegação)

1. Abrir `/apps/minha-delpi-chat/admin` — sidebar com Painel; topbar sem segunda barra de tabs.
2. Expandir **Conhecimento → Aprendizagem** — cinco folhas; URL com `/candidatos` por padrão.
3. Buscar `métricas` — árvore e/ou seção Conteúdo; clicar leva à tela correta.
4. Redimensionar &lt;1024px — **Menu do admin** abre/fecha sidebar.
5. Tema escuro — sem caixas brancas na barra de aprendizagem (navegação só na sidebar).

Checklist completo de abas: `src/ui/components/admin/README.md`.

---

## Referências no código

| Recurso | Caminho |
|---------|---------|
| Estado + seções | `src/navigation/adminNavigation.ts` |
| Páginas aninhadas | `src/navigation/adminNavPages.ts` |
| Árvore | `src/navigation/adminNavTree.ts` |
| Busca | `src/navigation/adminNavSearch.ts`, `adminNavSearchIndex.ts` |
| Página admin | `src/ui/pages/ChatAdminPage.tsx` |
| README componentes | `src/ui/components/admin/README.md` |
