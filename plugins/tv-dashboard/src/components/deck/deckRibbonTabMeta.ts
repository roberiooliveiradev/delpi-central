import {
  Database,
  Home,
  Eye,
  LayoutTemplate,
  Layers,
  MousePointer2,
  Paintbrush,
  Plus,
  Settings2,
  Table2,
} from "lucide-react";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { SelectionPanelTab } from "../comunicadoEditorContextCore";

export type DeckRibbonTabId =
  | "home"
  | "insert"
  | "element"
  | "tableDesign"
  | "tableLayout"
  | "data"
  | "layers"
  | "view"
  | "slide"
  | "playlist";

export type DeckRibbonTabMeta = {
  id: DeckRibbonTabId;
  label: string;
  hint: string;
  icon: typeof Home;
  customOnly?: boolean;
  /** Elemento / Dados / Design·Layout — só com seleção. Camadas não usa isto. */
  selectionOnly?: boolean;
  /**
   * Dados: só com seleção data-bound, ou quando `showDataTab` (Insert / painel aberto).
   */
  dataBoundOnly?: boolean;
  /**
   * `table` — só com table_view selecionada.
   * `nonTable` — esconde quando a seleção é table_view (par Design/Layout assume).
   */
  selectionKind?: "table" | "nonTable";
  disabledWhenNoSlide?: boolean;
};

const T = TV_DASHBOARD_HELP_TOOLTIPS.ribbonTabs;
const PANEL = TV_DASHBOARD_HELP_TOOLTIPS.tabs;

/** Abas do grupo contextual (estilo visual after Programação). */
const CONTEXTUAL_TAB_IDS = new Set<DeckRibbonTabId>([
  "element",
  "tableDesign",
  "tableLayout",
  "data",
  "layers",
]);

/**
 * Ordem canônica: permanentes primeiro; contextuais espelham o painel lateral.
 * Com tabela selecionada: Design da Tabela + Tabela Layout no lugar de Elemento.
 * Camadas: sempre visível em slide custom (sem seleção).
 */
export const DECK_RIBBON_TABS: DeckRibbonTabMeta[] = [
  { id: "home", label: "Página Inicial", hint: T.home, icon: Home },
  { id: "insert", label: "Inserir", hint: T.insert, icon: Plus, customOnly: true },
  { id: "view", label: "Exibir", hint: T.view, icon: Eye, customOnly: true },
  {
    id: "slide",
    label: "Tela",
    hint: PANEL.slide,
    icon: LayoutTemplate,
    disabledWhenNoSlide: true,
  },
  {
    id: "playlist",
    label: "Programação",
    hint: PANEL.playlist,
    icon: Settings2,
  },
  {
    id: "element",
    label: "Elemento",
    hint: PANEL.element ?? T.shape ?? "Propriedades e aparência do elemento selecionado.",
    icon: MousePointer2,
    customOnly: true,
    selectionOnly: true,
    selectionKind: "nonTable",
  },
  {
    id: "tableDesign",
    label: "Design da Tabela",
    hint: T.tableDesign ?? "Estilos, opções de cabeçalho/listras, sombreamento e bordas.",
    icon: Paintbrush,
    customOnly: true,
    selectionOnly: true,
    selectionKind: "table",
  },
  {
    id: "tableLayout",
    label: "Tabela Layout",
    hint: T.tableLayout ?? "Tamanho da moldura, alinhamento, organizar e truncamento.",
    icon: Table2,
    customOnly: true,
    selectionOnly: true,
    selectionKind: "table",
  },
  {
    id: "data",
    label: "Dados",
    hint: PANEL.data ?? T.data ?? "Fonte e parâmetros do elemento selecionado.",
    icon: Database,
    customOnly: true,
    selectionOnly: true,
    dataBoundOnly: true,
  },
  {
    id: "layers",
    label: "Camadas",
    hint: PANEL.layers ?? "Ordem e construção das camadas do slide.",
    icon: Layers,
    customOnly: true,
  },
];

/** Aba do grupo contextual (Elemento / Dados / Camadas / Design·Layout). */
export function isContextualDeckRibbonTab(tab: Pick<DeckRibbonTabMeta, "id">): boolean {
  return CONTEXTUAL_TAB_IDS.has(tab.id);
}

