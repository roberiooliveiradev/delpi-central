export function formatMonthLabel(item: {
  month_date?: string;
  month?: string | number;
  year?: string | number;
}): string {
  if (item.month_date) {
    const parsed = new Date(item.month_date);
    if (!Number.isNaN(parsed.getTime())) {
      return parsed.toLocaleDateString("pt-BR", {
        month: "short",
        year: "2-digit",
      });
    }
  }
  if (item.month != null && item.year != null) {
    return `${item.month}/${item.year}`;
  }
  return String(item.month ?? "—");
}

export function formatChartCurrencyAxis(value: number | string): string {
  const num = typeof value === "string" ? Number(value) : value;
  if (!Number.isFinite(num)) return "—";
  if (Math.abs(num) >= 1_000_000) {
    return `R$ ${(num / 1_000_000).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} mi`;
  }
  if (Math.abs(num) >= 1_000) {
    return `R$ ${(num / 1_000).toLocaleString("pt-BR", { maximumFractionDigits: 0 })} mil`;
  }
  return num.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
    maximumFractionDigits: 0,
  });
}
