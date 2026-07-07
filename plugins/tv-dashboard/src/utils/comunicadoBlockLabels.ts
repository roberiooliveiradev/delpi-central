import { isDataBlockType, type ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

const TYPE_LABELS: Record<string, string> = {
  heading: "Título",
  text: "Texto",
  image: "Imagem",
  video: "Vídeo",
  shape: "Forma",
  data_kpi: "Dados — KPI",
  data_chart: "Dados — Gráfico",
  data_table: "Dados — Tabela",
  data_metric: "Dados",
};

export function comunicadoBlockTypeLabel(type: string): string {
  return TYPE_LABELS[type] ?? type;
}

export function comunicadoBlockSummary(block: ComunicadoBlock): string {
  if (block.type === "heading" || block.type === "text") {
    const text = block.content.trim();
    return text || comunicadoBlockTypeLabel(block.type);
  }
  if (block.type === "shape") {
    return block.content?.trim() || comunicadoBlockTypeLabel(block.type);
  }
  if (isDataBlockType(block.type) && "dataBinding" in block) {
    return block.dataBinding.label ?? block.dataBinding.operationId;
  }
  return comunicadoBlockTypeLabel(block.type);
}
