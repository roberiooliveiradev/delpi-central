import type { LucideIcon } from "lucide-react";
import {
  BarChart3,
  Grid3x3,
  Heading,
  ListOrdered,
  Table2,
  Tags,
  Type,
} from "lucide-react";
import type { ChartElementId } from "@delpi/tv-dashboard-presentation";

export type ChartAddElementItem = {
  id: ChartElementId;
  icon: LucideIcon;
  label: string;
};

/** Fonte única — ribbon «Adicionar elemento» e float `+`. */
export const CHART_ADD_ELEMENT_ITEMS: ChartAddElementItem[] = [
  { id: "chartTitle", icon: Heading, label: "Título do gráfico" },
  { id: "axisTitles", icon: Type, label: "Títulos dos eixos" },
  { id: "legend", icon: ListOrdered, label: "Legenda" },
  { id: "dataLabels", icon: Tags, label: "Rótulos de dados" },
  { id: "dataTable", icon: Table2, label: "Tabela de dados" },
  { id: "axes", icon: BarChart3, label: "Eixos" },
  { id: "gridlines", icon: Grid3x3, label: "Linhas de grade" },
];
