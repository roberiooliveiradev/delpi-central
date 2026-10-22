/**
 * Turnos de fábrica — espelho de `api-delpi/.../factory_shifts.py`
 * e do plugin eficiência-fabril (`constants/shifts.ts`).
 * Não importar de outro MFE (bounded context).
 */

export type FactoryShiftId = "1" | "2" | "3";

export type FactoryShiftDefinition = {
  id: FactoryShiftId;
  label: string;
  start: string;
  end: string;
};

export const FACTORY_SHIFTS: readonly FactoryShiftDefinition[] = [
  { id: "1", label: "1º Turno", start: "04:34", end: "14:17" },
  { id: "2", label: "2º Turno", start: "14:18", end: "23:49" },
  { id: "3", label: "3º Turno", start: "23:50", end: "04:33" },
] as const;

/** Valor do select: vazio = todos os turnos. */
export const AUDITORIA_SHIFT_ALL = "" as const;

export type AuditoriaShiftFilter = FactoryShiftId | typeof AUDITORIA_SHIFT_ALL;

export const AUDITORIA_SHIFT_OPTIONS: ReadonlyArray<{
  value: AuditoriaShiftFilter;
  label: string;
}> = [
  { value: AUDITORIA_SHIFT_ALL, label: "Todos" },
  ...FACTORY_SHIFTS.map((shift) => ({
    value: shift.id,
    label: `${shift.label} (${shift.start} – ${shift.end})`,
  })),
];
