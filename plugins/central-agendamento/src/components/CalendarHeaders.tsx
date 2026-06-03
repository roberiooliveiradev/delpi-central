import { format, isSameDay } from "date-fns";
import { ptBR } from "date-fns/locale";
import type { DateHeaderProps, HeaderProps } from "react-big-calendar";

function weekdayLabel(date: Date): string {
  const name = format(date, "EEEE", { locale: ptBR });
  return name.charAt(0).toUpperCase() + name.slice(1);
}

export function CalendarDayHeader({ date }: HeaderProps) {
  const dayNumber = format(date, "d", { locale: ptBR });
  const isToday = isSameDay(date, new Date());

  return (
    <div className={`ca-day-header${isToday ? " ca-day-header--today" : ""}`}>
      <span className="ca-day-header__weekday">{weekdayLabel(date)}</span>
      <span className="ca-day-header__number">{dayNumber}</span>
    </div>
  );
}

export function CalendarMonthDateHeader({
  date,
  drilldownView,
  onDrillDown,
  isOffRange,
}: DateHeaderProps) {
  const dayNumber = format(date, "d", { locale: ptBR });
  const isToday = isSameDay(date, new Date());

  const content = (
    <span
      className={[
        "ca-month-date",
        isToday ? "ca-month-date--today" : "",
        isOffRange ? "ca-month-date--off" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {dayNumber}
    </span>
  );

  if (drilldownView) {
    return (
      <button type="button" className="rbc-button-link ca-month-date-btn" onClick={onDrillDown}>
        {content}
      </button>
    );
  }

  return content;
}
