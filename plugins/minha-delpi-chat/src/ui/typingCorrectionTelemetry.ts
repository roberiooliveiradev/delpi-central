import { recordAssistantHelpEvent } from "../data/api/chatApi";

/** Telemetria leve Playbook 14 — best-effort, não bloqueia UX. */
export function recordTypingCorrectionTelemetry(
  event:
    | "typing_correction_offered"
    | "typing_correction_accepted"
    | "typing_correction_dismissed",
  metadata?: Record<string, unknown>,
): void {
  void recordAssistantHelpEvent({
    event,
    metadata: metadata ?? null,
  }).catch(() => {
    /* ignora falha de rede/auth */
  });
}
