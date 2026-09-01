# Wireframes — Administração SI (Configuração enxuta)

> **Rota:** `/apps/strategic-indicators/settings`  
> **Permissão:** `strategic-indicators.settings.manage`  
> **Kit:** `@delpi/plugin-ui` (`PageHero` compact, `SectionCard`, `FilterBarShell`, `DataTable`, `DrawerPanel` / host-contained)  
> **Mapa kit:** [PLUGIN-UI-MAP-ADMIN.md](./PLUGIN-UI-MAP-ADMIN.md)  
> **Helps UI:** [HELP-CONTENT-ADMIN.md](./HELP-CONTENT-ADMIN.md) · [`src/content/helpTooltips.ts`](../src/content/helpTooltips.ts)  
> **Regras:** `plugins-visual-design-system.mdc`, `plugins-reusable-components.mdc`, `plugins-overlay-positioning.mdc`, `mfe-modal-host-contained.mdc`

**Objetivo:** revisar a UI administrativa atual e propor um visual **mais enxuto** — menos camadas de título, menos cards redundantes, navegação clara, formulários progressivos.

**Estado atual (referência código):** `SettingsPage.tsx`, `AdminDepartmentsWorkspace.tsx`, `AdminGoalsWorkspace.tsx`, `CatalogStructureValidationWorkspace.tsx`.

---

## 1. Diagnóstico — o que pesa hoje

| Problema | Onde | Impacto |
|----------|------|---------|
| **Header em camadas** | `PageHeader` + `SettingsHero` + `SettingsStatusStrip` + `tabbar` | ~280–360px antes do conteúdo útil |
| **Metadados de dev no hero** | `SettingsHero` (rota, permission code) | Ruído para operador/admin de negócio |
| **Título duplicado** | `SectionBlock` dentro de cada aba repete o que a aba já diz | Scroll e redundância textual |
| **Painel «legado»** | `SettingsSummaryCards` + grid de 3 cards + blocos weights/goals read-only | Informação histórica competindo com fluxo principal |
| **6 abas pill** | overview, departments, goals, catalog, global, audit | Muitas opções de mesmo peso visual; «Catálogo» separado de «Departamentos» |
| **Formulários longos** | Drawer indicador: 15+ campos visíveis de uma vez | Carga cognitiva; campos avançados misturados com essenciais |
| **Master-detail fixo 320px** | `.si-admin-master-detail` | OK desktop; tablet/mobile precisa stack claro |
| **Validação = tabela larga** | `CatalogStructureValidationWorkspace` | Difícil escanear; filtros competem com toolbar |

**Princípio da proposta:** uma camada de chrome, navegação lateral no desktop, conteúdo denso mas legível, ações primárias sempre visíveis.

---

## 2. Decisões de design (travadas)

| Decisão | Escolha |
|---------|---------|
| Hero | **Um só** — `PageHero` density=`compact` (kit); remove `SettingsHero` |
| Status | **Faixa única** inline: última sync · autor · erro/sucesso · `[Atualizar]` |
| Navegação desktop | **Sidebar 200px** dentro do MFE (4 grupos), não 6 pills |
| Navegação mobile | **Segmented control** sticky (4 itens) ou bottom nav |
| Abas | **4 rotas lógicas** (mesma URL com `?tab=`): Início · Catálogo · Metas · Sistema |
| SectionBlock | Só quando houver **sub-seção** dentro da área; não repetir título da aba |
| Formulários | **Drawer em 2 passos** (Essencial → Avançado) ou accordion kit |
| Validação | Lista compacta + painel de detalhe lateral (não tabela full-width) |
| Import/export | Move para **Sistema** (não ocupa Início) |
| Legado weights/goals | **Remover do Início**; link «Ver leitura legada» colapsável se ainda necessário |

---

## 3. Matriz de fluxos × superfície

| Fluxo | Superfície proposta | P0 | Herança |
|-------|---------------------|-----|---------|
| Ver saúde do módulo | Início — KPI strip + issues count | Sim | — |
| CRUD departamento | Catálogo — master list + detail | Sim | Drawer create/edit |
| CRUD indicador | Catálogo — detail do dept | Sim | Drawer 2 passos |
| Metas anuais | Metas — ano → indicador | Sim | Drawer meta |
| Validar catálogo | Catálogo — sub-nav «Validação» | Sim | Filtros sticky |
| Parâmetros/governança | Sistema — forms compactos | Sim | — |
| Auditoria | Sistema — timeline | Sim | — |
| Import/export bundle | Sistema — card único | Sim | — |
| Refresh snapshot | Hero action global | Sim | Todas abas |

