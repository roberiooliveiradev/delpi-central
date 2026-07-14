import type {
  ComunicadoBlock,
  ComunicadoDataFilters,
  ComunicadoInputBlock,
  ComunicadoInputTargetScope,
} from "./comunicadoTypes";
import { isFetchableDataBlockType } from "./comunicadoDataArchitecture";

export type InputParamSchemaField = {
  type?: string;
  label?: string;
  description?: string;
  default?: string | number | boolean;
  optional?: boolean;
  enum?: Array<string | number | boolean>;
  format?: string;
};

export type InputParamSchema = Record<string, InputParamSchemaField>;

export type InputFilterContributions = {
  slide: ComunicadoDataFilters;
  bySourceId: Record<string, ComunicadoDataFilters>;
};

export function isInputBlockType(type: string): type is "input" {
  return type === "input";
}

export function isComunicadoInputBlock(block: ComunicadoBlock): block is ComunicadoInputBlock {
  return block.type === "input";
}

export function resolveInputTargetScope(
  input: ComunicadoInputBlock["input"] | undefined,
): ComunicadoInputTargetScope {
  return input?.targetScope === "sources" ? "sources" : "slide";
}

/** Interseção das chaves de vários paramSchema. */
export function intersectParamSchemaKeys(schemas: InputParamSchema[]): string[] {
  if (schemas.length === 0) return [];
  let keys = new Set(Object.keys(schemas[0] ?? {}));
  for (let index = 1; index < schemas.length; index += 1) {
    const next = new Set(Object.keys(schemas[index] ?? {}));
    keys = new Set([...keys].filter((key) => next.has(key)));
  }
  return [...keys].sort();
}

/**
 * Campo do schema para paramKey se existir em todos os schemas alvo.
 * Schema resultante usa o primeiro campo encontrado (labels podem divergir).
 */
export function resolveInputParamSchemaField(
  paramKey: string,
  schemas: InputParamSchema[],
): InputParamSchemaField | null {
  const key = paramKey.trim();
  if (!key || schemas.length === 0) return null;
  if (!intersectParamSchemaKeys(schemas).includes(key)) return null;
  for (const schema of schemas) {
    const field = schema[key];
    if (field && typeof field === "object") return field;
  }
  return null;
}

export function isValueAllowedByParamSchema(
  value: string | number | boolean | null | undefined,
  field: InputParamSchemaField | null,
): boolean {
  if (value === undefined || value === null || value === "") return false;
  if (!field) return false;
  const rawEnum = Array.isArray(field.enum)
    ? field.enum.filter((item) => item !== null && item !== undefined)
    : [];
  if (rawEnum.length > 0) {
    return rawEnum.some((item) => String(item) === String(value));
  }
  if (field.type === "boolean") {
    return typeof value === "boolean" || value === "true" || value === "false";
  }
  if (field.type === "integer" || field.type === "number") {
    return typeof value === "number" ? Number.isFinite(value) : Number.isFinite(Number(value));
  }
  return true;
}

function blockZIndex(block: ComunicadoBlock): number {
  return block.style?.zIndex ?? 1;
}

/**
 * Contribuições dos blocos `input` (e overrides de runtime) para merge canônico.
 * Ordem: zIndex ascendente → último (maior z) vence na mesma chave/escopo.
 */
