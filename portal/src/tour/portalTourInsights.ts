export function formatExplorationDuration(seconds: number | null): string | null {
  if (seconds == null || seconds < 0) return null;

  const totalMinutes = Math.floor(seconds / 60);
  if (totalMinutes < 1) {
    return "menos de 1 minuto";
  }

  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;

  if (hours <= 0) {
    return minutes === 1 ? "1 minuto" : `${minutes} minutos`;
  }

  if (minutes <= 0) {
    return hours === 1 ? "1 hora" : `${hours} horas`;
  }

  const hourLabel = hours === 1 ? "1 hora" : `${hours} horas`;
  const minuteLabel = minutes === 1 ? "1 minuto" : `${minutes} minutos`;
  return `${hourLabel} e ${minuteLabel}`;
}

export function resolveExplorationDurationSeconds(
  startedAt: string | null | undefined,
  fallbackSeconds: number | null | undefined,
): number | null {
  if (fallbackSeconds != null && fallbackSeconds >= 0) {
    return fallbackSeconds;
  }
  if (!startedAt) return null;

  const startedMs = Date.parse(startedAt);
  if (Number.isNaN(startedMs)) return null;

  return Math.max(0, Math.floor((Date.now() - startedMs) / 1000));
}
