/**
 * Patch esparso de N telas: cada campo só entra no payload se o tipo aceitar.
 * O chamador aplica N PATCH existentes — sem endpoint batch.
 */

import type { Slide } from "../api/tvDashboardApi";

export type SlideHttpPatch = Partial<{
  title: string;
  durationSec: number | null;
  transitionStyle: string | null;
  isActive: boolean;
  externalUrl: string;
  nativeConfig: Record<string, unknown>;
}>;

export type SlideBatchInput = {
  title?: string;
  durationSec?: number | null;
  transitionStyle?: string | null;
  isActive?: boolean;
  externalUrl?: string;
  branch?: string | null;
  periodDays?: number;
  nativeConfig?: Record<string, unknown>;
};

export type SlideBatchSkipReason =
  | "not_custom"
  | "not_native_operational"
  | "not_external"
  | "empty_patch";

export type SlideBatchApplyResult = {
  applied: Array<{ slideId: string; payload: SlideHttpPatch }>;
  skipped: Array<{ slideId: string; reason: SlideBatchSkipReason }>;
};

export function isCustomMessageSlide(slide: Pick<Slide, "nativeScreenKey">): boolean {
  return slide.nativeScreenKey === "custom_message";
}

export function isNativeOperationalSlide(
  slide: Pick<Slide, "slideType" | "nativeScreenKey">,
): boolean {
  return slide.slideType === "native" && !isCustomMessageSlide(slide);
}

export function slideBatchFieldApplicability(slides: readonly Pick<Slide, "slideType" | "nativeScreenKey">[]) {
  return {
    common: slides.length > 0,
    externalUrl: slides.some((slide) => slide.slideType === "external"),
    branch: slides.some(isNativeOperationalSlide),
    nativeConfig: slides.some(isCustomMessageSlide),
  };
}

export function resolveMixedSlideField<T>(
  values: readonly T[],
  equals: (a: T, b: T) => boolean = Object.is,
): { mixed: true } | { mixed: false; value: T | undefined } {
  if (values.length === 0) return { mixed: false, value: undefined };
  const [first, ...rest] = values;
  return rest.every((value) => equals(value, first as T))
    ? { mixed: false, value: first }
    : { mixed: true };
}

function skipReasonFor(
  slide: Pick<Slide, "slideType" | "nativeScreenKey">,
  patch: SlideBatchInput,
): SlideBatchSkipReason {
  const onlyExternal = patch.externalUrl !== undefined && !hasCommonOrNativeFields(patch);
  if (onlyExternal && slide.slideType !== "external") return "not_external";
  const onlyBranch =
    (patch.branch !== undefined || patch.periodDays !== undefined) &&
    patch.nativeConfig === undefined &&
    !hasCommonFields(patch) &&
    patch.externalUrl === undefined;
  if (onlyBranch && !isNativeOperationalSlide(slide)) return "not_native_operational";
  const onlyCustom =
    patch.nativeConfig !== undefined &&
    !hasCommonFields(patch) &&
    patch.externalUrl === undefined &&
    patch.branch === undefined &&
    patch.periodDays === undefined;
  if (onlyCustom && !isCustomMessageSlide(slide)) return "not_custom";
  return "empty_patch";
}

function hasCommonFields(patch: SlideBatchInput): boolean {
  return (
    patch.title !== undefined ||
    patch.durationSec !== undefined ||
    patch.transitionStyle !== undefined ||
    patch.isActive !== undefined
  );
}

function hasCommonOrNativeFields(patch: SlideBatchInput): boolean {
  return (
    hasCommonFields(patch) ||
    patch.branch !== undefined ||
    patch.periodDays !== undefined ||
    patch.nativeConfig !== undefined
  );
}

export function applySlideBatchPatch(
  slides: readonly Slide[],
  patch: SlideBatchInput,
): SlideBatchApplyResult {
  const applied: SlideBatchApplyResult["applied"] = [];
  const skipped: SlideBatchApplyResult["skipped"] = [];

  for (const slide of slides) {
    const payload: SlideHttpPatch = {};
    if (patch.title !== undefined) payload.title = patch.title;
    if (patch.durationSec !== undefined) payload.durationSec = patch.durationSec;
    if (patch.transitionStyle !== undefined) payload.transitionStyle = patch.transitionStyle;
    if (patch.isActive !== undefined) payload.isActive = patch.isActive;

    if (patch.externalUrl !== undefined && slide.slideType === "external") {
      payload.externalUrl = patch.externalUrl;
    }

    const nextNative = { ...(slide.nativeConfig ?? {}) };
    let nativeTouched = false;
    if (isNativeOperationalSlide(slide) && (patch.branch !== undefined || patch.periodDays !== undefined)) {
      if (patch.branch !== undefined) {
        if (patch.branch.trim()) nextNative.branch = patch.branch.trim();
        else delete nextNative.branch;
      }
      if (patch.periodDays !== undefined) nextNative.periodDays = patch.periodDays;
      nativeTouched = true;
    }
    if (isCustomMessageSlide(slide) && patch.nativeConfig !== undefined) {
      Object.assign(nextNative, patch.nativeConfig);
      nativeTouched = true;
    }
    if (nativeTouched) payload.nativeConfig = nextNative;

    if (Object.keys(payload).length === 0) {
      skipped.push({ slideId: slide.id, reason: skipReasonFor(slide, patch) });
    } else {
      applied.push({ slideId: slide.id, payload });
    }
  }

  return { applied, skipped };
}
