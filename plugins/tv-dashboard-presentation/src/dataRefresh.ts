import { omitVisualOnlyDataParams } from "./chartWeekendFilter";
import { isComunicadoInputBlock, listFetchableSourceIds, resolveInputRefreshSourceIds } from "./comunicadoInputFilters";
import { isDataBlockType, isDataSourceBlockType } from "./comunicadoHelpers";
import {
  bindingTargetId,
  type ComunicadoBlock,
  type ComunicadoConfig,
  type ComunicadoDataBinding,
  type ComunicadoDataBlock,
  type ComunicadoDataSourceBlock,
  type TvDataModel,
} from "./comunicadoTypes";

export const DATA_REFRESH_SEC_MIN = 30;
export const DATA_REFRESH_SEC_MAX = 3600;
export const DATA_REFRESH_SEC_DEFAULT = 300;

/** Debounce único do auto-refresh do preview (filtros, fontes, inputs). */
export const DATA_PREVIEW_AUTO_REFRESH_DEBOUNCE_MS = 400;

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
    params: omitVisualOnlyDataParams(binding.params ?? {}),
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

/** Definição persistida do DataModel no fingerprint — artefatos de runtime fora. */
function serializeDataModelForFingerprint(model: TvDataModel): Record<string, unknown> {
  return {
    id: model.id,
    label: model.label ?? null,
    primaryInputId: model.primaryInputId,
    inputs: model.inputs.map((input) => ({
      id: input.id,
      operationId: input.operationId,
      label: input.label ?? null,
      queryName: input.queryName ?? null,
      params: omitVisualOnlyDataParams(input.params ?? {}),
      transform: input.transform ?? null,
    })),
    transform: model.transform ?? null,
    fieldLabels: model.fieldLabels ?? null,
  };
}

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
  // Remoções não exigem refetch das fontes restantes.
  return changed;
}

function viewLinkBakeKey(entry: unknown): string {
  if (!entry || typeof entry !== "object") return "";
  const { id: _id, ...rest } = entry as Record<string, unknown>;
  return JSON.stringify(rest);
}

/**
 * Fontes cujo encoding/binding de view mudou (ou ganhou view nova).
 * Excluir um visual NÃO dispara refetch — só intervalo / Atualizar / encoding.
 */
function changedSourceIdsFromViewLinkDiff(
  prevLinks: unknown,
  nextLinks: unknown,
  allFetchableIds: string[],
): string[] {
  const fetchableSet = new Set(allFetchableIds);
  const prevList = Array.isArray(prevLinks) ? prevLinks : [];
  const nextList = Array.isArray(nextLinks) ? nextLinks : [];
  const prevById = new Map<string, unknown>();
  for (const entry of prevList) {
    if (!entry || typeof entry !== "object") continue;
    const id = String((entry as { id?: unknown }).id ?? "").trim();
    if (id) prevById.set(id, entry);
  }
  const affected = new Set<string>();
  for (const entry of nextList) {
    if (!entry || typeof entry !== "object") continue;
    const id = String((entry as { id?: unknown }).id ?? "").trim();
    // Target ativo: modelId vence sobre dataSourceId (contrato DM2).
    const sid = bindingTargetId(entry as { modelId?: unknown; dataSourceId?: unknown });
    if (!sid || !fetchableSet.has(sid)) continue;
    const previous = id ? prevById.get(id) : undefined;
    if (!previous) {
      // View nova ligada ao target — um bake para carimbar linkedResolved.
      affected.add(sid);
      continue;
    }
    if (viewLinkBakeKey(previous) !== viewLinkBakeKey(entry)) {
      affected.add(sid);
    }
  }
  return [...affected];
}

