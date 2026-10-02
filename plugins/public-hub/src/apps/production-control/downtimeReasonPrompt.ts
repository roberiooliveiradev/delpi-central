/** Parada com motivo já gravado — não deve reabrir o seletor sozinha. */
export type DowntimeReasonSnapshot = {
  id: string;
  confirmed?: boolean;
  reasonCode?: string | null;
  reasonLabel?: string | null;
  endedAt?: string | null;
};

/**
 * Motivo informado: confirmação explícita ou código/rótulo já persistido.
 * `confirmed` sozinho pode oscilar num snapshot atrasado; o rótulo não.
 */
export function isDowntimeReasonInformed(
  downtime: DowntimeReasonSnapshot | null | undefined,
): boolean {
  if (!downtime) return false;
  if (downtime.confirmed) return true;
  return Boolean(downtime.reasonCode?.trim() || downtime.reasonLabel?.trim());
}

/**
 * Alvo do modal automático.
 *
 * A parada em registro tem prioridade. Se ela já tem motivo, nenhuma pendência
 * antiga reabre o seletor em cima dela. Sem parada aberta, a pendência
 * encerrada sem motivo continua pedindo classificação (sobrevive a F5).
 */
export function resolveDowntimeReasonPrompt<T extends DowntimeReasonSnapshot>(
  openDowntime: T | null | undefined,
  pendingDowntime: T | null | undefined,
): T | null {
  if (openDowntime) {
    return isDowntimeReasonInformed(openDowntime) ? null : openDowntime;
  }
  if (pendingDowntime && !isDowntimeReasonInformed(pendingDowntime)) {
    return pendingDowntime;
  }
  return null;
}
