import { BarChart3, Home, Eye, LayoutTemplate, Paintbrush, Plus, Settings2, Shapes } from "lucide-react";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";

export type DeckRibbonTabId =
  | "home"
  | "insert"
  | "format"
  | "chart"
  | "shape"
  | "view"
  | "slide"
  | "playlist";

export type DeckRibbonTabMeta = {
  id: DeckRibbonTabId;
  label: string;
  hint: string;
  icon: typeof Home;
  customOnly?: boolean;
  /** Só aparece com gráfico selecionado (aba contextual Excel). */
  chartOnly?: boolean;
  /** Só aparece com forma selecionada (aba contextual PowerPoint). */
  shapeOnly?: boolean;
  disabledWhenNoSlide?: boolean;
};

const T = TV_DASHBOARD_HELP_TOOLTIPS.ribbonTabs;

export const DECK_RIBBON_TABS: DeckRibbonTabMeta[] = [
  { id: "home", label: "Página Inicial", hint: T.home, icon: Home },
  { id: "insert", label: "Inserir", hint: T.insert, icon: Plus, customOnly: true },
  { id: "format", label: "Formatar", hint: T.format, icon: Paintbrush, customOnly: true },
  {
    id: "chart",
    label: "Gráfico",
    hint: T.chart ?? "Ferramentas do gráfico: tipo, rótulos, eixos e formato (como no Excel Online).",
    icon: BarChart3,
    customOnly: true,
    chartOnly: true,
  },
  {
    id: "shape",
    label: "Forma",
    hint: T.shape ?? "Ferramentas da forma: estilos, preenchimento, contorno e tamanho (como no PowerPoint).",
    icon: Shapes,
    customOnly: true,
    shapeOnly: true,
  },
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

export function resolveDeckRibbonTabs(
  isCustomSlide: boolean,
  options?: { chartSelected?: boolean; shapeSelected?: boolean },
): DeckRibbonTabMeta[] {
  const chartSelected = Boolean(options?.chartSelected);
  const shapeSelected = Boolean(options?.shapeSelected);
  return DECK_RIBBON_TABS.filter((tab) => {
    if (tab.customOnly && !isCustomSlide) return false;
    if (tab.chartOnly && !chartSelected) return false;
    if (tab.shapeOnly && !shapeSelected) return false;
    return true;
  });
}

/** Faixas Inserir + Formatar (+ Gráfico/Forma quando selecionados) — modal embutido. */
export function resolveEmbeddedComunicadoRibbonTabs(options?: {
  chartSelected?: boolean;
  shapeSelected?: boolean;
}): DeckRibbonTabMeta[] {
  const chartSelected = Boolean(options?.chartSelected);
  const shapeSelected = Boolean(options?.shapeSelected);
  return DECK_RIBBON_TABS.filter((tab) => {
    if (!tab.customOnly) return false;
    if (tab.chartOnly && !chartSelected) return false;
    if (tab.shapeOnly && !shapeSelected) return false;
    return true;
  });
}
