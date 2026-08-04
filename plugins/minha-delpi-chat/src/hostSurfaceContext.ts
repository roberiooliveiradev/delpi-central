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
};

export function buildTvDashboardHostContext(input: {
  playlistId?: string | null;
  slideId?: string | null;
  surface?: ChatHostSurface;
}): ChatHostContext {
  return {
    surface: input.surface || "tv-dashboard",
    playlistId: input.playlistId ?? null,
    slideId: input.slideId ?? null,
  };
}

type TvCopilotHostBridge = {
  onPreviewPatch?: (payload: {
    nativeConfig?: Record<string, unknown> | null;
    diff?: Record<string, unknown> | null;
    ops?: unknown[];
    sideEffects?: Record<string, unknown> | null;
  }) => void;
  onApplyPatchResult?: (payload: {
    ok: boolean;
    persisted?: boolean;
    target?: { playlistId?: string | null; slideId?: string | null };
  }) => void;
};

function readHostBridge(): TvCopilotHostBridge | null {
  if (typeof window === "undefined") return null;
  return (
    (window as unknown as { __DELPI_TV_COPILOT_HOST__?: TvCopilotHostBridge })
      .__DELPI_TV_COPILOT_HOST__ ?? null
  );
}

/**
 * Repassa resultado da tool tv_dashboard_copilot ao host TV (preview local / apply).
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

    if (mode === "apply") {
      bridge.onApplyPatchResult?.({
        ok,
        persisted: Boolean(data.persisted ?? meta.persisted),
        target:
          data.target && typeof data.target === "object"
            ? (data.target as { playlistId?: string | null; slideId?: string | null })
            : undefined,
      });
      continue;
    }

    bridge.onPreviewPatch?.({
      nativeConfig:
        data.nativeConfig && typeof data.nativeConfig === "object"
          ? (data.nativeConfig as Record<string, unknown>)
          : null,
      diff: data.diff && typeof data.diff === "object" ? (data.diff as Record<string, unknown>) : null,
      ops: Array.isArray(call.arguments?.ops) ? (call.arguments?.ops as unknown[]) : undefined,
      sideEffects:
        data.sideEffects && typeof data.sideEffects === "object"
          ? (data.sideEffects as Record<string, unknown>)
          : null,
    });
  }
}
