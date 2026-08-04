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
  if (presetKey) {
    ctx.presetKey = presetKey;
  }
  return ctx;
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

export type TvCopilotSideEffectHint =
  | "replaceNativeConfig"
  | "refreshFilmstrip"
  | "removeBlockIds"
  | string;

export type TvCopilotPreviewPatchPayload = {
  nativeConfig?: Record<string, unknown> | null;
  diff?: Record<string, unknown> | null;
  ops?: unknown[];
  sideEffects?: Record<string, unknown> | null;
  sideEffectHints?: TvCopilotSideEffectHint[] | null;
};

type TvCopilotHostBridge = {
  onPreviewPatch?: (payload: TvCopilotPreviewPatchPayload) => void;
  onApplyPatchResult?: (payload: {
    ok: boolean;
    persisted?: boolean;
    target?: { playlistId?: string | null; slideId?: string | null };
    sideEffectHints?: TvCopilotSideEffectHint[] | null;
    sideEffects?: Record<string, unknown> | null;
  }) => void;
};

function readHostBridge(): TvCopilotHostBridge | null {
  if (typeof window === "undefined") return null;
  return (
    (window as unknown as { __DELPI_TV_COPILOT_HOST__?: TvCopilotHostBridge })
      .__DELPI_TV_COPILOT_HOST__ ?? null
  );
}

function readObjectField(
  primary: Record<string, unknown>,
  fallback: Record<string, unknown>,
  key: string,
): Record<string, unknown> | null {
  const fromPrimary = primary[key];
  if (fromPrimary && typeof fromPrimary === "object" && !Array.isArray(fromPrimary)) {
    return fromPrimary as Record<string, unknown>;
  }
  const fromFallback = fallback[key];
  if (fromFallback && typeof fromFallback === "object" && !Array.isArray(fromFallback)) {
    return fromFallback as Record<string, unknown>;
  }
  return null;
}

function readHints(
  primary: Record<string, unknown>,
  fallback: Record<string, unknown>,
): TvCopilotSideEffectHint[] {
  return normalizeStringList(primary.sideEffectHints ?? fallback.sideEffectHints);
}

/**
 * Repassa resultado da tool tv_dashboard_copilot ao host TV (preview local / apply).
 * Inclui `sideEffectHints` do BFF para apply genérico no MFE (sem if por op).
 */
export function notifyHostOfTvCopilotToolCalls(
  toolCalls: Array<{
    name?: string;
    arguments?: Record<string, unknown> | null;
    metadata?: Record<string, unknown> | null;
  }>,
): void {
  const bridge = readHostBridge();
  if (!bridge) return;

  for (const call of toolCalls) {
    if (call.name !== "tv_dashboard_copilot") continue;
    const meta = call.metadata && typeof call.metadata === "object" ? call.metadata : {};
    const nested =
      meta.data && typeof meta.data === "object"
        ? (meta.data as Record<string, unknown>)
        : null;
    const data = nested ?? meta;
    const mode = String(
      (call.arguments && call.arguments.mode) || meta.mode || "preview",
    ).toLowerCase();
    const ok = meta.ok !== false && meta.blocked !== true;

    const sideEffects = readObjectField(data, meta, "sideEffects");
    const sideEffectHints = readHints(data, meta);

    if (mode === "apply") {
      bridge.onApplyPatchResult?.({
        ok,
        persisted: Boolean(data.persisted ?? meta.persisted),
        target:
          (data.target && typeof data.target === "object"
            ? (data.target as { playlistId?: string | null; slideId?: string | null })
            : undefined) ??
          (meta.target && typeof meta.target === "object"
            ? (meta.target as { playlistId?: string | null; slideId?: string | null })
            : undefined),
        sideEffectHints,
        sideEffects,
      });
      continue;
    }

    let nativeConfig =
      data.nativeConfig && typeof data.nativeConfig === "object"
        ? (data.nativeConfig as Record<string, unknown>)
        : null;
    if (!nativeConfig && sideEffects?.slides && Array.isArray(sideEffects.slides)) {
      const first = sideEffects.slides[0];
      if (first && typeof first === "object" && "nativeConfig" in first) {
        const nc = (first as { nativeConfig?: unknown }).nativeConfig;
        if (nc && typeof nc === "object") {
          nativeConfig = nc as Record<string, unknown>;
        }
      }
    }

    bridge.onPreviewPatch?.({
      nativeConfig,
      diff: data.diff && typeof data.diff === "object" ? (data.diff as Record<string, unknown>) : null,
      ops: Array.isArray(call.arguments?.ops) ? (call.arguments?.ops as unknown[]) : undefined,
      sideEffects,
      sideEffectHints,
    });
  }
}
