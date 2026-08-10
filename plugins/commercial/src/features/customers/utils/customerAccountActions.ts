import type { OpenOrdersTotvsItem } from "../../../types/openOrdersTotvs";
import { formatCurrency } from "../../../utils/format";
import type { CustomerSummary } from "../types/customerSummary";

export type CustomerConversationPoint = {
  id: "overdue" | "partial-coverage" | "open-value";
  label: string;
  variant: "danger" | "warning" | "info";
};

export function buildCustomerConversationPoints(
  customer: Pick<
    CustomerSummary,
    "quantidadePedidosAtrasados" | "maiorAtrasoDias" | "valorTotalAberto"
  >,
  coveragePartial: boolean,
): CustomerConversationPoint[] {
  const points: CustomerConversationPoint[] = [];

  if (customer.quantidadePedidosAtrasados > 0) {
    const count = customer.quantidadePedidosAtrasados;
    const delay =
      customer.maiorAtrasoDias > 0
        ? ` · maior atraso ${customer.maiorAtrasoDias.toLocaleString("pt-BR")} dias`
        : "";
    points.push({
      id: "overdue",
      label: `${count.toLocaleString("pt-BR")} ${count === 1 ? "pedido atrasado" : "pedidos atrasados"}${delay}`,
      variant: "danger",
    });
  }

  if (coveragePartial) {
    points.push({
      id: "partial-coverage",
      label: "Cobertura cadastral parcial",
      variant: "warning",
    });
  }

  if (customer.valorTotalAberto > 0) {
    points.push({
      id: "open-value",
      label: `${formatCurrency(customer.valorTotalAberto)} em aberto`,
      variant: "info",
    });
  }

  return points;
}

export function findFirstNavigableOrderLine(
  lines: readonly OpenOrdersTotvsItem[],
): OpenOrdersTotvsItem | null {
  return (
    lines.find(
      (line) =>
        Boolean(line.filial?.trim()) &&
        Boolean(line.pedido?.trim()) &&
        Boolean(line.linha?.trim()),
    ) ?? null
  );
}

export function findOrderProposalLine(
  lines: readonly OpenOrdersTotvsItem[],
): OpenOrdersTotvsItem | null {
  return lines.find((line) => Boolean(line.proposal_number?.trim())) ?? null;
}

export function buildOrderOpportunityContextSearch(
  line: Pick<OpenOrdersTotvsItem, "filial" | "proposal_number">,
): string {
  const params = new URLSearchParams();
  const branch = line.filial?.trim();
  const proposalNumber = line.proposal_number?.trim();
  if (branch) params.set("branch", branch);
  if (proposalNumber) params.set("search", proposalNumber);
  const query = params.toString();
  return query ? `?${query}` : "";
}
