import { recordAssistantHelpEvent } from "../../data/api/chatApi";

/** Telemetria leve Playbook 09 Fase 6 — best-effort, não bloqueia UX. */
export function recordPresentationTelemetry(
  event: string,
  metadata?: Record<string, unknown>,
): void {
  void recordAssistantHelpEvent({
    event,
    metadata: metadata ?? null,
  }).catch(() => {
    /* ignora falha de rede/auth */
  });
}
