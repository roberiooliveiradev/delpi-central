import type {
  ComunicadoBlock,
  ComunicadoDataSourceBlock,
  ComunicadoKpiViewBlock,
  FieldLabelsMap,
  KpiViewProjection,
} from "@delpi/tv-dashboard-presentation";
import { isDataSourceBlockType, patchFieldLabels } from "@delpi/tv-dashboard-presentation";

/**
 * Renomeia métrica/campo no registro da fonte e limpa label assado na projeção KPI.
 */
export function renameKpiMetricFieldLabel(input: {
  blocks: ComunicadoBlock[];
  kpiBlock: ComunicadoKpiViewBlock;
  field: string;
  label: string;
}): {
  sourcePatch?: { id: string; fieldLabels: FieldLabelsMap | undefined };
  kpiProjection?: KpiViewProjection;
} {
  const sourceId = input.kpiBlock.dataSourceId?.trim();
  const source = sourceId
    ? input.blocks.find(
        (block): block is ComunicadoDataSourceBlock =>
          block.id === sourceId && isDataSourceBlockType(block.type),
      )
    : undefined;

  const sourcePatch = source
    ? {
        id: source.id,
        fieldLabels: patchFieldLabels(source.fieldLabels, input.field, input.label),
      }
    : undefined;

  const metrics = input.kpiBlock.kpiProjection?.metrics;
  let kpiProjection = input.kpiBlock.kpiProjection;
  if (metrics?.length) {
    const nextMetrics = metrics.map((metric) =>
      metric.field === input.field ? { ...metric, label: undefined } : metric,
    );
    kpiProjection = { ...input.kpiBlock.kpiProjection, metrics: nextMetrics };
  }

  return { sourcePatch, kpiProjection };
}
