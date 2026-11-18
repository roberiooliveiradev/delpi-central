# DELPI Line Balance Studio V4 — inventário de componentes e plano reuse-first

**Data:** 2026-11-18  
**Estado:** `INVENTORIED / UX_DESIGN_APPROVED / IMPLEMENTATION_NOT_STARTED_IN_THIS_TASK`  
**Contrato de UX:** [cards de origem + sidebar interna retrátil](ux-v4-study-entry-and-method-sidebar.md).  
**Owner UI genérica:** `@delpi/plugin-ui`. **Owner da composição/métodos e estado do estudo:** `plugins/delpi-line-balance-studio`. **Consumer inicial:** MFE `plugins/engineering` via API pública.  
**Regra:** não criar subaplicação ou UI duplicada no Portal Engenharia. Não copiar componentes da implementação legada de Balanceamento/Roteiro do Portal. Não colocar regras de balanceamento no Plugin UI.

## 1. Inventário factual (exports públicos no HEAD observado)

| Necessidade UX V4 | Componente público localizado | Superfície observada | Decisão de primeira abordagem |
|---|---|---|---|
| Dois cards grandes selecionáveis (Produto DELPI / Estudo manual) | `NavigationCard` com `density="featured"`, ícone, descrição, click, disabled e orientação | `plugins/plugin-ui/src/components/layout/NavigationCard.tsx`, `src/index.ts` exporta layout | **REUSE candidato**; testar selected state, propor extensão genérica *somente se faltar* |
| Container e seções com título, ações e recolhimento | `SectionCard` (`collapsible`, `open`, `onOpenChange`) | `components/layout/SectionCard.tsx` | **REUSE**; não confundir SectionCard recolhido com sidebar retrátil |
| Cabeçalho do Studio | `PageHeader` | `native-controls.ts` e index geral | **REUSE**; não duplicar chrome do Portal |
| Botões/ações | `ActionButton`, `IconButton` | `native-controls.ts` | **REUSE** |
| Seletor de filial/estágio/cenários | `ModernSelectControl` | `native-controls.ts` | **REUSE**, garantir portal dentro do Shadow DOM |
| Input de SKU/nome/horários | `NativeTextControl` | `native-controls.ts` | **REUSE** |
| Stepper de demanda/lote/postos | `NumberStepperControl` sobre `ComboboxNumberControl` | `components/forms/NumberStepperControl.tsx`, barrel `components/forms/index.ts` | **REUSE via API pública geral**; avaliar exposição no entrypoint estreito `native-controls` se a demo independente exigir |
| Switch Visual/Tabela ou Horários/Minutos | `SegmentToggle` | `components/forms/SegmentToggle.tsx`, barrel forms | **REUSE**; eventualmente export estreito, sem duplicação |
| Tabela editável de operações | `DataTable`, `EditableTableCell` | `native-controls.ts`, `components/forms` | **REUSE candidato**; edição, seleção e foco exigem contrato do Studio |
| KPIs de resumo | `SimpleKpiCard`, `StatusBadge`, `StateBox` | `native-controls.ts` | **REUSE** |
| Gráfico Yamazumi | `StackedColumnChart`; catálogo geral também possui `ChartViewShell` e `MultiTypeSeriesChart` | `native-controls.ts` e `components/charts` | **REUSE** respeitando dados observados/providos; sem solver no gráfico |
| Sidebar de métodos com expand/collapse, icons-only, tooltip, active, mobile drawer | `NavigationRail` identificado em `components/conversation` com categorias FIXAS DÉLIA, não método genérico | `NavigationRail.tsx` | **NÃO reutilizar diretamente**: API fixa `conversations/projects/agents/plugins`; **EXTENSÃO candidata** `CollapsibleToolRail` ou `CollapsibleNavigationPanel` genérico após contrato |
| Paleta de ícones dos métodos | `lucide-react` já dependência do kit | `plugins/plugin-ui/package.json` | **REUSE**; mapear M1 gauge, M2 list-ordered, M3 git-branch, M4 columns-3, M5 chart-no-axes-column-increasing, M6 users-round no Studio (não no kit) |
| Status de método/capability | `StatusBadge` genérico | `native-controls.ts` | **REUSE**; estados são semântica do Studio/domínio, não do kit |

**Observação:** nomes acima foram lidos do código fonte GitHub; não há teste de props em runtime nem garantia de compatibilidade com o entrypoint estreito ou Module Federation até build/contract tests. O `NavigationRail` conversacional existe, mas **não** é um substituto genérico pronto para o rail M1–M6.

## 2. Novo componente genérico candidato no Plugin UI

**Nome provisório:** `CollapsibleToolRail` (alternativa genérica `CollapsibleNavigationPanel`; escolher nome após buscar equivalentes em todo Plugin UI e design system).

**Responsabilidade permitida:** layout de trilho lateral expandível, listagem de itens com ícones, active, labels, tooltip, grupos e colapso mobile. **Não** saber o que é M1–M6, produto, roteiro, takt, Yamazumi, DRAFT ou API.

