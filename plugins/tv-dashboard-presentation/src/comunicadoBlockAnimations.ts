import type { CSSProperties } from "react";

import type {
  ComunicadoBlockAnimation,
  ComunicadoBlockAnimationDirection,
  ComunicadoBlockAnimationEasing,
  ComunicadoBlockAnimationKind,
} from "./comunicadoTypes";

export const BLOCK_ENTRANCE_DELAY_MIN_MS = 0;
export const BLOCK_ENTRANCE_DELAY_MAX_MS = 5000;
export const BLOCK_ENTRANCE_DELAY_STEP_MS = 100;
export const BLOCK_ENTRANCE_DURATION_MIN_MS = 200;
export const BLOCK_ENTRANCE_DURATION_MAX_MS = 2000;
export const BLOCK_ENTRANCE_DURATION_STEP_MS = 100;
export const BLOCK_ENTRANCE_DURATION_DEFAULT_MS = 600;

export const BLOCK_ENTRANCE_PRESET_OPTIONS: Array<{ value: string; label: string }> = [
  { value: "none", label: "Nenhuma" },
  { value: "fade", label: "Aparecer (fade)" },
  { value: "slide-in:up", label: "Deslizar de baixo" },
  { value: "slide-in:down", label: "Deslizar de cima" },
  { value: "slide-in:left", label: "Deslizar da direita" },
  { value: "slide-in:right", label: "Deslizar da esquerda" },
];

const EASING_VALUES: ComunicadoBlockAnimationEasing[] = ["ease", "ease-out", "ease-in-out", "linear"];
const DIRECTION_VALUES: ComunicadoBlockAnimationDirection[] = ["up", "down", "left", "right"];

function clampMs(
  value: unknown,
  min: number,
  max: number,
  fallback: number,
): number {
  if (typeof value !== "number" || !Number.isFinite(value)) return fallback;
  return Math.min(max, Math.max(min, Math.round(value)));
}

export function normalizeBlockAnimations(value: unknown): ComunicadoBlockAnimation[] | undefined {
  if (!Array.isArray(value) || value.length === 0) return undefined;
  const normalized: ComunicadoBlockAnimation[] = [];
  for (const raw of value) {
    if (!raw || typeof raw !== "object") continue;
    const item = raw as Record<string, unknown>;
    const phase = item.phase === "entrance" ? "entrance" : null;
    const kind =
      item.kind === "fade" || item.kind === "slide-in"
        ? (item.kind as ComunicadoBlockAnimationKind)
        : null;
    if (!phase || !kind) continue;
    const easing = EASING_VALUES.includes(item.easing as ComunicadoBlockAnimationEasing)
      ? (item.easing as ComunicadoBlockAnimationEasing)
      : "ease-out";
    const direction = DIRECTION_VALUES.includes(item.direction as ComunicadoBlockAnimationDirection)
      ? (item.direction as ComunicadoBlockAnimationDirection)
      : kind === "slide-in"
        ? "up"
        : undefined;
    normalized.push({
      phase: "entrance",
      kind,
      delayMs: clampMs(item.delayMs, BLOCK_ENTRANCE_DELAY_MIN_MS, BLOCK_ENTRANCE_DELAY_MAX_MS, 0),
      durationMs: clampMs(
        item.durationMs,
        BLOCK_ENTRANCE_DURATION_MIN_MS,
        BLOCK_ENTRANCE_DURATION_MAX_MS,
        BLOCK_ENTRANCE_DURATION_DEFAULT_MS,
      ),
      easing,
      ...(direction ? { direction } : {}),
    });
  }
  return normalized.length > 0 ? normalized : undefined;
}

export function serializeBlockAnimations(
  animations: ComunicadoBlockAnimation[] | undefined,
): Array<Record<string, unknown>> | undefined {
  if (!animations?.length) return undefined;
  return animations.map((anim) => {
    const payload: Record<string, unknown> = {
      phase: anim.phase,
      kind: anim.kind,
    };
    if (anim.delayMs != null && anim.delayMs > 0) payload.delayMs = anim.delayMs;
    if (anim.durationMs != null) payload.durationMs = anim.durationMs;
    if (anim.easing && anim.easing !== "ease-out") payload.easing = anim.easing;
    if (anim.direction) payload.direction = anim.direction;
    return payload;
  });
}

export function resolveEntranceAnimation(
  animations: ComunicadoBlockAnimation[] | undefined,
): ComunicadoBlockAnimation | undefined {
  return animations?.find((anim) => anim.phase === "entrance");
}

export function entrancePresetValue(animation: ComunicadoBlockAnimation | undefined): string {
  if (!animation) return "none";
  if (animation.kind === "fade") return "fade";
  const direction = animation.direction ?? "up";
  return `slide-in:${direction}`;
}

export function entranceAnimationFromPreset(
  preset: string,
  options?: { delayMs?: number; durationMs?: number },
): ComunicadoBlockAnimation[] | undefined {
  if (preset === "none" || !preset.trim()) return undefined;
  if (preset === "fade") {
    return [
      {
        phase: "entrance",
        kind: "fade",
        delayMs: options?.delayMs ?? 0,
        durationMs: options?.durationMs ?? BLOCK_ENTRANCE_DURATION_DEFAULT_MS,
        easing: "ease-out",
      },
    ];
  }
  const match = /^slide-in:(up|down|left|right)$/.exec(preset);
  if (!match) return undefined;
  return [
    {
      phase: "entrance",
      kind: "slide-in",
      direction: match[1] as ComunicadoBlockAnimationDirection,
      delayMs: options?.delayMs ?? 0,
      durationMs: options?.durationMs ?? BLOCK_ENTRANCE_DURATION_DEFAULT_MS,
      easing: "ease-out",
    },
  ];
}

export function blockEntranceAnimationClass(
  animations: ComunicadoBlockAnimation[] | undefined,
): string {
  const anim = resolveEntranceAnimation(animations);
  if (!anim) return "";
  if (anim.kind === "fade") return "tdp-comunicado__block--anim-fade";
  const direction = anim.direction ?? "up";
  return `tdp-comunicado__block--anim-slide-in tdp-comunicado__block--anim-slide-in-${direction}`;
}

export function blockEntranceAnimationStyle(
  animations: ComunicadoBlockAnimation[] | undefined,
): CSSProperties {
  const anim = resolveEntranceAnimation(animations);
  if (!anim) return {};
  return {
    ["--tdp-block-anim-delay" as string]: `${anim.delayMs ?? 0}ms`,
    ["--tdp-block-anim-duration" as string]: `${anim.durationMs ?? BLOCK_ENTRANCE_DURATION_DEFAULT_MS}ms`,
    ["--tdp-block-anim-easing" as string]: anim.easing ?? "ease-out",
  };
}