export type ResolveDeckRibbonTabsOptions = {
  hasSelection?: boolean;
  /** Quando true, troca Elemento pelo par Design/Layout da tabela. */
  isTableSelection?: boolean;
  /**
   * Exibe aba Dados mesmo sem seleção data-bound (Insert / painel Dados aberto).
   */
  showDataTab?: boolean;
  /** Seleção atual é data-bound (chart/kpi/table/fonte). */
  hasDataBoundSelection?: boolean;
};

export function resolveDeckRibbonTabs(
  isCustomSlide: boolean,
  options?: ResolveDeckRibbonTabsOptions,
): DeckRibbonTabMeta[] {
  const hasSelection = Boolean(options?.hasSelection);
  const isTableSelection = Boolean(options?.isTableSelection);
  const showDataTab = Boolean(options?.showDataTab);
  const hasDataBoundSelection = Boolean(options?.hasDataBoundSelection);
  return DECK_RIBBON_TABS.filter((tab) => {
    if (tab.customOnly && !isCustomSlide) return false;
    if (tab.selectionOnly && !hasSelection) return false;
    if (tab.dataBoundOnly && !hasDataBoundSelection && !showDataTab) return false;
    if (tab.selectionKind === "table" && !isTableSelection) return false;
    if (tab.selectionKind === "nonTable" && isTableSelection) return false;
    return true;
  });
}

/** Faixas Inserir + Exibir (+ contextuais) — compositor embutido. */
export function resolveEmbeddedComunicadoRibbonTabs(
  options?: ResolveDeckRibbonTabsOptions,
): DeckRibbonTabMeta[] {
  const hasSelection = Boolean(options?.hasSelection);
  const isTableSelection = Boolean(options?.isTableSelection);
  const showDataTab = Boolean(options?.showDataTab);
  const hasDataBoundSelection = Boolean(options?.hasDataBoundSelection);
  return DECK_RIBBON_TABS.filter((tab) => {
    if (!tab.customOnly) return false;
    if (tab.selectionOnly && !hasSelection) return false;
    if (tab.dataBoundOnly && !hasDataBoundSelection && !showDataTab) return false;
    if (tab.selectionKind === "table" && !isTableSelection) return false;
    if (tab.selectionKind === "nonTable" && isTableSelection) return false;
    return true;
  });
}

export type SelectionPanelTabMeta = {
  id: SelectionPanelTab;
  label: string;
  hint: string;
  icon: typeof Home;
};

/**
 * Abas do painel lateral — mesma fonte de labels/hints/ícones da ribbon.
 * Sem seleção: só Camadas.
 * Seleção comum: Elemento (+ Dados) + Camadas.
 * Tabela: Design da Tabela + Tabela Layout (+ Dados) + Camadas.
 */
export function resolveSelectionPanelTabs(options: {
  hasSelection: boolean;
  showDataTab: boolean;
  isTableSelection?: boolean;
}): SelectionPanelTabMeta[] {
  const tabs: SelectionPanelTabMeta[] = [];
  if (options.hasSelection) {
    if (options.isTableSelection) {
      tabs.push({
        id: "tableDesign",
        label: "Design da Tabela",
        hint: T.tableDesign ?? "Estilos, opções de cabeçalho/listras, sombreamento e bordas.",
        icon: Paintbrush,
      });
      tabs.push({
        id: "tableLayout",
        label: "Tabela Layout",
        hint: T.tableLayout ?? "Tamanho da moldura, alinhamento, organizar e truncamento.",
        icon: Table2,
      });
    } else {
      tabs.push({
        id: "element",
        label: "Elemento",
        hint: PANEL.element ?? "Propriedades e aparência do elemento selecionado.",
        icon: MousePointer2,
      });
    }
  }
  if (options.showDataTab) {
    tabs.push({
      id: "data",
      label: "Dados",
      hint: PANEL.data ?? "Fonte e parâmetros do elemento selecionado.",
      icon: Database,
    });
  }
  tabs.push({
    id: "layers",
    label: "Camadas",
    hint: PANEL.layers ?? "Ordem e construção das camadas do slide.",
    icon: Layers,
  });
  return tabs;
}