/** Chave estável só com filtros e bindings — mudanças de layout não disparam refetch. */
export function buildDataPreviewFingerprint(
  config: ComunicadoConfig,
  options?: { playlistDefaults?: Record<string, unknown> | null },
): string {
  const dataFilters = omitVisualOnlyDataParams(config.dataFilters ?? {});
  const playlistDefaults = omitVisualOnlyDataParams(options?.playlistDefaults ?? {});
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
        block.type === "canvas_table" ||
        ((block.type === "heading" || block.type === "text" || block.type === "shape") &&
          bindingTargetId(block)),
    )
    .filter((block) => {
      if (block.type === "canvas_table") {
        return Boolean(
          bindingTargetId(block) ||
            block.cells.some((row) =>
              row.some(
                (cell) =>
                  Boolean(cell.dataRef?.field?.trim()) || bindingTargetId(cell),
              ),
            ),
        );
      }
      return true;
    })
    .map((block) => {
      const textProj =
        block.type === "heading" || block.type === "text" || block.type === "shape"
          ? block.textProjection
          : undefined;
      const contentRunRefs =
        block.type === "heading" || block.type === "text" || block.type === "shape"
          ? (block.contentRuns ?? [])
              .map((run) => {
                const field = run.dataRef?.field?.trim();
                if (!field) return null;
                const fmt = run.dataRef?.displayFormat ?? null;
                return `${field}:${run.dataRef?.aggregation ?? "first"}:${JSON.stringify(fmt)}`;
              })
              .filter(Boolean)
          : undefined;
      return {
        id: block.id,
        dataSourceId:
          block.type === "chart_view" ||
          block.type === "table_view" ||
          block.type === "kpi_view" ||
          block.type === "canvas_table"
            ? block.dataSourceId
            : "dataSourceId" in block
              ? block.dataSourceId
              : undefined,
        modelId: "modelId" in block ? block.modelId : undefined,
        // FE-BE-003: encoding + displayFormat — bake server-side exige re-preview.
        textProjection: textProj
          ? {
              field: textProj.field ?? null,
              aggregation: textProj.aggregation ?? null,
              format: textProj.format ?? null,
              displayFormat: textProj.displayFormat ?? null,
              decimalPlaces: textProj.decimalPlaces ?? null,
              prefix: textProj.prefix ?? null,
              suffix: textProj.suffix ?? null,
            }
          : undefined,
        contentRunRefs: contentRunRefs?.length ? contentRunRefs : undefined,
        chartProjection:
          block.type === "chart_view"
            ? {
                categoryField: block.chartProjection?.categoryField ?? null,
                series: (block.chartProjection?.series ?? []).map((s) => ({
                  field: s.field,
                  aggregation: s.aggregation ?? null,
                  label: s.label ?? null,
                })),
                goalField: block.chartProjection?.goalField ?? null,
                maxCategories: block.chartProjection?.maxCategories ?? null,
              }
            : undefined,
        chartDisplay:
          block.type === "chart_view"
            ? {
                displayValueFormat: block.chartOptions?.displayValueFormat ?? null,
                valueFormat: block.chartOptions?.valueFormat ?? null,
                decimalPlaces: block.chartOptions?.decimalPlaces ?? null,
                displayCategoryFormat: block.chartOptions?.displayCategoryFormat ?? null,
                categoryLabelFormat: block.chartOptions?.categoryLabelFormat ?? null,
              }
            : undefined,
        kpiProjection:
          block.type === "kpi_view"
            ? {
                metrics: (block.kpiProjection?.metrics ?? []).map((m) => ({
                  field: m.field,
                  aggregation: m.aggregation ?? null,
                  visible: m.visible !== false,
                  displayFormat: m.displayFormat ?? null,
                  format: m.format ?? null,
                  decimalPlaces: m.decimalPlaces ?? null,
                })),
              }
            : undefined,
        kpiDisplay:
          block.type === "kpi_view"
            ? {
                displayValueFormat: block.kpiOptions?.displayValueFormat ?? null,
                valueFormat: block.kpiOptions?.valueFormat ?? null,
                decimalPlaces: block.kpiOptions?.decimalPlaces ?? null,
              }
            : undefined,
        tableProjection:
          block.type === "table_view"
            ? {
                columns: (block.tableProjection?.columns ?? []).map((c) => ({
                  key: c.key ?? null,
                  visible: c.visible !== false,
                  displayFormat: c.displayFormat ?? null,
                  valueFormat: c.valueFormat ?? null,
                })),
              }
            : undefined,
        tableDisplay:
          block.type === "table_view"
            ? {
                displayValueFormat: block.tableOptions?.displayValueFormat ?? null,
                valueFormat: block.tableOptions?.valueFormat ?? null,
              }
            : undefined,
        canvasCells:
          block.type === "canvas_table"
            ? block.cells.flatMap((row, rowIndex) =>
                row
                  .map((cell, colIndex) => {
                    if (!cell.dataRef?.field) return null;
                    const src = bindingTargetId(cell) || bindingTargetId(block);
                    const fmt = cell.dataRef.displayFormat ?? cell.displayFormat ?? null;
                    return `${rowIndex}:${colIndex}:${src}:${cell.dataRef.field}:${JSON.stringify(fmt)}`;
                  })
                  .filter(Boolean),
              )
            : undefined,
      };
    });
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
            ...(block.input?.binding
              ? { binding: block.input.binding, valueSchema: block.input.valueSchema ?? null }
              : {}),
          }
        : null,
    )
    .filter(Boolean);
  const dataModels = (config.dataModels ?? []).map(serializeDataModelForFingerprint);
  return JSON.stringify({
    dataFilters,
    playlistDefaults,
    blocks: [...legacyBlocks, ...sourceBlocks],
    viewLinks,
    inputs: inputBlocks,
    dataModels,
  });
}