export function collectInputFilterContributions(
  blocks: ComunicadoBlock[] | undefined | null,
  runtimeOverrides?: InputFilterContributions | null,
  /** Validação opcional: schema por sourceId (e "\0slide" para escopo slide). */
  schemaBySourceId?: Record<string, InputParamSchema> | null,
  slideSchemas?: InputParamSchema[] | null,
): InputFilterContributions {
  const slide: ComunicadoDataFilters = {};
  const bySourceId: Record<string, ComunicadoDataFilters> = {};

  const inputs = (blocks ?? [])
    .filter(isComunicadoInputBlock)
    .slice()
    .sort((a, b) => blockZIndex(a) - blockZIndex(b) || a.id.localeCompare(b.id));

  const applyValue = (
    target: ComunicadoDataFilters,
    paramKey: string,
    value: string | number | boolean | null | undefined,
    field: InputParamSchemaField | null,
  ) => {
    if (!isValueAllowedByParamSchema(value, field) && field !== null) return;
    if (value === undefined || value === null || value === "") return;
    // Sem schema (validação desligada): aceita valor não vazio.
    if (field === null && schemaBySourceId == null && slideSchemas == null) {
      target[paramKey] = value;
      return;
    }
    if (field && isValueAllowedByParamSchema(value, field)) {
      target[paramKey] = value;
    }
  };

  for (const block of inputs) {
    const paramKey = String(block.input?.paramKey || "").trim();
    if (!paramKey) continue;
    const scope = resolveInputTargetScope(block.input);
    const value = block.input?.defaultValue;

    if (scope === "slide") {
      const field =
        slideSchemas && slideSchemas.length > 0
          ? resolveInputParamSchemaField(paramKey, slideSchemas)
          : null;
      const allowWithoutSchema = !slideSchemas || slideSchemas.length === 0;
      if (allowWithoutSchema) {
        if (value !== undefined && value !== null && value !== "") slide[paramKey] = value;
      } else {
        applyValue(slide, paramKey, value, field);
      }
      continue;
    }

    const ids = (block.input?.targetSourceIds ?? [])
      .map((id) => String(id || "").trim())
      .filter(Boolean);
    for (const sourceId of ids) {
      if (!bySourceId[sourceId]) bySourceId[sourceId] = {};
      const schema = schemaBySourceId?.[sourceId];
      const field = schema ? resolveInputParamSchemaField(paramKey, [schema]) : null;
      const allowWithoutSchema = schemaBySourceId == null;
      if (allowWithoutSchema) {
        if (value !== undefined && value !== null && value !== "") {
          bySourceId[sourceId][paramKey] = value;
        }
      } else {
        applyValue(bySourceId[sourceId], paramKey, value, field);
      }
    }
  }

  // Runtime overrides (kiosk) — mesma validação quando schemas fornecidos.
  if (runtimeOverrides?.slide) {
    for (const [key, value] of Object.entries(runtimeOverrides.slide)) {
      const field =
        slideSchemas && slideSchemas.length > 0
          ? resolveInputParamSchemaField(key, slideSchemas)
          : null;
      if (!slideSchemas || slideSchemas.length === 0) {
        if (value !== undefined && value !== null && value !== "") slide[key] = value;
      } else {
        applyValue(slide, key, value, field);
      }
    }
  }
  if (runtimeOverrides?.bySourceId) {
    for (const [sourceId, params] of Object.entries(runtimeOverrides.bySourceId)) {
      if (!params || typeof params !== "object") continue;
      if (!bySourceId[sourceId]) bySourceId[sourceId] = {};
      for (const [key, value] of Object.entries(params)) {
        const schema = schemaBySourceId?.[sourceId];
        const field = schema ? resolveInputParamSchemaField(key, [schema]) : null;
        if (schemaBySourceId == null) {
          if (value !== undefined && value !== null && value !== "") {
            bySourceId[sourceId][key] = value;
          }
        } else {
          applyValue(bySourceId[sourceId], key, value, field);
        }
      }
    }
  }

  return { slide, bySourceId };
}

/** Ids fetchable no slide (para multi-select de alvo). */
export function listFetchableSourceIds(blocks: ComunicadoBlock[] | undefined | null): string[] {
  return (blocks ?? [])
    .filter((block) => isFetchableDataBlockType(block.type))
    .map((block) => block.id);
}

/** Merge shallow de filtros (direita ganha). */
export function mergeFilterLayers(
  ...layers: Array<ComunicadoDataFilters | undefined | null>
): ComunicadoDataFilters {
  const merged: ComunicadoDataFilters = {};
  for (const layer of layers) {
    if (!layer || typeof layer !== "object") continue;
    for (const [key, value] of Object.entries(layer)) {
      if (value === undefined || value === null || value === "") continue;
      merged[key] = value;
    }
  }
  return merged;
}

export function emptyInputFilterContributions(): InputFilterContributions {
  return { slide: {}, bySourceId: {} };
}

