import { isSameDay } from "date-fns";

/** Reservas com início e fim em dias diferentes vão para a faixa superior na visão semana/dia (react-big-calendar). */
export function isMultiDayBooking(start: Date, end: Date): boolean {
  return !isSameDay(start, end);
}