---

## 4. Convenções ASCII

| Símbolo | Significado |
|---------|-------------|
| `[Botão]` / `[ghost]` / `[primary]` | `ActionButton` do kit |
| `·····` | input / select |
| `●` `○` `⚠` `✕` | severidade validação |
| `│ ░░░ │` | skeleton |
| `▼` | seção colapsável |
| `?` | hint (`SectionHintLabel`) |

**Root MFE:** `.dashboard-strategic-indicators.dashboard-page` (alinhar escopo CSS existente `si-*`).

**Breakpoints:**

| Faixa | Regra |
|-------|-------|
| Desktop `>1100px` | Sidebar + área principal (wireframes A) |
| Tablet `769–1100px` | Sidebar colapsável · master-detail 240px |
| Mobile `≤768px` | Nav segmented sticky · master-detail vira stack · drawer full-screen |

---

## 5. WF-SI-00 — Shell administrativo (template)

Substitui: `PageHeader` + `SettingsHero` + tabbar pills.

### Desktop (`>1100px`)

```text
┌─ Sidebar Portal ─┬─ .dashboard-strategic-indicators ─────────────────────────────────────┐
│ Minha DELPI      │ ┌─ PageHero compact ────────────────────────────────────────────────┐ │
│ …                │ │ INDICADORES ESTRATÉGICOS · Administração                          │ │
│ ► Indicadores    │ │ Sync 01/09/2026 · por admin@… · [ghost Atualizar scores]         │ │
│                  │ └───────────────────────────────────────────────────────────────────┘ │
│                  │ ┌ Nav ───┐ ┌─ Conteúdo (WF-SI-01…04) ──────────────────────────────┐ │
│                  │ │ Início │ │                                                              │ │
│                  │ │ Catálogo│ │                                                              │ │
│                  │ │ Metas  │ │                                                              │ │
│                  │ │ Sistema│ │                                                              │ │
│                  │ └────────┘ └──────────────────────────────────────────────────────────────┘ │
└──────────────────┴────────────────────────────────────────────────────────────────────────────┘
```

**Componentes kit:** `PageHero` compact · `ActionButton` · nav local `SiAdminNav` (lista vertical, não CSS custom pesado).

**Status inline:** absorve `SettingsStatusStrip` — erro em banner fino abaixo do hero; sucesso toast ou banner dismissível.

### Mobile (`≤768px`)

```text
┌─ PageHero compact (2 linhas) ─────────────────────────┐
│ Administração SI          [Atualizar]               │
│ Sync 01/09 · admin@…                                │
├─ Segmented sticky ──────────────────────────────────┤
│ [ Início ] [ Catálogo ] [ Metas ] [ Sistema ]       │
├─ conteúdo rota ─────────────────────────────────────┤
│ …                                                   │
└─────────────────────────────────────────────────────┘
```

---

## 6. WF-SI-01 — Início (ex-overview enxuto)

**Remove:** `SettingsSummaryCards`, grid 3 cards explicativos, import/export no topo.

```text
┌─ Área principal ────────────────────────────────────────────────────────────────┐
│ ┌─ KPI strip (1 linha, 4 células) ─────────────────────────────────────────────┐ │
│ │ 8 deptos │ 42 indicadores │ 2026: 38 metas │ ⚠ 3 avisos catálogo          │ │
│ └──────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│ ┌─ Ações rápidas ──────────────────────────────────────────────────────────────┐ │
│ │ [primary Ir para validação]  [ghost Novo indicador]  [ghost Novo ano metas]   │ │
│ └──────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│ ┌─ SectionCard «Pendências» (só se issues > 0) ────────────────────────────────┐ │
│ │ ⚠ Comercial · commercial-rol · source_consolidated sem meta Consolidado      │ │
│ │ ⚠ Qualidade · quality-ppm-internal · ppm + sum (config inválida)             │ │
│ │                                    [Ver todas na validação →]                 │ │
│ └──────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│ ┌─ SectionCard «Atividade recente» (opcional P1) ──────────────────────────────┐ │
│ │ Última alteração: indicator_goals · commercial-rol · há 2h                   │ │
│ └──────────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────┘
```

**Dados:** contagem de `useCatalogStructureValidation` (issues) + APIs existentes — **sem** bloco legado weights/goals.

---

## 7. WF-SI-02 — Catálogo (departamentos + indicadores + validação)

