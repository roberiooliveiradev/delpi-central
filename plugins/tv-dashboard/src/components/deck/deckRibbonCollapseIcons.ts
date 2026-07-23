import type { LucideIcon } from "lucide-react";
import {
  AlignLeft,
  ArrowLeft,
  BarChart3,
  Baseline,
  Circle,
  Clapperboard,
  Database,
  Eye,
  Grid3x3,
  Image,
  Layers,
  LayoutTemplate,
  LineChart,
  Link,
  ListChecks,
  Maximize2,
  Monitor,
  MoreHorizontal,
  Move,
  Paintbrush,
  PaintBucket,
  Palette,
  RotateCw,
  Settings2,
  Shapes,
  Sparkles,
  Square,
  Scaling,
  SwatchBook,
  Table,
  Tag,
  Type,
  Wrench,
} from "lucide-react";

/**
 * Ícones do botão colapsado da ribbon (estilo PowerPoint).
 * Chave = `groupId` estável passado a `DeckRibbonGroup`.
 */
export const DECK_RIBBON_COLLAPSE_ICONS: Readonly<Record<string, LucideIcon>> = {
  /* Inserir */
  "insert-text": Type,
  "insert-media": Image,
  "insert-illustrations": Shapes,
  "insert-data": Database,
  /* Exibir */
  "view-zoom": Maximize2,
  "view-show": Eye,
  /* Tela */
  "slide-current": Monitor,
  "slide-background": Paintbrush,
  "slide-presets": SwatchBook,
  "slide-properties": Settings2,
  "slide-type": LayoutTemplate,
  "slide-tools": Wrench,
  /* Programação */
  "playlist-chrome": Clapperboard,
  "playlist-rotation": RotateCw,
  "playlist-link": Link,
  "playlist-master": Layers,
  /* Elemento — tipografia */
  "typo-font": Type,
  "typo-effects": Sparkles,
  "typo-paragraph": AlignLeft,
  "typo-style": Baseline,
  /* Elemento — forma / frame / ações */
  "shape-forma": Square,
  "shape-marker": Circle,
  "shape-forms-gallery": Shapes,
  "shape-icon": Sparkles,
  "shape-corner": Circle,
  "shape-adjustments": Move,
  "frame-size": Move,
  "organize-layers": Layers,
  organize: Layers,
  "element-actions": MoreHorizontal,
  "media-section": Image,
  "appearance-display": Eye,
  "data-source-hint": Database,
  "canvas-table": Table,
  "part-nav": ArrowLeft,
  /* Design tabela */
  "table-style-options": ListChecks,
  "table-styles": Table,
  "table-shading": PaintBucket,
  "table-borders": Grid3x3,
  "table-effects": Sparkles,
  "table-forma": Square,
  "table-data": Database,
  /* Layout tabela */
  "table-layout-data": Table,
  "table-layout-align": AlignLeft,
  "table-layout-size": Scaling,
  /* Design gráfico */
  "chart-layout": LayoutTemplate,
  "chart-type": BarChart3,
  "chart-labels": Tag,
  "chart-axes": BarChart3,
  "chart-styles": Palette,
  "chart-data": Database,
  "chart-series": LineChart,
};

export function resolveDeckRibbonCollapseIcon(
  groupId: string | undefined,
  override?: LucideIcon,
): LucideIcon | undefined {
  if (override) return override;
  if (!groupId) return undefined;
  return DECK_RIBBON_COLLAPSE_ICONS[groupId];
}
