import {
  isDataBlockType,
  isDataSourceBlockType,
  resolveVisualBoxDisplayText,
  textBlockHasDataBinding,
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";

const TYPE_LABELS: Record<string, string> = {
  heading: "Título",
  text: "Texto",
  image: "Imagem",
  video: "Vídeo",
  shape: "Forma",
  icon: "Ícone",
  data_source: "Fonte de dados",
  chart_view: "Gráfico",
  table_view: "Tabela",
  canvas_table: "Grade",
  input: "Campo / Filtro",
  kpi_view: "KPI",
  data_kpi: "Dados — KPI",
  data_chart: "Dados — Gráfico",
  data_table: "Dados — Tabela",
  data_metric: "Dados",
};

export function comunicadoBlockTypeLabel(type: string): string {
  return TYPE_LABELS[type] ?? type;
}

function visualBoxSummaryLabel(block: Extract<ComunicadoBlock, { type: "heading" | "text" | "shape" }>): string {
  if (textBlockHasDataBinding(block)) {
    const display = resolveVisualBoxDisplayText(block, block.resolved);
    const live = display.content?.trim();
    if (live) return live;
  }
  const staticText =
    block.type === "shape" ? block.content?.trim() ?? "" : block.content.trim();
  return staticText || comunicadoBlockTypeLabel(block.type);
}

export function comunicadoBlockSummary(block: ComunicadoBlock): string {
  if (block.type === "heading" || block.type === "text" || block.type === "shape") {
    return visualBoxSummaryLabel(block);
  }
  if (isDataBlockType(block.type) && "dataBinding" in block) {
    return block.dataBinding.label ?? block.dataBinding.operationId;
  }
  if (isDataSourceBlockType(block.type) && "dataBinding" in block) {
    return block.dataBinding.label ?? block.dataBinding.operationId;
  }
  if (block.type === "icon") {
    return block.iconName;
  }
  if (block.type === "input") {
    return block.input?.label?.trim() || block.input?.paramKey || comunicadoBlockTypeLabel(block.type);
  }
  return comunicadoBlockTypeLabel(block.type);
}