Unifica abas atuais **Departamentos** e **Catálogo e validação** com sub-nav horizontal leve.

### 7.A — Sub-nav

```text
[ Estrutura ● ]   [ Validação (3) ]
```

### 7.B — Estrutura (master-detail enxuto)

```text
┌─ Master 260px ─────────────┬─ Detail ────────────────────────────────────────────┐
│ [+ Depto]  ··· busca ···   │ Comercial                           [Editar] [···] │
│ ┌────────────────────────┐ │ Agregação dept: Consolidado · Peso IGD 18%            │
│ │● Comercial      18%   │ │ ─────────────────────────────────────────────────── │
│ │  Produção        22%   │ │ Indicadores (6)              [+ Indicador] ··· 🔍   │
│ │  Qualidade       15%   │ │ ┌────────────────────────────────────────────────┐ │
│ │  …                     │ │ │ ROL          40%  per_unit  sum    ● ativo  [>] │ │
│ └────────────────────────┘ │ │ OTD          25%  per_unit  média  ● ativo  [>] │ │
│                            │ │ Closing rate 15%  per_unit  média  ○ inativo    │ │
│                            │ └────────────────────────────────────────────────┘ │
│                            │ Linha = clique abre drawer edição (não nova página) │
└────────────────────────────┴──────────────────────────────────────────────────────┘
```

**Lista indicador (denso):** nome · peso · escopo · agregação filiais (badge curto) · status · chevron.

**Drawer indicador — 2 passos (WF-SI-02-D1):**

```text
┌─ Drawer «Editar indicador» ────────────────────────────────┐
│ Passo 1 de 2 — Essencial                          [×]    │
│ Nome ·················································   │
│ ID ···················································   │
│ Peso % ·····  Escopo [Por unidade ▼]                     │
│ Agregação filiais [Soma ▼]  ?                            │
│ Fonte (source_key) ···································   │
│ Direção [Quanto maior, melhor ▼]   [Ativo toggle]        │
│                                                          │
│              [Cancelar]            [Continuar →]           │
└──────────────────────────────────────────────────────────┘

┌─ Drawer passo 2 — Formato & avançado ────────────────────┐
│ Unidade [Moeda ▼]  Decimais [2]  Prefixo · Sufixo        │
│ Descrição estratégica (textarea 3 linhas)                │
│ Ordem exibição ·······································   │
│                                                          │
│              [← Voltar]     [Salvar indicador]           │
└──────────────────────────────────────────────────────────┘
```

**Departamento drawer:** mesmos campos atuais, agrupados em **Identidade** | **IDD & peso** | **Resumo estratégico** (accordion 3 painéis, um aberto por vez).

### 7.C — Validação (lista + detalhe)

Substitui tabela full-width.

```text
┌─ FilterBarShell sticky ──────────────────────────────────────────────────────────┐
│ Ano [2026 ▼]  Depto [Todos ▼]  [✓] Só com pendências   ⚠3  ✕1   ··· busca ···   │
└──────────────────────────────────────────────────────────────────────────────────┘
┌─ Lista ───────────────────────────────┬─ Detalhe (row selecionada) ──────────────┐
│ ⚠ Comercial › ROL                     │ ROL · Comercial · per_unit · sum        │
│   source_sem_meta_consolidada           │ Metas: C○ 01● 02●                       │
│ ● Qualidade › PPM interno        OK   │ Issues:                                 │
│ ⚠ Suprimentos › OTD                   │ • Agregação «fonte» exige meta C.         │
│ ✕ RH › PDIs                           │ [Ir para indicador] [Ir para metas]     │
└───────────────────────────────────────┴──────────────────────────────────────────┘
```

**Mobile:** lista full-width; toque na linha abre **drawer detalhe** (não coluna lateral).

---

## 8. WF-SI-03 — Metas anuais

Mantém master-detail **ano → painel**, reduz chrome.

```text
┌─ Master anos ──────────────┬─ Detail ano 2026 ─────────────────────────────────────┐
│ [+ Ano]                    │ 2026 · 38 metas ativas · 4 indicadores sem meta      │
│ ┌────────────────────────┐ │ [Duplicar ano] [Preencher faltantes] [Export ano]     │
│ │● 2026  38 metas  ⚠2     │ │ ─────────────────────────────────────────────────── │
│ │  2025  36 metas         │ │ Filtro: Depto [▼] Indicador ··· 🔍                  │
│ │  2024  …                │ │ ┌ DataTable compact ──────────────────────────────┐ │
│ └────────────────────────┘ │ │ Indicador │ Escopo │ Modo │ Meta │ C/01/02 │ [>]  │ │
│                            │ └───────────────────────────────────────────────────┘ │
└────────────────────────────┴───────────────────────────────────────────────────────┘
```

