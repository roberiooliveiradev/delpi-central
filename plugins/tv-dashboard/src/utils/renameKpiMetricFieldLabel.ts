import type {
  ComunicadoBlock,
  ComunicadoDataSourceBlock,
  ComunicadoKpiViewBlock,
  FieldLabelsMap,
  KpiViewProjection,
  TvDataModel,
} from "@delpi/tv-dashboard-presentation";
import {
  bindingTargetKind,
  bindingTargetId,
  findDataModel,
  isDataSourceBlockType,
  patchFieldLabels,
} from "@delpi/tv-dashboard-presentation";

/**
 * Renomeia métrica/campo no registro da fonte/modelo ligado e limpa label
 * assado na projeção KPI.
 */
export function renameKpiMetricFieldLabel(input: {
  blocks: ComunicadoBlock[];
  kpiBlock: ComunicadoKpiViewBlock;
  field: string;
  label: string;
  dataModels?: readonly TvDataModel[] | null;
}): {
  sourcePatch?: { id: string; fieldLabels: FieldLabelsMap | undefined };
  /** Patch em `config.dataModels` quando o binding ativo é `modelId`. */
  modelPatch?: { id: string; fieldLabels: FieldLabelsMap | undefined };
  kpiProjection?: KpiViewProjection;
} {
  const isModelBound = bindingTargetKind(input.kpiBlock) === "model";
  const sourceId = isModelBound ? "" : input.kpiBlock.dataSourceId?.trim();
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

  const model = isModelBound
    ? findDataModel(
        { dataModels: [...(input.dataModels ?? [])] },
        bindingTargetId(input.kpiBlock),
      )
    : null;
  const modelPatch = model
    ? {
        id: model.id,
        fieldLabels: patchFieldLabels(model.fieldLabels, input.field, input.label),
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

  return { sourcePatch, modelPatch, kpiProjection };
}
