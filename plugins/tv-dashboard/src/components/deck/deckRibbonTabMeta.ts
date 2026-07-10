import { Home, Eye, LayoutTemplate, Paintbrush, Plus, Settings2 } from "lucide-react";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";

export type DeckRibbonTabId = "home" | "insert" | "format" | "view" | "slide" | "playlist";

export type DeckRibbonTabMeta = {
  id: DeckRibbonTabId;
  label: string;
  hint: string;
  icon: typeof Home;
  customOnly?: boolean;
  disabledWhenNoSlide?: boolean;
};

const T = TV_DASHBOARD_HELP_TOOLTIPS.ribbonTabs;

export const DECK_RIBBON_TABS: DeckRibbonTabMeta[] = [
  { id: "home", label: "Página Inicial", hint: T.home, icon: Home },
  { id: "insert", label: "Inserir", hint: T.insert, icon: Plus, customOnly: true },
  { id: "format", label: "Formatar", hint: T.format, icon: Paintbrush, customOnly: true },
  { id: "view", label: "Exibir", hint: T.view, icon: Eye, customOnly: true },
  {
    id: "slide",
    label: "Tela",
    hint: TV_DASHBOARD_HELP_TOOLTIPS.tabs.slide,
    icon: LayoutTemplate,
    disabledWhenNoSlide: true,
  },
  {
    id: "playlist",
    label: "Programação",
    hint: TV_DASHBOARD_HELP_TOOLTIPS.tabs.playlist,
    icon: Settings2,
  },
];

export function resolveDeckRibbonTabs(isCustomSlide: boolean): DeckRibbonTabMeta[] {
  return DECK_RIBBON_TABS.filter((tab) => !tab.customOnly || isCustomSlide);
}

/** Faixas Inserir + Formatar — modal embutido e preview rápido do compositor. */
export function resolveEmbeddedComunicadoRibbonTabs(): DeckRibbonTabMeta[] {
  return DECK_RIBBON_TABS.filter((tab) => tab.customOnly);
}