**Remove:** parágrafo hint longo no toolbar; substituir por `SectionHintLabel` no header da tabela.

**Drawer meta:** campos atuais + badges escopo C/01/02 no topo (reuso `GoalScopeBadges`).

---

## 9. WF-SI-04 — Sistema (global + auditoria + bundle)

```text
┌─ SectionCard «Parâmetros globais» ───────────────────────────────────────────────┐
│ Tabela key-value editável (3–8 linhas visíveis)              [Salvar alterações] │
└──────────────────────────────────────────────────────────────────────────────────┘

┌─ SectionCard «Governança» ───────────────────────────────────────────────────────┐
│ Notas / políticas (textarea por item)                        [Salvar alterações] │
└──────────────────────────────────────────────────────────────────────────────────┘

┌─ SectionCard «Backup e migração» ────────────────────────────────────────────────┐
│ Exportar JSON · Importar JSON · Preview diff          (AdminConfigImportExport)   │
└──────────────────────────────────────────────────────────────────────────────────┘

┌─ SectionCard «Auditoria» ────────────────────────────────────────────────────────┐
│ Filtro entidade [▼]  Período [▼]                                                 │
│ Timeline compacta (últimos 20 eventos)                        [Ver histórico →]  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

**Auditoria full:** link expande mesma aba ou rota `?tab=system&view=audit` — evita 6ª aba top-level.

---

## 10. Comparativo visual — antes × depois

| Métrica | Antes (est.) | Depois (proposta) |
|---------|--------------|-------------------|
| Blocos acima do fold | 4–5 | 1 hero + nav |
| Abas top-level | 6 pills | 4 (sidebar/segmented) |
| Cliques dept → indicador | 1 select + scroll list | 1 clique linha |
| Campos visíveis create indicador | ~15 de uma vez | 8 + 7 (passo 2) |
| Altura header admin | ~320px | ~96–120px |
| Validação em laptop 1366px | scroll horizontal | lista + detalhe |

---

## 11. Mapa de componentes (implementação futura)

| Wireframe | Kit / existente | Novo (mínimo) |
|-----------|-----------------|---------------|
| Shell | `PageHero`, `ActionButton` | `SiAdminNav` (nav vertical fina) |
| KPI strip | `MetricStrip` ou `KpiCard` size=sm | composição Início |
| Master-detail | padrão `si-admin-master-detail` | ajustar colunas 260px / token |
| Drawer 2 passos | `DrawerPanel` / host-contained | `SiWizardSteps` (header step only) |
| Validação lista | `DataTable` density=compact **ou** lista custom escopada | `SiValidationSplitView` |
| Forms | `SiNativeTextControl`, `SiSelectControl` | agrupar em accordion kit |

**Não fazer:** CSS de componente kit no MFE; modais full-screen no portal; nova lib de steps externa.

---

## 12. Fases sugeridas (implementação)

| Fase | Escopo | Risco |
|------|--------|-------|
| **P0** | Shell enxuto (remover Hero, status inline, nav 4 itens) | Baixo |
| **P1** | Catálogo unificado + drawer 2 passos indicador | Médio |
| **P2** | Validação split-view + Início KPI/issues | Médio |
| **P3** | Metas toolbar/table compact; Sistema agrupado | Baixo |
| **P4** | Remover blocos legado overview; polish mobile | Baixo |

---

## 13. Critérios de pronto (UX)

- [ ] Above-the-fold mostra nav + conteúdo útil em 900px altura (1080p)
- [ ] Zero repetição título aba = SectionBlock title
- [ ] Create indicador ≤ 8 campos no passo 1
- [ ] Validação sem scroll horizontal em 1280px
- [ ] Mobile: master-detail vira stack; drawer ocupa viewport
- [ ] Claro/escuro validado no portal federado
- [ ] `npm run build` verde em `plugins/strategic-indicators`

---

## Referências

- UI atual: `plugins/strategic-indicators/src/ui/pages/SettingsPage.tsx`
- Design system: `.cursor/rules/plugins-visual-design-system.mdc`
- Componentes: `.cursor/rules/plugins-reusable-components.mdc`
- Wireframes referência: `docs/12-roadmap-e-evolucao/production-pulse/WIREFRAMES.md`
