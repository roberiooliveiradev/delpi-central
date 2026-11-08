import { ChevronLeft, ChevronRight } from "lucide-react";
import { useMemo } from "react";

import { copy } from "../content/copy";
import {
  buildMonthGrid,
  parseLocalIsoDate,
  shiftMonth,
} from "../utils/mywegInvoiceDocumentDate";

const texts = copy.mywegNeeds.invoices;
const WEEKDAYS = ["S", "T", "Q", "Q", "S", "S", "D"] as const;

type Props = {
  selectedIso: string;
  onSelectDate: (iso: string) => void;
  viewYear: number;
  viewMonth: number;
  onViewChange: (next: { year: number; month: number }) => void;
};

function monthTitle(year: number, month: number): string {
  const label = new Date(year, month - 1, 1).toLocaleDateString("pt-BR", {
    month: "long",
    year: "numeric",
  });
  return label.charAt(0).toUpperCase() + label.slice(1);
}

export function MyWegInvoiceMonthCalendar({
  selectedIso,
  onSelectDate,
  viewYear,
  viewMonth,
  onViewChange,
}: Props) {
  const cells = useMemo(
    () => buildMonthGrid(viewYear, viewMonth),
    [viewMonth, viewYear],
  );
  const todayIso = useMemo(() => {
    const now = new Date();
    const y = now.getFullYear();
    const m = String(now.getMonth() + 1).padStart(2, "0");
    const d = String(now.getDate()).padStart(2, "0");
    return `${y}-${m}-${d}`;
  }, []);

  const selected = parseLocalIsoDate(selectedIso);

  return (
    <div
      className="ppc-myweg-needs__month-cal"
      role="group"
      aria-label={texts.calendarAria}
    >
      <header className="ppc-myweg-needs__month-cal-header">
        <button
          type="button"
          className="ppc-myweg-needs__month-cal-nav"
          aria-label={texts.calendarPrevMonth}
          onClick={() => onViewChange(shiftMonth(viewYear, viewMonth, -1))}
        >
          <ChevronLeft size={16} strokeWidth={2} aria-hidden />
        </button>
        <strong className="ppc-myweg-needs__month-cal-title">
          {monthTitle(viewYear, viewMonth)}
        </strong>
        <button
          type="button"
          className="ppc-myweg-needs__month-cal-nav"
          aria-label={texts.calendarNextMonth}
          onClick={() => onViewChange(shiftMonth(viewYear, viewMonth, 1))}
        >
          <ChevronRight size={16} strokeWidth={2} aria-hidden />
        </button>
      </header>

      <div className="ppc-myweg-needs__month-cal-weekdays" aria-hidden="true">
        {WEEKDAYS.map((label, index) => (
          <span key={`${label}-${index}`}>{label}</span>
        ))}
      </div>

      <div className="ppc-myweg-needs__month-cal-grid" role="grid">
        {cells.map((cell) => {
          const selectedDay =
            selected != null &&
            cell.iso ===
              `${selected.year}-${String(selected.month).padStart(2, "0")}-${String(selected.day).padStart(2, "0")}`;
          const isToday = cell.iso === todayIso;
          const className = [
            "ppc-myweg-needs__month-cal-day",
            cell.inMonth ? "" : "ppc-myweg-needs__month-cal-day--muted",
            selectedDay ? "ppc-myweg-needs__month-cal-day--selected" : "",
            isToday ? "ppc-myweg-needs__month-cal-day--today" : "",
          ]
            .filter(Boolean)
            .join(" ");

          return (
            <button
              key={cell.iso}
              type="button"
              className={className}
              aria-label={cell.iso}
              aria-pressed={selectedDay}
              onClick={() => {
                onSelectDate(cell.iso);
                if (!cell.inMonth) {
                  const parsed = parseLocalIsoDate(cell.iso);
                  if (parsed) {
                    onViewChange({ year: parsed.year, month: parsed.month });
                  }
                }
              }}
            >
              {cell.day}
            </button>
          );
        })}
      </div>
    </div>
  );
}
