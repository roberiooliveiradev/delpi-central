export type EficienciaFabrilShift = "1" | "2" | "3";

export type ShiftDefinition = {
  id: EficienciaFabrilShift;
  label: string;
  start: string;
  end: string;
};

/** Turnos da fábrica — classificação pelo horário de início do apontamento. */
export const FACTORY_SHIFTS: readonly ShiftDefinition[] = [
  { id: "1", label: "1º Turno", start: "04:34", end: "14:17" },
  { id: "2", label: "2º Turno", start: "14:18", end: "23:49" },
  { id: "3", label: "3º Turno", start: "23:50", end: "04:33" },
] as const;

const SHIFT_MINUTES: Record<
  EficienciaFabrilShift,
  { start: number; end: number }
> = {
  "1": { start: 4 * 60 + 34, end: 14 * 60 + 17 },
  "2": { start: 14 * 60 + 18, end: 23 * 60 + 49 },
  "3": { start: 23 * 60 + 50, end: 4 * 60 + 33 },
};

function isWithinShiftMinutes(
  minutes: number,
  start: number,
  end: number
): boolean {
  if (start <= end) {
    return minutes >= start && minutes <= end;
  }
  return minutes >= start || minutes <= end;
}

/** Converte hora de início (HH:MM ou HH:MM:SS) em minutos desde meia-noite. */
export function parseStartTimeToMinutes(
  horaInicio: string | null | undefined
): number | null {
  if (!horaInicio) return null;

  const trimmed = String(horaInicio).trim();
  const match = trimmed.match(/(?:T|^)(\d{1,2}):(\d{2})(?::(\d{2}))?/);
  if (!match) return null;

  const hours = Number(match[1]);
  const minutes = Number(match[2]);
  if (!Number.isFinite(hours) || !Number.isFinite(minutes)) return null;
  if (hours < 0 || hours > 23 || minutes < 0 || minutes > 59) return null;

  return hours * 60 + minutes;
}

export function getShiftForStartTime(
  horaInicio: string | null | undefined
): EficienciaFabrilShift | null {
  const minutes = parseStartTimeToMinutes(horaInicio);
  if (minutes === null) return null;

  for (const shift of FACTORY_SHIFTS) {
    const range = SHIFT_MINUTES[shift.id];
    if (isWithinShiftMinutes(minutes, range.start, range.end)) {
      return shift.id;
    }
  }

  return null;
}

export function matchesShiftFilter(
  horaInicio: string | null | undefined,
  shifts: EficienciaFabrilShift[] | undefined
): boolean {
  if (!shifts || shifts.length === 0) return true;

  const itemShift = getShiftForStartTime(horaInicio);
  if (!itemShift) return false;

  return shifts.includes(itemShift);
}
