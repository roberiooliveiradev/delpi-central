import { isDataBlockType, isDataSourceBlockType } from "./comunicadoHelpers";
import type {
  ComunicadoConfig,
  ComunicadoDataBinding,
  ComunicadoDataBlock,
  ComunicadoDataSourceBlock,
} from "./comunicadoTypes";

export const DATA_REFRESH_SEC_MIN = 30;
export const DATA_REFRESH_SEC_MAX = 3600;
export const DATA_REFRESH_SEC_DEFAULT = 300;

/** Intervalo efetivo de um bloco de dados: override do bloco ou padrão da programação. */
export function resolveDataBlockRefreshSec(
  binding: Pick<ComunicadoDataBinding, "refreshSec"> | undefined,
  globalRefreshSec?: number | null,
): number {
  const blockSec = binding?.refreshSec;
  if (
    typeof blockSec === "number" &&
    Number.isFinite(blockSec) &&
    blockSec >= DATA_REFRESH_SEC_MIN &&
    blockSec <= DATA_REFRESH_SEC_MAX
  ) {
    return Math.round(blockSec);
  }
  const globalSec = globalRefreshSec ?? DATA_REFRESH_SEC_DEFAULT;
  if (
    Number.isFinite(globalSec) &&
    globalSec >= DATA_REFRESH_SEC_MIN &&
    globalSec <= DATA_REFRESH_SEC_MAX
  ) {
    return Math.round(globalSec);
  }
  return DATA_REFRESH_SEC_DEFAULT;
}

function serializeBindingForFingerprint(binding: ComunicadoDataBinding): Record<string, unknown> {
  return {
    operationId: binding.operationId,
    params: binding.params ?? {},
    displayMode: binding.displayMode,
    label: binding.label,
    valueField: binding.valueField,
    maxRows: binding.maxRows,
    refreshSec: binding.refreshSec,
  };
}

/** Chave estável só com filtros e bindings — mudanças de layout não disparam refetch. */
export function buildDataPreviewFingerprint(config: ComunicadoConfig): string {
  const dataFilters = config.dataFilters ?? {};
  const legacyBlocks = (config.blocks ?? [])
    .filter((block): block is ComunicadoDataBlock => isDataBlockType(block.type))
    .map((block) => ({
      id: block.id,
      type: block.type,
      dataBinding: serializeBindingForFingerprint(block.dataBinding),
    }));
  const sourceBlocks = (config.blocks ?? [])
    .filter((block): block is ComunicadoDataSourceBlock => isDataSourceBlockType(block.type))
    .map((block) => ({
      id: block.id,
      type: block.type,
      dataBinding: serializeBindingForFingerprint(block.dataBinding),
    }));
  const viewLinks = (config.blocks ?? [])
    .filter((block) => block.type === "chart_view" || block.type === "table_view")
    .map((block) => ({
      id: block.id,
      dataSourceId: block.type === "chart_view" || block.type === "table_view" ? block.dataSourceId : undefined,
    }));
  return JSON.stringify({ dataFilters, blocks: [...legacyBlocks, ...sourceBlocks], viewLinks });
}
