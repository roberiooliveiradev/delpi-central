import type {
  ComunicadoBlock,
  ComunicadoDataSourceBlock,
  ComunicadoTableViewBlock,
  FieldLabelsMap,
  TableViewProjection,
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
 * Renomeia um campo no registro da fonte/modelo ligado ao visual e limpa label
 * assado na projeção da coluna (para a cascata da fonte valer em tempo real).
 */
export function renameTableColumnFieldLabel(input: {
  blocks: ComunicadoBlock[];
  tableBlock: ComunicadoTableViewBlock;
  columnKey: string;
  label: string;
  dataModels?: readonly TvDataModel[] | null;
}): {
  sourcePatch?: { id: string; fieldLabels: FieldLabelsMap | undefined };
  /** Patch em `config.dataModels` quando o binding ativo é `modelId`. */
  modelPatch?: { id: string; fieldLabels: FieldLabelsMap | undefined };
  tableProjection?: TableViewProjection;
} {
  const isModelBound = bindingTargetKind(input.tableBlock) === "model";
  const sourceId = isModelBound ? "" : input.tableBlock.dataSourceId?.trim();
  const source = sourceId
    ? input.blocks.find(
        (block): block is ComunicadoDataSourceBlock =>
          block.id === sourceId && isDataSourceBlockType(block.type),
      )
    : undefined;

  const sourcePatch = source
    ? {
        id: source.id,
        fieldLabels: patchFieldLabels(source.fieldLabels, input.columnKey, input.label),
      }
    : undefined;

  const model = isModelBound
    ? findDataModel(
        { dataModels: [...(input.dataModels ?? [])] },
        bindingTargetId(input.tableBlock),
      )
    : null;
  const modelPatch = model
    ? {
        id: model.id,
        fieldLabels: patchFieldLabels(model.fieldLabels, input.columnKey, input.label),
      }
    : undefined;

  const columns = input.tableBlock.tableProjection?.columns;
  let tableProjection = input.tableBlock.tableProjection;
  if (columns?.length) {
    const nextColumns = columns.map((col) =>
      col.key === input.columnKey ? { ...col, label: undefined } : col,
    );
    tableProjection = { ...input.tableBlock.tableProjection, columns: nextColumns };
  }

  return { sourcePatch, modelPatch, tableProjection };
}
