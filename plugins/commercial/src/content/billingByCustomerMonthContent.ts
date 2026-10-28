/**
 * Copy da página Gestão à vista → Faturamento por Cliente.
 */

export const BILLING_BY_CUSTOMER_MONTH_CONTENT = {
  title: "Faturamento por Cliente",
  description:
    "Histórico de faturamento por cliente (código + loja), com filtros de período, filial e carteira. Exporte o resultado completo para Excel.",
  pathLabel: "Gestão à vista",
  filters: {
    year: "Ano",
    month: "Mês",
    monthAll: "Todos os meses",
    nature: "Natureza",
  },
  table: {
    code: "Código",
    store: "Loja",
    name: "Cliente",
    total: "Total",
    grandTotal: "Total geral",
    empty: "Nenhum faturamento no período filtrado.",
    truncated:
      "A consulta atingiu o limite de clientes retornados. Refine filtros de carteira ou período.",
  },
  export: {
    label: "Exportar Excel (.xlsx)",
    filenamePrefix: "faturamento-por-cliente",
    sheetTitle: "Faturamento por Cliente",
  },
  loading: "Carregando faturamento por cliente…",
  errorFallback: "Não foi possível carregar o relatório de faturamento.",
  reload: "Tentar novamente",
} as const;

const MONTH_LABELS_PT = [
  "Janeiro",
  "Fevereiro",
  "Março",
  "Abril",
  "Maio",
  "Junho",
  "Julho",
  "Agosto",
  "Setembro",
  "Outubro",
  "Novembro",
  "Dezembro",
] as const;

export function monthLabelPt(monthKey: string): string {
  const match = /^(\d{4})-(\d{2})$/.exec(monthKey.trim());
  if (!match) return monthKey;
  const monthIndex = Number(match[2]) - 1;
  const label = MONTH_LABELS_PT[monthIndex];
  if (!label) return monthKey;
  return `${label.slice(0, 3)}/${match[1].slice(2)}`;
}

export function monthOptionLabel(month: number): string {
  return MONTH_LABELS_PT[month - 1] ?? String(month);
}

export function resolveYearMonthRange(
  year: number,
  month: number | "all",
): { start: string; end: string } {
  if (month === "all") {
    return {
      start: `${year}-01-01`,
      end: `${year}-12-31`,
    };
  }
  const mm = String(month).padStart(2, "0");
  const lastDay = new Date(year, month, 0).getDate();
  return {
    start: `${year}-${mm}-01`,
    end: `${year}-${mm}-${String(lastDay).padStart(2, "0")}`,
  };
}
