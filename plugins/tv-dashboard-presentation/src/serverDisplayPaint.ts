import type {
  ComunicadoContentRun,
  ComunicadoDataResolved,
} from "./comunicadoTypes";

/**
 * Enrich emitiu strings prontas (`display*` / `serverDisplayApplied`).
 * Path de paint do slide deve preferi-las e não chamar `formatDisplayValue`.
 *
 * Gate E5: `serverDisplayPaint.test.ts` + `textViewProjection.test.ts`
 * (serverDisplayApplied) documentam o contrato paint-only.
 */
/**
 * PAINT-only gate (G32): true when enrich stamped display* / serverDisplayApplied
 * and presentation is not stale. Does not perform formatting or projection.
 */
export function hasServerDisplayPaint(
  resolved?: ComunicadoDataResolved | null,
): boolean {
  if (!resolved) return false;
  if (resolved.presentationStale === true) return false;
  if (resolved.serverDisplayApplied === true) return true;
  if (typeof resolved.displayText === "string") return true;
  if (Array.isArray(resolved.displayRuns) && resolved.displayRuns.length > 0) return true;
  if (typeof resolved.kpi?.displayValue === "string") return true;
  if (resolved.table?.displayRows?.length) return true;
  return false;
}

/** Runs/texto compostos do enrich para blocos text/heading/shape. */
export function preferServerTextDisplayRuns(
  resolved?: ComunicadoDataResolved | null,
): ComunicadoContentRun[] | null {
  if (!resolved) return null;
  if (resolved.presentationStale === true) return null;
  if (Array.isArray(resolved.displayRuns) && resolved.displayRuns.length > 0) {
    return resolved.displayRuns.map((run) => ({
      ...run,
      text: String(run.text ?? ""),
    }));
  }
  if (typeof resolved.displayText === "string") {
    return [{ text: resolved.displayText }];
  }
  return null;
}

/** Texto de um dataRef já materializado em `displayRuns` (canvas / compat). */
export function preferServerDisplayRunText(
  resolved: ComunicadoDataResolved | undefined,
  field: string,
): string | undefined {
  if (resolved?.presentationStale === true) return undefined;
  const key = field.trim();
  if (!key || !resolved?.displayRuns?.length) return undefined;
  const hit = resolved.displayRuns.find(
    (run) => run.dataRef?.field?.trim() === key,
  );
  return hit && typeof hit.text === "string" ? hit.text : undefined;
}
