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
  /** Elemento / Dados / Camadas / Design·Layout tabela — só com seleção. */
  selectionOnly?: boolean;
  /**
   * `table` — só com table_view selecionada.
   * `nonTable` — esconde quando a seleção é table_view (par Design/Layout assume).
   */
  selectionKind?: "table" | "nonTable";
  disabledWhenNoSlide?: boolean;
};

const T = TV_DASHBOARD_HELP_TOOLTIPS.ribbonTabs;
const PANEL = TV_DASHBOARD_HELP_TOOLTIPS.tabs;

/**
 * Ordem canônica: permanentes primeiro; contextuais espelham o painel lateral.
 * Com tabela selecionada: Design da Tabela + Tabela Layout no lugar de Elemento.
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
  },
  {
    id: "layers",
    label: "Camadas",
    hint: PANEL.layers ?? "Ordem e construção das camadas do slide.",
    icon: Layers,
    customOnly: true,
    selectionOnly: true,
  },
];

/** Aba contextual (só com elemento selecionado). */
export function isContextualDeckRibbonTab(
  tab: Pick<DeckRibbonTabMeta, "selectionOnly">,
): boolean {
  return Boolean(tab.selectionOnly);
}

export function resolveDeckRibbonTabs(
  isCustomSlide: boolean,
  options?: {
    hasSelection?: boolean;
    /** Quando true, troca Elemento pelo par Design/Layout da tabela. */
    isTableSelection?: boolean;
  },
): DeckRibbonTabMeta[] {
  const hasSelection = Boolean(options?.hasSelection);
  const isTableSelection = Boolean(options?.isTableSelection);
  return DECK_RIBBON_TABS.filter((tab) => {
    if (tab.customOnly && !isCustomSlide) return false;
    if (tab.selectionOnly && !hasSelection) return false;
    if (tab.selectionKind === "table" && !isTableSelection) return false;
    if (tab.selectionKind === "nonTable" && isTableSelection) return false;
    return true;
  });
}

/** Faixas Inserir + Exibir (+ contextuais) — modal embutido. */
export function resolveEmbeddedComunicadoRibbonTabs(options?: {
  hasSelection?: boolean;
  isTableSelection?: boolean;
}): DeckRibbonTabMeta[] {
  const hasSelection = Boolean(options?.hasSelection);
  const isTableSelection = Boolean(options?.isTableSelection);
  return DECK_RIBBON_TABS.filter((tab) => {
    if (!tab.customOnly) return false;
    if (tab.selectionOnly && !hasSelection) return false;
    if (tab.selectionKind === "table" && !isTableSelection) return false;
    if (tab.selectionKind === "nonTable" && isTableSelection) return false;
    return true;
  });
}
