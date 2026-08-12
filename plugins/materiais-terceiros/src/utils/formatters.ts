const quantityFormatter = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 0,
  maximumFractionDigits: 4,
});

const integerFormatter = new Intl.NumberFormat("pt-BR");

const dateFormatter = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
});

export function formatQuantity(value: number | null | undefined, unit?: string | null): string {
  if (value == null || Number.isNaN(value)) return "—";
  const formatted = quantityFormatter.format(value);
  return unit ? `${formatted} ${unit}` : formatted;
}

export function formatInteger(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return integerFormatter.format(0);
  return integerFormatter.format(value);
}

export function formatDatePtBr(value: string | null | undefined): string {
  if (!value) return "—";
  const iso = /^(\d{4})-(\d{2})-(\d{2})/.exec(value.trim());
  if (iso) {
    const date = new Date(Number(iso[1]), Number(iso[2]) - 1, Number(iso[3]));
    if (!Number.isNaN(date.getTime())) return dateFormatter.format(date);
  }
  return value;
}

export function formatStatus(status: string | null | undefined): string {
  switch (status) {
    case "completed":
      return "Concluído";
    case "partial":
      return "Parcial";
    case "no_return":
      return "Sem retorno";
    default:
      return status?.trim() || "—";
  }
}

export function branchLabel(branch: string): string {
  if (branch === "01") return "SC (01)";
  if (branch === "02") return "ES (02)";
  return branch || "—";
}
