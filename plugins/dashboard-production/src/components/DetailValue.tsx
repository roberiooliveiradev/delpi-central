import type { ReactNode } from "react";

import { formatAppointmentDateTime, formatDisplayDate } from "../utils/dates";
import {
  PRODUCTION_QUANTITY_FRACTION_DIGITS,
  formatDecimal,
  formatHours,
  formatPercent,
} from "../utils/format";

type QuantityProps = {
  value: number | null | undefined;
  unit?: string | null;
  fractionDigits?: number;
};

export function DetailQuantityValue({
  value,
  unit,
  fractionDigits = PRODUCTION_QUANTITY_FRACTION_DIGITS,
}: QuantityProps): ReactNode {
  if (value == null || Number.isNaN(value)) return "—";

  const number = value.toLocaleString("pt-BR", {
    minimumFractionDigits: 0,
    maximumFractionDigits: fractionDigits,
  });
  const normalizedUnit = unit?.trim();

  if (!normalizedUnit) {
    return <span className="detail-value detail-value--numeric">{number}</span>;
  }

  return (
    <span className="detail-value detail-value--quantity">
      <span className="detail-value__number">{number}</span>
      <span className="detail-value__unit">{normalizedUnit}</span>
    </span>
  );
}

export function DetailNumericValue({
  value,
  fractionDigits = 2,
}: {
  value: number | null | undefined;
  fractionDigits?: number;
}): ReactNode {
  const formatted = formatDecimal(value, fractionDigits);
  if (formatted === "—") return formatted;
  return <span className="detail-value detail-value--numeric">{formatted}</span>;
}

export function DetailPercentValue({
  value,
  fractionDigits = 2,
}: {
  value: number | null | undefined;
  fractionDigits?: number;
}): ReactNode {
  const formatted = formatPercent(value, fractionDigits);
  if (formatted === "—") return formatted;
  return <span className="detail-value detail-value--percent">{formatted}</span>;
}

export function DetailHoursValue({
  value,
  fractionDigits = 2,
}: {
  value: number | null | undefined;
  fractionDigits?: number;
}): ReactNode {
  const formatted = formatHours(value, fractionDigits);
  if (formatted === "—") return formatted;
  const [number, unit] = formatted.split(" ");
  return (
    <span className="detail-value detail-value--quantity">
      <span className="detail-value__number">{number}</span>
      <span className="detail-value__unit">{unit}</span>
    </span>
  );
}

export function DetailDateValue({ value }: { value?: string | null }): ReactNode {
  const formatted = formatDisplayDate(value);
  if (formatted === "—") return formatted;
  return <span className="detail-value detail-value--datetime">{formatted}</span>;
}

export function DetailDateTimeValue({
  date,
  time,
}: {
  date?: string | null;
  time?: string | null;
}): ReactNode {
  const formatted = formatAppointmentDateTime(date, time);
  if (formatted === "—") return formatted;
  return <span className="detail-value detail-value--datetime">{formatted}</span>;
}

export function DetailFormulaValue({ value }: { value: string }): ReactNode {
  if (!value.trim()) return "—";
  return <span className="detail-value detail-value--formula">{value}</span>;
}

export function DetailIntegerValue({
  value,
}: {
  value: number | null | undefined;
}): ReactNode {
  if (value == null || Number.isNaN(value)) return "—";
  return (
    <span className="detail-value detail-value--numeric">
      {value.toLocaleString("pt-BR")}
    </span>
  );
}
