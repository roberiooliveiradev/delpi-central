import type { DelinquencyCustomer } from "../types";

const LABEL_MAX_LENGTH = 28;

/** Taxa de inadimplência proporcional ao portfólio de títulos do cliente. */
export function delinquencyRateByCount(customer: DelinquencyCustomer): number {
  if (customer.totalTitles <= 0) return 0;
  return (customer.lateTitles / customer.totalTitles) * 100;
}

export function formatDelinquentCustomerLabel(customer: DelinquencyCustomer): string {
  const base = (customer.shortName || customer.customerName || customer.customerCode).trim();
  if (base.length <= LABEL_MAX_LENGTH) {
    return base;
  }
  return `${base.slice(0, LABEL_MAX_LENGTH - 1).trimEnd()}…`;
}

export type DelinquentCustomerChartRow = {
  label: string;
  delinquencyPct: number;
  lateTitles: number;
  totalTitles: number;
  customerCode: string;
  store: string;
  fill: string;
};

export function buildTopDelinquentChartRows(
  customers: readonly DelinquencyCustomer[],
): DelinquentCustomerChartRow[] {
  return customers
    .filter((customer) => customer.totalTitles > 0 && customer.lateTitles > 0)
    .map((customer) => ({
      label: formatDelinquentCustomerLabel(customer),
      delinquencyPct: delinquencyRateByCount(customer),
      lateTitles: customer.lateTitles,
      totalTitles: customer.totalTitles,
      customerCode: customer.customerCode,
      store: customer.store,
      fill: delinquencyBarFill(delinquencyRateByCount(customer)),
    }))
    .sort((left, right) => {
      if (right.delinquencyPct !== left.delinquencyPct) {
        return right.delinquencyPct - left.delinquencyPct;
      }
      return left.label.localeCompare(right.label, "pt-BR");
    });
}

function delinquencyBarFill(rate: number): string {
  if (rate >= 75) return "var(--fin-critical, #e5484d)";
  if (rate >= 40) return "#f97316";
  return "var(--fin-accent, #089bdb)";
}
