import type { LucideIcon } from "lucide-react";
import {
  Activity,
  Gauge,
  Heading,
  LayoutTemplate,
  LineChart,
  Target,
  TrendingUp,
  Type,
  X,
} from "lucide-react";
import type { KpiAddElementChoiceId, KpiElementId } from "@delpi/tv-dashboard-presentation";

export type KpiAddElementFlyoutChoice = {
  id: KpiAddElementChoiceId;
  label: string;
  icon: LucideIcon;
};

export type KpiAddElementMenuRoot = {
  elementId: KpiElementId | "kpiLayout";
  label: string;
  icon: LucideIcon;
  moreOptionsLabel: string;
  choices: KpiAddElementFlyoutChoice[];
};

export function resolveKpiAddElementMenuRoots(): KpiAddElementMenuRoot[] {
  return [
    {
      elementId: "kpiTitle",
      label: "Título",
      icon: Heading,
      moreOptionsLabel: "Mais opções de título…",
      choices: [
        { id: "title:on", label: "Mostrar", icon: Heading },
        { id: "title:off", label: "Ocultar", icon: X },
      ],
    },
    {
      elementId: "kpiHint",
      label: "Subtítulo",
      icon: Type,
      moreOptionsLabel: "Mais opções de subtítulo…",
      choices: [
        { id: "hint:on", label: "Mostrar", icon: Type },
        { id: "hint:off", label: "Ocultar", icon: X },
      ],
    },
    {
      elementId: "kpiIcon",
      label: "Ícone",
      icon: Gauge,
      moreOptionsLabel: "Mais opções de ícone…",
      choices: [
        { id: "icon:on", label: "Mostrar", icon: Gauge },
        { id: "icon:off", label: "Ocultar", icon: X },
      ],
    },
    {
      elementId: "kpiComparison",
      label: "Comparação",
      icon: TrendingUp,
      moreOptionsLabel: "Mais opções de comparação…",
      choices: [
        { id: "comparison:target", label: "Vs meta", icon: Target },
        { id: "comparison:previous", label: "Vs período", icon: TrendingUp },
        { id: "comparison:off", label: "Nenhuma", icon: X },
      ],
    },
    {
      elementId: "kpiProgress",
      label: "Progresso",
      icon: Activity,
      moreOptionsLabel: "Mais opções de progresso…",
      choices: [
        { id: "progress:on", label: "Barra até a meta", icon: Activity },
        { id: "progress:off", label: "Nenhum", icon: X },
      ],
    },
    {
      elementId: "kpiSparkline",
      label: "Sparkline",
      icon: LineChart,
      moreOptionsLabel: "Mais opções de sparkline…",
      choices: [
        { id: "sparkline:on", label: "Mostrar série", icon: LineChart },
        { id: "sparkline:off", label: "Ocultar", icon: X },
      ],
    },
    {
      elementId: "kpiLayout",
      label: "Layout",
      icon: LayoutTemplate,
      moreOptionsLabel: "Mais opções de layout…",
      choices: [
        { id: "layout:compact", label: "Compacto", icon: LayoutTemplate },
        { id: "layout:ban", label: "BAN + tendência", icon: LineChart },
        { id: "layout:scorecard", label: "Scorecard + meta", icon: Target },
        { id: "layout:free", label: "Layout livre", icon: LayoutTemplate },
      ],
    },
  ];
}
