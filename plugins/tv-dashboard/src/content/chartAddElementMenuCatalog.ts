import type { LucideIcon } from "lucide-react";
import {
  AlignLeft,
  AlignRight,
  ArrowDown,
  ArrowUp,
  BarChart3,
  CircleDot,
  Grid3x3,
  Heading,
  ListOrdered,
  Table2,
  Tags,
  Type,
  X,
} from "lucide-react";
import type { SeriesChartKind } from "@delpi/plugin-ui/index";
import type { ChartAddElementChoiceId, ChartElementId } from "@delpi/tv-dashboard-presentation";
import {
  CHART_ELEMENT_CATALOG,
  isChartElementApplicable,
} from "@delpi/tv-dashboard-presentation";

export type ChartAddElementFlyoutChoice = {
  id: ChartAddElementChoiceId;
  label: string;
  icon: LucideIcon;
};

export type ChartAddElementMenuRoot = {
  elementId: ChartElementId;
  label: string;
  icon: LucideIcon;
  moreOptionsLabel: string;
  choices: ChartAddElementFlyoutChoice[];
};

const ROOT_META: Record<
  Exclude<
    ChartElementId,
    "chartArea" | "plotArea" | "series"
  >,
  { icon: LucideIcon; moreOptionsLabel: string }
> = {
  axes: { icon: BarChart3, moreOptionsLabel: "Mais opções de eixos…" },
  axisTitles: { icon: Type, moreOptionsLabel: "Mais opções de títulos de eixos…" },
  chartTitle: { icon: Heading, moreOptionsLabel: "Mais opções de título do gráfico…" },
  dataLabels: { icon: Tags, moreOptionsLabel: "Mais opções de rótulos de dados…" },
  dataTable: { icon: Table2, moreOptionsLabel: "Mais opções de tabela de dados…" },
  gridlines: { icon: Grid3x3, moreOptionsLabel: "Mais opções de linhas de grade…" },
  legend: { icon: ListOrdered, moreOptionsLabel: "Mais opções de legenda…" },
  markers: { icon: CircleDot, moreOptionsLabel: "Mais opções de marcadores…" },
};

/** Ordem PPT-ish dos itens raiz do flyout. */
const ROOT_ORDER: Array<keyof typeof ROOT_META> = [
  "axes",
  "axisTitles",
  "chartTitle",
  "dataLabels",
  "dataTable",
  "gridlines",
  "legend",
  "markers",
];

const CHOICES_BY_ROOT: Record<keyof typeof ROOT_META, ChartAddElementFlyoutChoice[]> = {
  axes: [
    { id: "axes:x", label: "Horizontal principal", icon: ArrowDown },
    { id: "axes:y", label: "Vertical principal", icon: AlignLeft },
    { id: "axes:none", label: "Nenhum", icon: X },
  ],
  axisTitles: [
    { id: "axisTitles:x", label: "Horizontal principal", icon: ArrowDown },
    { id: "axisTitles:y", label: "Vertical principal", icon: AlignLeft },
    { id: "axisTitles:none", label: "Nenhum", icon: X },
  ],
  chartTitle: [
    { id: "chartTitle:none", label: "Nenhum", icon: X },
    { id: "chartTitle:show", label: "Mostrar", icon: Heading },
  ],
  dataLabels: [
    { id: "dataLabels:none", label: "Nenhum", icon: X },
    { id: "dataLabels:show", label: "Mostrar", icon: Tags },
  ],
  dataTable: [
    { id: "dataTable:none", label: "Nenhum", icon: X },
    { id: "dataTable:show", label: "Mostrar", icon: Table2 },
  ],
  gridlines: [
    { id: "grid:horizontal", label: "Horizontal principal", icon: ArrowDown },
    { id: "grid:vertical", label: "Vertical principal", icon: AlignLeft },
    { id: "grid:none", label: "Nenhum", icon: X },
  ],
  legend: [
    { id: "legend:none", label: "Nenhum", icon: X },
    { id: "legend:right", label: "Direita", icon: AlignRight },
    { id: "legend:top", label: "Superior", icon: ArrowUp },
    { id: "legend:left", label: "Esquerda", icon: AlignLeft },
    { id: "legend:bottom", label: "Inferior", icon: ArrowDown },
  ],
  markers: [
    { id: "markers:none", label: "Nenhum", icon: X },
    { id: "markers:show", label: "Mostrar", icon: CircleDot },
  ],
};

/**
 * Catálogo UI do menu «Adicionar elemento» (flyouts).
 * Filtra por tipo de gráfico via `isChartElementApplicable`.
 */
export function resolveChartAddElementMenuRoots(
  chartKind: SeriesChartKind,
): ChartAddElementMenuRoot[] {
  return ROOT_ORDER.flatMap((elementId) => {
    const def = CHART_ELEMENT_CATALOG.find((entry) => entry.id === elementId);
    if (!def || !isChartElementApplicable(def, chartKind)) return [];
    const meta = ROOT_META[elementId];
    return [
      {
        elementId,
        label: def.label,
        icon: meta.icon,
        moreOptionsLabel: meta.moreOptionsLabel,
        choices: CHOICES_BY_ROOT[elementId],
      },
    ];
  });
}

/** @deprecated Prefer `resolveChartAddElementMenuRoots` — lista plana legada. */
export { CHART_ADD_ELEMENT_ITEMS } from "./chartAddElementItems";