type PreviewFingerprintPayload = {
  dataFilters?: unknown;
  playlistDefaults?: unknown;
  blocks?: unknown;
  viewLinks?: unknown;
  inputs?: unknown;
  dataModels?: unknown;
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
 * FE-BE-003: mudança de encoding/binding de view exige re-preview da fonte ligada.
 * Add/delete puro de visual NÃO refetcha todas as fontes — só a afetada (view nova)
 * ou nenhuma (exclusão). Filtros → todas; binding → só ids alterados.
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
  const playlistDefaultsChanged =
    JSON.stringify(prev.playlistDefaults ?? null) !==
    JSON.stringify(next.playlistDefaults ?? null);
  const viewLinksChanged =
    JSON.stringify(prev.viewLinks ?? null) !== JSON.stringify(next.viewLinks ?? null);

  // Filtros do slide / programação aplicam a todas as fontes fetchable.
  if (dataFiltersChanged || playlistDefaultsChanged) {
    return allFetchableIds;
  }

  const ids = new Set<string>();

  if (blocksChanged) {
    for (const id of diffChangedFetchableBlockIds(
      prev.blocks,
      next.blocks,
      allFetchableIds,
    )) {
      ids.add(id);
    }
  }

  if (viewLinksChanged) {
    for (const id of changedSourceIdsFromViewLinkDiff(
      prev.viewLinks,
      next.viewLinks,
      allFetchableIds,
    )) {
      ids.add(id);
    }
  }

  if (inputsChanged) {
    if (inputAffectedSourceIds.length > 0) {
      for (const id of inputAffectedSourceIds) {
        if (allFetchableIds.includes(id)) ids.add(id);
      }
    } else {
      return allFetchableIds;
    }
  }

  return [...ids];
}

function variableInputsFromFingerprint(inputs: unknown): unknown[] {
  if (!Array.isArray(inputs)) return [];
  return inputs.filter(
    (entry) => entry && typeof entry === "object" && "binding" in (entry as Record<string, unknown>),
  );
}

/** Modelos cuja definição persistida mudou entre fingerprints. */
function diffChangedDataModelIds(
  prevModels: unknown,
  nextModels: unknown,
  allModelIds: string[],
): string[] {
  const modelSet = new Set(allModelIds);
  const prevList = (Array.isArray(prevModels) ? prevModels : []) as Array<{
    id?: unknown;
  }>;
  const nextList = (Array.isArray(nextModels) ? nextModels : []) as Array<{
    id?: unknown;
  }>;
  const prevById = new Map(
    prevList
      .map((model) => [String(model?.id ?? "").trim(), model] as const)
      .filter(([id]) => id),
  );
  const changed: string[] = [];
  for (const model of nextList) {
    const id = String(model?.id ?? "").trim();
    if (!id || !modelSet.has(id)) continue;
    const previous = prevById.get(id);
    if (!previous || JSON.stringify(previous) !== JSON.stringify(model)) {
      changed.push(id);
    }
  }
  return changed;
}

/**
 * Quais DataModels recarregar quando o fingerprint muda.
 * Espelho de `resolvePreviewRefreshSourceIds` para `dataModels[]`:
 * filtros do slide → todos; definição alterada/nova → id afetado;
 * view link de model-bound visual → id afetado (bake de linkedResolved).
 */
