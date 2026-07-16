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
    selectedValueFields: binding.selectedValueFields ?? [],
    maxRows: binding.maxRows,
    refreshSec: binding.refreshSec,
  };
}

type FingerprintBlock = {
  id: string;
  type: string;
  dataBinding: Record<string, unknown>;
  dataTransform?: unknown;
};

function diffChangedFetchableBlockIds(
  prevBlocks: unknown,
  nextBlocks: unknown,
  allFetchableIds: string[],
): string[] {
  const fetchableSet = new Set(allFetchableIds);
  const prevList = (Array.isArray(prevBlocks) ? prevBlocks : []) as FingerprintBlock[];
  const nextList = (Array.isArray(nextBlocks) ? nextBlocks : []) as FingerprintBlock[];
  const prevById = new Map(prevList.map((block) => [block.id, block]));
  const changed: string[] = [];
  for (const block of nextList) {
    if (!block?.id || !fetchableSet.has(block.id)) continue;
    const previous = prevById.get(block.id);
    if (!previous || JSON.stringify(previous) !== JSON.stringify(block)) {
      changed.push(block.id);
    }
  }
  return changed.length > 0 ? changed : allFetchableIds;
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
      dataTransform: block.dataTransform ?? null,
    }));
  const viewLinks = (config.blocks ?? [])
    .filter(
      (block) =>
        block.type === "chart_view" ||
        block.type === "table_view" ||
        block.type === "kpi_view" ||
        ((block.type === "heading" || block.type === "text" || block.type === "shape") &&
          "dataSourceId" in block &&
          block.dataSourceId?.trim()),
    )
    .map((block) => ({
      id: block.id,
      dataSourceId:
        block.type === "chart_view" || block.type === "table_view" || block.type === "kpi_view"
          ? block.dataSourceId
          : "dataSourceId" in block
            ? block.dataSourceId
            : undefined,
      textProjection:
        block.type === "heading" || block.type === "text" || block.type === "shape"
          ? block.textProjection?.field
          : undefined,
    }));
  const inputBlocks = (config.blocks ?? [])
    .filter((block) => block.type === "input")
    .map((block) =>
      block.type === "input"
        ? {
            id: block.id,
            paramKey: block.input?.paramKey ?? "",
            defaultValue: block.input?.defaultValue ?? null,
            targetScope: block.input?.targetScope ?? "slide",
            targetSourceIds: block.input?.targetSourceIds ?? [],
          }
        : null,
    )
    .filter(Boolean);
  return JSON.stringify({
    dataFilters,
    blocks: [...legacyBlocks, ...sourceBlocks],
    viewLinks,
    inputs: inputBlocks,
  });
}

type PreviewFingerprintPayload = {
  dataFilters?: unknown;
  blocks?: unknown;
  viewLinks?: unknown;
  inputs?: unknown;
};

function parsePreviewFingerprint(fingerprint: string): PreviewFingerprintPayload | null {
  try {
    const raw = JSON.parse(fingerprint) as PreviewFingerprintPayload;
    return raw && typeof raw === "object" ? raw : null;
  } catch {
    return null;
  }
}

/**
 * Quais fontes recarregar quando o fingerprint de dados muda.
 * Só vínculo visual (viewLinks) → nenhum refetch (visuais leem resolved da fonte).
 * Binding/transform de fonte → só ids alterados; filtros → fontes afetadas ou todas.
 */
export function resolvePreviewRefreshSourceIds(params: {
  previousFingerprint: string | null;
  nextFingerprint: string;
  allFetchableIds: string[];
  inputAffectedSourceIds: string[];
}): string[] {
  const { previousFingerprint, nextFingerprint, allFetchableIds, inputAffectedSourceIds } = params;
  if (!previousFingerprint || previousFingerprint === nextFingerprint) return [];
  const prev = parsePreviewFingerprint(previousFingerprint);
  const next = parsePreviewFingerprint(nextFingerprint);
  if (!prev || !next) return allFetchableIds;

  const blocksChanged =
    JSON.stringify(prev.blocks ?? null) !== JSON.stringify(next.blocks ?? null);
  const inputsChanged =
    JSON.stringify(prev.inputs ?? null) !== JSON.stringify(next.inputs ?? null);
  const dataFiltersChanged =
    JSON.stringify(prev.dataFilters ?? null) !== JSON.stringify(next.dataFilters ?? null);
  const viewLinksChanged =
    JSON.stringify(prev.viewLinks ?? null) !== JSON.stringify(next.viewLinks ?? null);

  if (!blocksChanged && !inputsChanged && !dataFiltersChanged) {
    return viewLinksChanged ? [] : allFetchableIds;
  }

  if (blocksChanged) {
    return diffChangedFetchableBlockIds(prev.blocks, next.blocks, allFetchableIds);
  }

  if (inputsChanged || dataFiltersChanged) {
    return inputAffectedSourceIds.length > 0 ? inputAffectedSourceIds : allFetchableIds;
  }

  return allFetchableIds;
}

/** @deprecated Use resolvePreviewRefreshSourceIds */
export function resolveStaleSourceIdsForPreviewChange(
  params: Parameters<typeof resolvePreviewRefreshSourceIds>[0],
): string[] {
  return resolvePreviewRefreshSourceIds(params);
}
