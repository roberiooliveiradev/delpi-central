import type { MyWegProbableDateShift, MyWegProbableDateShiftKind } from "../types";

export type MyWegProbableShiftFilter = "all" | "advancement" | "postponement";

export type MyWegProductKeyDisplay = {
  label: string;
  identityKind: "verified_code" | "customer_reference" | "unresolved";
  confirmed: boolean;
};

/** Diferença de dias de calendário (to − from), sem deslocamento por timezone local. */
export function calendarDaysBetween(fromIso: string, toIso: string): number | null {
  const from = parseDateOnlyParts(fromIso);
  const to = parseDateOnlyParts(toIso);
  if (!from || !to) return null;
  const fromUtc = Date.UTC(from.y, from.m - 1, from.d);
  const toUtc = Date.UTC(to.y, to.m - 1, to.d);
  return Math.round((toUtc - fromUtc) / 86_400_000);
}

export function parseDateOnlyParts(
  value: string | null | undefined,
): { y: number; m: number; d: number } | null {
  const text = (value ?? "").trim();
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(text);
  if (!match) return null;
  const y = Number(match[1]);
  const m = Number(match[2]);
  const d = Number(match[3]);
  if (!Number.isFinite(y) || !Number.isFinite(m) || !Number.isFinite(d)) return null;
  return { y, m, d };
}

export function formatProductKeyForDisplay(productKey: string): MyWegProductKeyDisplay {
  const key = (productKey ?? "").trim();
  if (key.startsWith("code:")) {
    const label = key.slice("code:".length).trim() || key;
    return { label, identityKind: "verified_code", confirmed: true };
  }
  if (key.startsWith("ref:")) {
    const label = key.slice("ref:".length).trim() || key;
    return { label, identityKind: "customer_reference", confirmed: false };
  }
  if (key.startsWith("informed:")) {
    const label = key.slice("informed:".length).trim() || key;
    return { label, identityKind: "unresolved", confirmed: false };
  }
  if (key.startsWith("unresolved:")) {
    return { label: "Identidade não confirmada", identityKind: "unresolved", confirmed: false };
  }
  return { label: key || "Identidade não confirmada", identityKind: "unresolved", confirmed: false };
}

export function isAdvancementKind(kind: string | null | undefined): boolean {
  return kind === "possible_advancement";
}

export function isPostponementKind(kind: string | null | undefined): boolean {
  return kind === "possible_postponement";
}

export function countProbableShiftKinds(shifts: readonly MyWegProbableDateShift[]): {
  advancements: number;
  postponements: number;
  sameDate: number;
  total: number;
} {
  let advancements = 0;
  let postponements = 0;
  let sameDate = 0;
  for (const shift of shifts) {
    if (isAdvancementKind(shift.kind)) advancements += 1;
    else if (isPostponementKind(shift.kind)) postponements += 1;
    else if (shift.kind === "same_date_redistribution") sameDate += 1;
  }
  return {
    advancements,
    postponements,
    sameDate,
    total: shifts.length,
  };
}

export function filterProbableDateShifts(
  shifts: readonly MyWegProbableDateShift[],
  filter: MyWegProbableShiftFilter,
): MyWegProbableDateShift[] {
  if (filter === "advancement") {
    return shifts.filter((shift) => isAdvancementKind(shift.kind));
  }
  if (filter === "postponement") {
    return shifts.filter((shift) => isPostponementKind(shift.kind));
  }
  return [...shifts];
}

/** Prioriza remessas mais próximas (menor data from/to). */
export function sortProbableDateShiftsByNearestRemessa(
  shifts: readonly MyWegProbableDateShift[],
): MyWegProbableDateShift[] {
  return [...shifts].sort((a, b) => {
    const aKey = nearestRemessaSortKey(a);
    const bKey = nearestRemessaSortKey(b);
    if (aKey !== bKey) return aKey < bKey ? -1 : 1;
    if (a.productKey !== b.productKey) return a.productKey < b.productKey ? -1 : 1;
    if (a.fromRemessa !== b.fromRemessa) return a.fromRemessa < b.fromRemessa ? -1 : 1;
    return a.toRemessa < b.toRemessa ? -1 : a.toRemessa > b.toRemessa ? 1 : 0;
  });
}

function nearestRemessaSortKey(shift: MyWegProbableDateShift): string {
  const from = (shift.fromRemessa ?? "").slice(0, 10);
  const to = (shift.toRemessa ?? "").slice(0, 10);
  if (!from) return to || "9999-99-99";
  if (!to) return from;
  return from < to ? from : to;
}

export function normalizeProbableDateShifts(
  value: unknown,
): MyWegProbableDateShift[] {
  if (!Array.isArray(value)) return [];
  const out: MyWegProbableDateShift[] = [];
  for (const raw of value) {
    if (!raw || typeof raw !== "object") continue;
    const item = raw as Record<string, unknown>;
    const productKey = String(item.productKey ?? "").trim();
    const fromRemessa = String(item.fromRemessa ?? "").trim();
    const toRemessa = String(item.toRemessa ?? "").trim();
    const quantityUn = String(item.quantityUn ?? "").trim();
    const kind = String(item.kind ?? "").trim() as MyWegProbableDateShiftKind | string;
    const confidence = String(item.confidence ?? "").trim() || "probable_not_proven";
    if (!productKey || !fromRemessa || !toRemessa || !quantityUn || !kind) continue;
    out.push({
      productKey,
      fromRemessa,
      toRemessa,
      quantityUn,
      kind: kind as MyWegProbableDateShiftKind,
      confidence,
    });
  }
  return out;
}