**Contrato candidato (pseudocódigo, não API vigente):**
```ts
type ToolRailItem = {
  id: string;
  label: string;
  icon: ReactNode;
  description?: string;
  disabled?: boolean;
  statusText?: string;
};
type ToolRailGroup = { id: string; label?: string; collapsible?: boolean; items: ToolRailItem[] };
type CollapsibleToolRailProps = {
  groups: readonly ToolRailGroup[];
  activeId?: string;
  expanded: boolean;
  onExpandedChange: (expanded: boolean) => void;
  onSelect: (id: string) => void;
  ariaLabel: string;
  mobileMode?: "auto" | "drawer" | "rail";
};
```

Revisar necessidade de props de classe, largura via tokens, foco e render de indicadores; evitar criar engine de estado ou permissões no kit. `statusText` é texto de apresentação, não capability check.

**AC mínimo do componente genérico:**
1. Expandido: nome/ícone/status; recolhido: só ícone, label acessível e tooltip em foco/hover.
2. Manter `activeId` e invocar `onSelect`; não chamar callback ao recolher.
3. Grupos planejados podem ser exibidos recolhidos e itens disabled não invocam `onSelect`.
4. Teclado tab/Enter/Escape conforme variante, foco visível; no mobile drawer recuperar foco, sem overlay z-index quebrado.
5. Theme light/dark, CSS pelo kit, breakpoints 1440/1024/390/320 sem overflow.
6. Entry points genéricos `@delpi/plugin-ui` e, quando justificado, `@delpi/plugin-ui/native-controls`; teste de export e estilos no Shadow DOM.
7. Teste em consumidor neutro para confirmar portabilidade fora do Portal Engenharia.

## 3. Composição específica do Studio (NÃO mover para Plugin UI)

1. `StudyOriginChooser`: dois cards `NavigationCard featured`, escolha oficial/manual, dados e transição para cabeçalho compacto; identidade/status/erros e prevenção contra perda do rascunho.
2. `MethodRailAdapter`: mapeia catálogo M1–M6, ícones e estado de capability para `CollapsibleToolRail` genérico.
3. `StudyContextHeader`: produto/filial/estágio ou nome de estudo manual, provenance, ação Trocar origem.
4. `MethodWorkspace`: compartilha operações, demanda, pausas, postos e cenários; muda somente a vista específica e invalida resultados stale.
5. `ShiftScheduleEditor`, `OperationsEditor`, `StationBoard`, `YamazumiWorkspace` — módulos de domínio de interface com controles do kit, sem fonte oficial e sem cálculo de solver.

**Consumer Portal Engenharia:** busca roteiros autorizados, filial/estágio, AuthZ/SSO e fontes; passa dados via contrato Studio. Não construir cards/rail duplicados no host.

## 4. Ordem de implementação recomendada

| Slice | Owner | Entrega | Gate |
|---|---|---|---|
| UI-0 | Plugin UI + Studio | Inventário dos exports reais, API contracts, screenshot baseline GitHub Pages/HML | Review documental |
| UI-1 | Plugin UI | Testar `NavigationCard featured` para escolha da origem; ajustar **só** lacunas genéricas necessárias | Component tests e visual |
| UI-2 | Plugin UI | Construir `CollapsibleToolRail` **se não houver equivalente genérico**; CSS, testes de teclado/mobile, exports | Build Plugin UI, Shadow DOM test |
| ST-1 | Studio | Montar dois cards de origem + MethodRailAdapter + estados | Standalone demo e tests |
| ST-2 | Studio | Cabeçalho compacto/contexto compartilhado/troca de método | Unit, scenario, F5 tests |
| INT-1 | Portal Engenharia | Consumir API pública Studio atualizada, sem layout duplicado | HML E2E/visual/regressão |
| VERIFY | Independente | Verify e HML; PROD separado após aprovação | `PASS/INCONCLUSIVE` honesto |

## 5. Gates de não regressão

- CSS canônico do Plugin UI dentro do Shadow DOM via pipeline validado (`?inline`/estilos); não reaparecer interface sem estilos; sem token override host.
- Preview GitHub Pages e HML visualmente equivalentes para mesma fixture, temas e viewports.
- Sem regressão da Ficha do Produto/Roteiro e da área Processos.
- M1 manual não anuncia cálculo oficial sem capability. M5 visual não é solver. M2 limitado; M3/M4/M6 planejados.
- Dados de fonte/filial/estágio/revisão e `DRAFT_LOCAL` preservados na alternância. Nenhum write oficial.
- Primeiro consumidor real e execução de testes na SHA; kit permanece agnóstico a Engenharia.

## 6. Estado

Este documento é **inventário + plano**, não modifica componentes, código ou deploy. `TEST_NOT_RUN` para integração V4. Uma tarefa de desenvolvimento deve começar pelo Gate UI-0 e seguir em pequenos commits verificáveis.
