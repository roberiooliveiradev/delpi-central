import {
  Database,
  Home,
  Eye,
  LayoutTemplate,
  Layers,
  MousePointer2,
  Plus,
  Settings2,
} from "lucide-react";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";

export type DeckRibbonTabId =
  | "home"
  | "insert"
  | "element"
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
  /** Elemento / Dados / Camadas — só com seleção no palco. */
  selectionOnly?: boolean;
  disabledWhenNoSlide?: boolean;
};

const T = TV_DASHBOARD_HELP_TOOLTIPS.ribbonTabs;
const PANEL = TV_DASHBOARD_HELP_TOOLTIPS.tabs;

/**
 * Ordem canônica: permanentes primeiro; contextuais Elemento/Dados/Camadas
 * espelham o painel lateral (mesmas abas, mesmos controles).
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
    /** Qualquer bloco selecionado no palco. */
    hasSelection?: boolean;
  },
): DeckRibbonTabMeta[] {
  const hasSelection = Boolean(options?.hasSelection);
  return DECK_RIBBON_TABS.filter((tab) => {
    if (tab.customOnly && !isCustomSlide) return false;
    if (tab.selectionOnly && !hasSelection) return false;
    return true;
  });
}

/** Faixas Inserir + Exibir (+ contextuais) — modal embutido. */
export function resolveEmbeddedComunicadoRibbonTabs(options?: {
  hasSelection?: boolean;
}): DeckRibbonTabMeta[] {
  const hasSelection = Boolean(options?.hasSelection);
  return DECK_RIBBON_TABS.filter((tab) => {
    if (!tab.customOnly) return false;
    if (tab.selectionOnly && !hasSelection) return false;
    return true;
  });
}
