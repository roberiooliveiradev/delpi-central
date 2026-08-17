/**
 * Apply genérico de sideEffectHints do Copiloto TV (BFF).
 * Sem `if (op === 'add_slide_from_preset')` — novas ops só declaram hints no catálogo.
 */

export type TvCopilotSideEffectHint =
  | "replaceNativeConfig"
  | "refreshFilmstrip"
  | "removeBlockIds"
  | string;

export type TvCopilotSideEffectPayload = {
  nativeConfig?: Record<string, unknown> | null;
  sideEffects?: Record<string, unknown> | null;
  sideEffectHints?: TvCopilotSideEffectHint[] | null;
};

export type TvCopilotSideEffectPlan = {
  hints: TvCopilotSideEffectHint[];
  nativeConfig: Record<string, unknown> | null;
  removeBlockIds: string[];
  refreshFilmstrip: boolean;
  replaceNativeConfig: boolean;
};

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

function resolveNativeConfigFromPayload(
  payload: TvCopilotSideEffectPayload,
): Record<string, unknown> | null {
  if (payload.nativeConfig && typeof payload.nativeConfig === "object") {
    return payload.nativeConfig;
  }
  const slides = payload.sideEffects?.slides;
  if (!Array.isArray(slides) || slides.length === 0) return null;
  const first = slides[0];
  if (!first || typeof first !== "object") return null;
  const nc = (first as { nativeConfig?: unknown }).nativeConfig;
  return nc && typeof nc === "object" ? (nc as Record<string, unknown>) : null;
}

/**
 * Interpreta o envelope BFF (hints + sideEffects + nativeConfig) de forma genérica.
 */
export function planTvCopilotSideEffects(
  payload: TvCopilotSideEffectPayload,
): TvCopilotSideEffectPlan {
  const sideEffects =
    payload.sideEffects && typeof payload.sideEffects === "object"
      ? payload.sideEffects
      : null;
  const nativeConfig = resolveNativeConfigFromPayload(payload);
  const removeBlockIds = normalizeStringList(
    sideEffects?.removedBlockIds ?? sideEffects?.removeBlockIds,
  );

  const declared = normalizeStringList(payload.sideEffectHints);
  const hints: TvCopilotSideEffectHint[] =
    declared.length > 0
      ? declared
      : [
          ...(nativeConfig ? (["replaceNativeConfig"] as const) : []),
          ...(removeBlockIds.length > 0 ? (["removeBlockIds"] as const) : []),
          ...(Array.isArray(sideEffects?.slides) &&
          sideEffects.slides.length > 0 &&
          !nativeConfig
            ? (["refreshFilmstrip"] as const)
            : []),
        ];

  const replaceNativeConfig =
    hints.includes("replaceNativeConfig") || Boolean(nativeConfig);
  const refreshFilmstrip = hints.includes("refreshFilmstrip");
  const wantsRemove =
    hints.includes("removeBlockIds") ||
    (!replaceNativeConfig && removeBlockIds.length > 0);

  return {
    hints,
    nativeConfig: replaceNativeConfig ? nativeConfig : null,
    removeBlockIds: wantsRemove ? removeBlockIds : [],
    refreshFilmstrip,
    replaceNativeConfig,
  };
}

export type TvCopilotSideEffectHandlers = {
  replaceNativeConfig: (nativeConfig: Record<string, unknown>) => boolean;
  removeBlockIds: (ids: string[]) => boolean;
  refreshFilmstrip: () => boolean;
};

export type TvCopilotSideEffectApplyResult = {
  plan: TvCopilotSideEffectPlan;
  appliedReplace: boolean;
  appliedRemove: boolean;
  appliedRefresh: boolean;
  wantsRefreshFilmstrip: boolean;
};

/**
 * Aplica hints no draft local. Preferência: replaceNativeConfig > removeBlockIds.
 * refreshFilmstrip é opcional (preview costuma só sinalizar; apply recarrega).
 */
export function applyTvCopilotPreviewSideEffects(
  payload: TvCopilotSideEffectPayload,
  handlers: TvCopilotSideEffectHandlers,
): TvCopilotSideEffectApplyResult {
  const plan = planTvCopilotSideEffects(payload);
  let appliedReplace = false;
  let appliedRemove = false;
  let appliedRefresh = false;

  if (plan.replaceNativeConfig && plan.nativeConfig) {
    appliedReplace = handlers.replaceNativeConfig(plan.nativeConfig);
  } else if (plan.removeBlockIds.length > 0) {
    appliedRemove = handlers.removeBlockIds(plan.removeBlockIds);
  }

  if (plan.refreshFilmstrip) {
    appliedRefresh = handlers.refreshFilmstrip();
  }

  return {
    plan,
    appliedReplace,
    appliedRemove,
    appliedRefresh,
    wantsRefreshFilmstrip: plan.refreshFilmstrip,
  };
}
