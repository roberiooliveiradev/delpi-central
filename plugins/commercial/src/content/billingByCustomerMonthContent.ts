/**
 * Copy da página Gestão à vista → Faturamento por Cliente.
 */

export const BILLING_BY_CUSTOMER_MONTH_CONTENT = {
  title: "Faturamento por Cliente",
  description:
    "Histórico mensal por cliente (código + loja) no período escolhido. Filtre um cliente para acompanhar a evolução mês a mês; use atalho de ano/mês ou o intervalo de datas. Exportação Excel do recorte completo.",
  pathLabel: "Gestão à vista",
  filters: {
    year: "Ano (atalho)",
    month: "Mês (atalho)",
    monthAll: "Todos os meses",
    monthCustom: "Intervalo (use as datas)",
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

const ISO_DATE = /^(\d{4})-(\d{2})-(\d{2})$/;

/**
 * Reconhece atalho ano/mês quando o intervalo cobre o ano civil inteiro
 * ou exatamente um mês-calendário. Caso contrário o período é o range livre.
 */
export function inferYearMonthFromRange(
  start: string,
  end: string,
): { year: number; month: number | "all" } | null {
  const startMatch = ISO_DATE.exec(start.trim());
  const endMatch = ISO_DATE.exec(end.trim());
  if (!startMatch || !endMatch) return null;

  const startYear = Number(startMatch[1]);
  const startMonth = Number(startMatch[2]);
  const startDay = Number(startMatch[3]);
  const endYear = Number(endMatch[1]);
  const endMonth = Number(endMatch[2]);
  const endDay = Number(endMatch[3]);

  if (
    startYear === endYear &&
    startMonth === 1 &&
    startDay === 1 &&
    endMonth === 12 &&
    endDay === 31
  ) {
    return { year: startYear, month: "all" };
  }

  if (startYear === endYear && startMonth === endMonth && startDay === 1) {
    const lastDay = new Date(startYear, startMonth, 0).getDate();
    if (endDay === lastDay) {
      return { year: startYear, month: startMonth };
    }
  }

  return null;
}
