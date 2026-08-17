/**
 * Contagem do badge «Minhas tarefas» na topbar: tarefas abertas (não concluídas).
 */

export type MyTasksNavBadgeCounts = {
  open?: number | null;
  overdue?: number | null;
  today?: number | null;
  later?: number | null;
};

/** Prefer `open`; fallback overdue+today+later se a API antiga omitir open. */
export function resolveMyTasksNavBadgeCount(counts: MyTasksNavBadgeCounts | null | undefined): number {
  if (!counts) return 0;
  if (typeof counts.open === "number" && Number.isFinite(counts.open)) {
    return Math.max(0, Math.trunc(counts.open));
  }
  const overdue = typeof counts.overdue === "number" ? counts.overdue : 0;
  const today = typeof counts.today === "number" ? counts.today : 0;
  const later = typeof counts.later === "number" ? counts.later : 0;
  return Math.max(0, Math.trunc(overdue) + Math.trunc(today) + Math.trunc(later));
}