export function resolvePreviewRefreshModelIds(params: {
  previousFingerprint: string | null;
  nextFingerprint: string;
  allModelIds: string[];
}): string[] {
  const { previousFingerprint, nextFingerprint, allModelIds } = params;
  if (allModelIds.length === 0) return [];
  if (!previousFingerprint || previousFingerprint === nextFingerprint) return [];
  const prev = parsePreviewFingerprint(previousFingerprint);
  const next = parsePreviewFingerprint(nextFingerprint);
  if (!prev || !next) return allModelIds;

  const modelSet = new Set(allModelIds);
  const dataFiltersChanged =
    JSON.stringify(prev.dataFilters ?? null) !== JSON.stringify(next.dataFilters ?? null);
  const playlistDefaultsChanged =
    JSON.stringify(prev.playlistDefaults ?? null) !==
    JSON.stringify(next.playlistDefaults ?? null);
  // Variáveis `input.*` do slide alcançam qualquer DataModel (ExpressionSpec nos inputs).
  if (
    dataFiltersChanged ||
    playlistDefaultsChanged ||
    JSON.stringify(variableInputsFromFingerprint(prev.inputs)) !==
      JSON.stringify(variableInputsFromFingerprint(next.inputs))
  ) {
    return allModelIds;
  }

  const ids = new Set<string>();

  if (JSON.stringify(prev.dataModels ?? null) !== JSON.stringify(next.dataModels ?? null)) {
    for (const id of diffChangedDataModelIds(prev.dataModels, next.dataModels, allModelIds)) {
      ids.add(id);
    }
  }

  if (JSON.stringify(prev.viewLinks ?? null) !== JSON.stringify(next.viewLinks ?? null)) {
    for (const id of changedSourceIdsFromViewLinkDiff(
      prev.viewLinks,
      next.viewLinks,
      allModelIds,
    )) {
      if (modelSet.has(id)) ids.add(id);
    }
  }

  return [...ids];
}

/**
 * Plano canônico de refresh de preview de DataModels — único ponto de decisão
 * para `preview_data_model`. Espelha `planDataPreviewRefresh`.
 */
export function planDataModelPreviewRefresh(params: {
  previousFingerprint: string | null;
  nextFingerprint: string;
  dataModels: TvDataModel[] | undefined | null;
}): string[] {
  const allModelIds = (params.dataModels ?? []).map((model) => model.id).filter(Boolean);
  if (allModelIds.length === 0) return [];
  return resolvePreviewRefreshModelIds({
    previousFingerprint: params.previousFingerprint,
    nextFingerprint: params.nextFingerprint,
    allModelIds,
  });
}

/**
 * Plano canônico de refresh do preview: fingerprint → quais fontes refetchar.
 * Único ponto de decisão (slide/programação/input/binding) — o editor só agenda o fetch.
 */
export function planDataPreviewRefresh(params: {
  previousFingerprint: string | null;
  nextFingerprint: string;
  blocks: ComunicadoBlock[] | undefined | null;
}): string[] {
  const allFetchableIds = listFetchableSourceIds(params.blocks);
  if (allFetchableIds.length === 0) return [];
  const inputAffected = new Set<string>();
  for (const block of params.blocks ?? []) {
    if (!isComunicadoInputBlock(block)) continue;
    for (const id of resolveInputRefreshSourceIds(block, params.blocks)) {
      inputAffected.add(id);
    }
  }
  return resolvePreviewRefreshSourceIds({
    previousFingerprint: params.previousFingerprint,
    nextFingerprint: params.nextFingerprint,
    allFetchableIds,
    inputAffectedSourceIds: [...inputAffected],
  });
}

/** @deprecated Use resolvePreviewRefreshSourceIds */
/**
 * @deprecated G31 — dead for production paint; fingerprint + presentationStale cover preview.
 * Kept for unit tests / migration reference only.
 */
export function resolveStaleSourceIdsForPreviewChange(
  params: Parameters<typeof resolvePreviewRefreshSourceIds>[0],
): string[] {
  return resolvePreviewRefreshSourceIds(params);
}
