import type { PpcBranch } from "../types";

export const LINE_FEEDER_DEFAULT_HOURS = 3;
export const LINE_FEEDER_MAX_HOURS = 24;

function storageKey(branch: PpcBranch): string {
  return `production-control:line-feeder:hours:v1:${branch}`;
}

function validHours(value: number): boolean {
  return Number.isFinite(value) && value > 0 && value <= LINE_FEEDER_MAX_HOURS;
}

/** Conserva somente a duração, nunca a fotografia operacional da coleta. */
export function readPreferredLineFeederHours(branch: PpcBranch): number {
  try {
    if (typeof window === "undefined") return LINE_FEEDER_DEFAULT_HOURS;
    const stored = window.localStorage.getItem(storageKey(branch));
    if (!stored?.trim()) return LINE_FEEDER_DEFAULT_HOURS;
    const value = Number(stored);
    return validHours(value) ? value : LINE_FEEDER_DEFAULT_HOURS;
  } catch {
    return LINE_FEEDER_DEFAULT_HOURS;
  }
}

export function savePreferredLineFeederHours(branch: PpcBranch, hours: number): void {
  if (!validHours(hours)) return;
  try {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(storageKey(branch), String(hours));
    }
  } catch {
    // Sem storage o campo permanece funcional durante o acesso atual.
  }
}
