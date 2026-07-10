import { isDataBlockType } from "./comunicadoHelpers";
import type { ComunicadoConfig, ComunicadoDataBinding, ComunicadoDataBlock } from "./comunicadoTypes";

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
  const blocks = (config.blocks ?? [])
    .filter((block): block is ComunicadoDataBlock => isDataBlockType(block.type))
    .map((block) => ({
      id: block.id,
      type: block.type,
      dataBinding: serializeBindingForFingerprint(block.dataBinding),
    }));
  return JSON.stringify({ dataFilters, blocks });
}
