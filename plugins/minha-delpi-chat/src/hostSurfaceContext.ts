/**
 * Contrato ambient de host embutido (surface + bindings).
 * Espelha ChatHostSurfaceContextService na API — o host declara o app;
 * o usuário não precisa repetir «estou no TV Dashboard».
 */

export type ChatHostSurface = "tv-dashboard" | string;

export type ChatHostContext = {
  surface: ChatHostSurface;
  playlistId?: string | null;
  slideId?: string | null;
  /** Blocos selecionados no editor do host (foco operacional). */
  selectedBlockIds?: string[];
  /** Tipos dos blocos selecionados (resumo opcional do foco). */
  selectedBlockTypes?: string[];
  /** Primeiro bloco em foco (id). */
  focusBlockId?: string | null;
  /** Tipo do primeiro bloco em foco. */
  focusBlockType?: string | null;
  /** operationId da fonte em foco / primeira fonte do slide. */
  operationId?: string | null;
  /** Id do bloco data_source em foco. */
  dataSourceId?: string | null;
  selectedDataSourceId?: string | null;
  selectedVisualId?: string | null;
  dataSources?: Array<{ id: string; operationId: string; label: string }>;
  /** Há draft local ainda não sincronizado com o BFF. */
  hasLocalDraft?: boolean;
  /** Preset do slide, quando o host souber. */
  presetKey?: string | null;
};

export function buildTvDashboardHostContext(input: {
  playlistId?: string | null;
  slideId?: string | null;
  surface?: ChatHostSurface;
  selectedBlockIds?: string[] | null;
  selectedBlockTypes?: string[] | null;
  focusBlockId?: string | null;
  focusBlockType?: string | null;
  operationId?: string | null;
  dataSourceId?: string | null;
  selectedDataSourceId?: string | null;
  selectedVisualId?: string | null;
  dataSources?: Array<{ id?: string; operationId?: string; label?: string }> | null;
  hasLocalDraft?: boolean;
  presetKey?: string | null;
}): ChatHostContext {
  const selectedBlockIds = normalizeStringList(input.selectedBlockIds);
  const selectedBlockTypes = normalizeStringList(input.selectedBlockTypes);
  const focusBlockId =
    (input.focusBlockId && String(input.focusBlockId).trim()) ||
    selectedBlockIds[0] ||
    null;
  const focusBlockType =
    (input.focusBlockType && String(input.focusBlockType).trim()) ||
    selectedBlockTypes[0] ||
    null;
  const operationId = (input.operationId && String(input.operationId).trim()) || null;
  const dataSourceId = (input.dataSourceId && String(input.dataSourceId).trim()) || null;
  const selectedDataSourceId =
    (input.selectedDataSourceId && String(input.selectedDataSourceId).trim()) || null;
  const selectedVisualId =
    (input.selectedVisualId && String(input.selectedVisualId).trim()) || null;
  const presetKey = (input.presetKey && String(input.presetKey).trim()) || null;

  const ctx: ChatHostContext = {
    surface: input.surface || "tv-dashboard",
    playlistId: input.playlistId ?? null,
    slideId: input.slideId ?? null,
  };
  if (selectedBlockIds.length > 0) {
    ctx.selectedBlockIds = selectedBlockIds;
  }
  if (selectedBlockTypes.length > 0) {
    ctx.selectedBlockTypes = selectedBlockTypes;
  }
  if (focusBlockId) {
    ctx.focusBlockId = focusBlockId;
  }
  if (focusBlockType) {
    ctx.focusBlockType = focusBlockType;
  }
  if (operationId) {
    ctx.operationId = operationId;
  }
  if (dataSourceId) {
    ctx.dataSourceId = dataSourceId;
  }
  if (selectedDataSourceId) {
    ctx.selectedDataSourceId = selectedDataSourceId;
  }
  if (selectedVisualId) {
    ctx.selectedVisualId = selectedVisualId;
  }
  const dataSources = normalizeDataSources(input.dataSources);
  if (dataSources.length > 0) {
    ctx.dataSources = dataSources;
  }
  if (input.hasLocalDraft) {
    ctx.hasLocalDraft = true;
  }
  if (presetKey) {
    ctx.presetKey = presetKey;
  }
  return ctx;
}

function normalizeDataSources(
  value: Array<{ id?: string; operationId?: string; label?: string }> | null | undefined,
): Array<{ id: string; operationId: string; label: string }> {
  if (!Array.isArray(value)) return [];
  return value.flatMap((item) => {
    const id = String(item?.id ?? "").trim();
    const operationId = String(item?.operationId ?? "").trim();
    if (!id || !operationId) return [];
    return [{ id, operationId, label: String(item?.label ?? "").trim() || operationId }];
  });
}

function normalizeStringList(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  const out: string[] = [];
  const seen = new Set<string>();
  for (const item of value) {
    const text = String(item ?? "").trim();
    if (!text || seen.has(text)) continue;
    seen.add(text);
    out.push(text);
  }
  return out;
}