/** Atualiza overrides de sessão ao mudar um bloco `input` no kiosk/prévia. */
export function applyRuntimeInputValue(
  contributions: InputFilterContributions,
  block: ComunicadoInputBlock,
  value: string | number | boolean | null,
): InputFilterContributions {
  const paramKey = String(block.input?.paramKey || "").trim();
  if (!paramKey) return contributions;
  const clear = value === undefined || value === null || value === "";
  const nextSlide = { ...(contributions.slide ?? {}) };
  const nextBySource: Record<string, ComunicadoDataFilters> = {};
  for (const [sourceId, params] of Object.entries(contributions.bySourceId ?? {})) {
    nextBySource[sourceId] = { ...params };
  }

  if (resolveInputTargetScope(block.input) === "slide") {
    if (clear) delete nextSlide[paramKey];
    else nextSlide[paramKey] = value;
    return { slide: nextSlide, bySourceId: nextBySource };
  }

  for (const sourceId of (block.input?.targetSourceIds ?? [])
    .map((id) => String(id || "").trim())
    .filter(Boolean)) {
    const bucket = { ...(nextBySource[sourceId] ?? {}) };
    if (clear) delete bucket[paramKey];
    else bucket[paramKey] = value;
    if (Object.keys(bucket).length === 0) delete nextBySource[sourceId];
    else nextBySource[sourceId] = bucket;
  }
  return { slide: nextSlide, bySourceId: nextBySource };
}

export function hasInputFilterContributions(contributions: InputFilterContributions | null | undefined): boolean {
  if (!contributions) return false;
  if (Object.keys(contributions.slide ?? {}).length > 0) return true;
  return Object.values(contributions.bySourceId ?? {}).some(
    (params) => params && Object.keys(params).length > 0,
  );
}

/** Ids fetchable que o input deve refreshar (slide = todos; sources = lista). */
export function resolveInputRefreshSourceIds(
  block: ComunicadoInputBlock | undefined | null,
  blocks: ComunicadoBlock[] | undefined | null,
): string[] {
  if (!block || block.type !== "input") return [];
  if (resolveInputTargetScope(block.input) === "slide") {
    return listFetchableSourceIds(blocks);
  }
  const fetchable = new Set(listFetchableSourceIds(blocks));
  return (block.input?.targetSourceIds ?? [])
    .map((id) => String(id || "").trim())
    .filter((id) => id && fetchable.has(id));
}

/**
 * Ao remover filtros do slide, limpa chaves de `dataFilters` que nenhum input restante mantém.
 */
export function pruneSlideDataFiltersAfterInputRemoval(
  remainingBlocks: ComunicadoBlock[] | undefined | null,
  currentFilters: ComunicadoDataFilters | undefined,
  removedInputs: ComunicadoInputBlock[],
): ComunicadoDataFilters | undefined {
  if (!currentFilters || removedInputs.length === 0) return currentFilters;
  const filters = { ...currentFilters };
  for (const input of removedInputs) {
    if (resolveInputTargetScope(input.input) !== "slide") continue;
    const key = String(input.input?.paramKey || "").trim();
    if (!key || !(key in filters)) continue;
    const stillUsed = (remainingBlocks ?? []).some(
      (block) =>
        isComunicadoInputBlock(block) &&
        resolveInputTargetScope(block.input) === "slide" &&
        String(block.input?.paramKey || "").trim() === key &&
        block.input?.defaultValue !== undefined &&
        block.input?.defaultValue !== null &&
        block.input?.defaultValue !== "",
    );
    if (!stillUsed) delete filters[key];
  }
  return Object.keys(filters).length > 0 ? filters : undefined;
}

/** União dos sourceIds a refreshar para uma lista de filtros removidos. */
export function resolveRemovedInputRefreshSourceIds(
  removedInputs: ComunicadoInputBlock[],
  blocksBeforeRemoval: ComunicadoBlock[] | undefined | null,
): string[] {
  const ids = new Set<string>();
  for (const input of removedInputs) {
    for (const id of resolveInputRefreshSourceIds(input, blocksBeforeRemoval)) {
      ids.add(id);
    }
  }
  return [...ids];
}
