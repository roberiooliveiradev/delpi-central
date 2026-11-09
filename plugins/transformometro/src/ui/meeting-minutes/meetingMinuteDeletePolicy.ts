/** Client-side eligibility for soft-deleting a meeting minute.

Backend remains the authority — this only gates UI affordances.
Draft-only, never sent for signature, no completed signature rows.
*/

export type MeetingMinuteDeleteCandidate = {
  status?: unknown;
  submitted_for_signature_at?: unknown;
  minute_number?: unknown;
  title?: unknown;
  signatures_done?: unknown;
};

export function canDeleteMeetingMinute(
  minute: MeetingMinuteDeleteCandidate | null | undefined,
  signatures: ReadonlyArray<unknown> | null | undefined = [],
): boolean {
  if (!minute) return false;
  if (String(minute.status ?? "") !== "draft") return false;
  if (minute.submitted_for_signature_at != null && minute.submitted_for_signature_at !== "") {
    return false;
  }
  if (Array.isArray(signatures) && signatures.length > 0) return false;
  const done = Number(minute.signatures_done ?? 0);
  if (Number.isFinite(done) && done > 0) return false;
  return true;
}

export function meetingMinuteDeleteConfirmCopy(
  minute: MeetingMinuteDeleteCandidate | null | undefined,
  options?: { discardUnsaved?: boolean },
): { title: string; message: string; confirmLabel: string } {
  const number = String(minute?.minute_number ?? "").trim() || "sem número";
  const title = String(minute?.title ?? "").trim() || "sem título";
  const unsaved = options?.discardUnsaved
    ? " Alterações locais não salvas também serão descartadas."
    : "";
  return {
    title: "Excluir ata?",
    message:
      `Você está prestes a excluir a ata ${number} — ${title}. ` +
      `Esta ação removerá a ata das listagens ativas.${unsaved} Deseja continuar?`,
    confirmLabel: "Excluir ata",
  };
}
