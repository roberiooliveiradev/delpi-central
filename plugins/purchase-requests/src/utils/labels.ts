import type { StatusBadgeVariant } from "@delpi/plugin-ui/index";

import { formatDatePtBr } from "./formatters";

import type {
  ApprovalStatus,
  CostCenterRef,
  DeliveryStatus,
  OverallStage,
  PurchaseOrderSummaryRef,
  PurchaseRequestLine,
  PurchaseRequestListItem,
  PurchaseRequestSummary,
  SupplierRef,
} from "../types/purchaseRequests";

export function labelOverallStage(stage: string | null | undefined): string {
  switch (stage) {
    case "awaiting_order":
      return "Aguardando pedido";
    case "partially_ordered":
      return "Pedido parcial";
    case "ordered":
      return "Pedido emitido";
    case "awaiting_receipt":
      return "Aguardando entrega";
    case "partially_received":
      return "Recebimento parcial";
    case "completed":
      return "Concluída";
    case "residual_closed":
      return "Encerrada por resíduo";
    default:
      return stage || "—";
  }
}

export function labelApprovalStatus(status: string | null | undefined): string {
  switch (status) {
    case "approved":
      return "Aprovada";
    case "rejected":
      return "Rejeitada";
    case "blocked":
      return "Bloqueada";
    case "unknown":
      return "Não identificada";
    default:
      return status || "—";
  }
}

export function labelDeliveryDeadline(item: PurchaseRequestSummary): string {
  if (item.overall_stage === "completed" || item.first_receipt_date) {
    return "Recebido";
  }
  if (item.has_overdue_order) {
    const days = item.max_days_overdue;
    return days != null && days > 0 ? `Atrasado (${days}d)` : "Atrasado";
  }
  const orders = item.purchase_orders ?? [];
  if (orders.length === 0) return "N/A";
  return "No prazo";
}

export function labelReceiptSummary(item: PurchaseRequestSummary): string {
  const stage = item.overall_stage;
  if (stage === "completed") return "Recebido";
  if (stage === "partially_received") return "Parcial";
  if (item.first_receipt_date || item.last_receipt_date) return "Parcial";
  if ((item.purchase_orders?.length ?? 0) > 0) return "Sem recebimento";
  return "Sem recebimento";
}

export function overallStageVariant(stage: string | null | undefined): StatusBadgeVariant {
  switch (stage as OverallStage) {
    case "completed":
      return "success";
    case "partially_received":
    case "partially_ordered":
    case "awaiting_receipt":
    case "awaiting_order":
      return "warning";
    case "residual_closed":
      return "neutral";
    default:
      return "info";
  }
}

export function approvalVariant(status: string | null | undefined): StatusBadgeVariant {
  switch (status as ApprovalStatus) {
    case "approved":
      return "success";
    case "rejected":
    case "blocked":
      return "danger";
    case "unknown":
      return "neutral";
    default:
      return "neutral";
  }
}

export function deliveryVariant(item: PurchaseRequestSummary): StatusBadgeVariant {
  const label = labelDeliveryDeadline(item);
  if (label.startsWith("Atrasado")) return "danger";
  if (label === "Recebido") return "success";
  if (label === "No prazo") return "info";
  return "neutral";
}

export function formatRequestNumber(requestNumber: string): string {
  const trimmed = requestNumber.trim();
  return trimmed ? `SC ${trimmed}` : "—";
}

export function formatRequesterName(
  name: string | null | undefined,
  code: string | null | undefined,
): string {
  const resolved = (name || "").trim();
  if (resolved) return resolved;
  const fallback = (code || "").trim();
  return fallback || "—";
}

export function formatRequesterOptionLabel(
  name: string | null | undefined,
  code: string | null | undefined,
  protheusUserId: string,
): string {
  const label = formatRequesterName(name, code);
  if (label !== "—" && label !== protheusUserId) return label;
  return protheusUserId || label;
}

export function formatCostCentersSummary(costCenters: CostCenterRef[] | undefined): string {
  const list = costCenters ?? [];
  if (list.length === 0) return "—";
  if (list.length === 1) {
    const cc = list[0];
    const desc = cc.description?.trim();
    return desc ? `${cc.code} · ${desc.slice(0, 24)}${desc.length > 24 ? "…" : ""}` : cc.code;
  }
  return `${list[0].code} + ${list.length - 1}`;
}

export function formatCostCentersDetailLabel(costCenters: CostCenterRef[] | undefined): string {
  const count = costCenters?.length ?? 0;
  if (count === 0) return "—";
  if (count === 1) return "1 centro de custo";
  return `${count} centros de custo`;
}

export function formatOrdersSummary(orders: PurchaseOrderSummaryRef[] | undefined): string {
  const list = orders ?? [];
  if (list.length === 0) return "—";
  if (list.length === 1) return list[0].order_number?.trim() || "—";
  return `${list.length} pedidos`;
}

export function formatSuppliersSummary(suppliers: SupplierRef[] | undefined): string {
  const list = suppliers ?? [];
  if (list.length === 0) return "—";
  if (list.length === 1) {
    const name = suppliers?.[0]?.name?.trim();
    return name || suppliers?.[0]?.code?.trim() || "—";
  }
  return `${list.length} fornecedores`;
}

export function formatForecastSummary(item: PurchaseRequestSummary): string {
  const orders = item.purchase_orders ?? [];
  if (orders.length === 0) return "—";
  return "Ver detalhes";
}

export function formatProductLabel(
  code: string | null | undefined,
  description: string | null | undefined,
): string {
  const resolvedCode = (code || "").trim();
  const resolvedDescription = (description || "").trim();
  if (resolvedCode && resolvedDescription) {
    return `${resolvedCode} · ${resolvedDescription}`;
  }
  return resolvedCode || resolvedDescription || "—";
}

export function formatCostCenterLine(line: PurchaseRequestLine): string {
  const code = (line.cost_center?.code || line.cost_center_code || "").trim();
  if (!code) return "—";
  const desc = (line.cost_center?.description || line.cost_center_description || "").trim();
  return desc ? `${code} · ${desc}` : code;
}

function ordersFromLine(line: PurchaseRequestLine): PurchaseOrderSummaryRef[] {
  return (line.purchase_orders ?? []).map((order) => ({
    branch: order.branch,
    order_number: order.order_number,
    order_item: order.order_item,
    supplier_code: order.supplier_code,
    supplier_store: order.supplier_store,
    supplier_name: order.supplier_name,
  }));
}

function suppliersFromLine(line: PurchaseRequestLine): SupplierRef[] {
  const map = new Map<string, SupplierRef>();
  for (const order of line.purchase_orders ?? []) {
    const code = (order.supplier_code || "").trim();
    const store = (order.supplier_store || "").trim();
    if (!code) continue;
    const key = `${code}:${store}`;
    map.set(key, {
      code,
      store,
      name: order.supplier_name,
    });
  }
  return [...map.values()];
}

export function labelDeliveryDeadlineForLine(line: PurchaseRequestLine): string {
  const stage = line.derived?.overall_stage;
  if (stage === "completed" || stage === "residual_closed") {
    return "Recebido";
  }
  const orders = line.purchase_orders ?? [];
  const overdue = orders.some((order) => order.derived?.delivery_status === "overdue");
  if (overdue) {
    const days = orders
      .map((order) => order.derived?.days_overdue)
      .filter((value): value is number => value != null && value > 0);
    const maxDays = days.length > 0 ? Math.max(...days) : null;
    return maxDays != null ? `Atrasado (${maxDays}d)` : "Atrasado";
  }
  if (orders.length === 0) return "N/A";
  return "No prazo";
}

export function labelReceiptSummaryForLine(line: PurchaseRequestLine): string {
  const stage = line.derived?.overall_stage;
  if (stage === "completed") return "Recebido";
  if (stage === "partially_received") return "Parcial";
  const orders = line.purchase_orders ?? [];
  const received = orders.some((order) => (order.received_quantity ?? 0) > 0);
  if (received) return "Parcial";
  if (orders.length > 0) return "Sem recebimento";
  return "Sem recebimento";
}

export function formatForecastSummaryForLine(line: PurchaseRequestLine): string {
  const dates = (line.purchase_orders ?? [])
    .map((order) => order.expected_delivery_date)
    .filter((value): value is string => Boolean(value));
  if (dates.length === 0) return "—";
  return formatDatePtBr(dates.sort()[0]);
}

export function deliveryVariantForLine(line: PurchaseRequestLine): StatusBadgeVariant {
  const label = labelDeliveryDeadlineForLine(line);
  if (label.startsWith("Atrasado")) return "danger";
  if (label === "Recebido") return "success";
  if (label === "No prazo") return "info";
  return "neutral";
}

export function listItemOverallStage(line: PurchaseRequestListItem): string | null | undefined {
  return line.derived?.overall_stage;
}

export function listItemApprovalStatus(line: PurchaseRequestListItem): string | null | undefined {
  return line.approval?.status;
}

export function listItemIssueDate(line: PurchaseRequestListItem): string | null | undefined {
  return line.request_issue_date;
}

export function listItemRequesterName(line: PurchaseRequestListItem): string {
  return formatRequesterName(line.requester?.name, line.requester?.code);
}

export function listItemOrdersSummary(line: PurchaseRequestListItem): string {
  return formatOrdersSummary(ordersFromLine(line));
}

export function listItemSuppliersSummary(line: PurchaseRequestListItem): string {
  return formatSuppliersSummary(suppliersFromLine(line));
}

export function formatBuyerLabel(
  buyer: { name?: string | null; code?: string | null } | null | undefined,
): string {
  const name = buyer?.name?.trim();
  if (name) return name;
  const code = buyer?.code?.trim();
  if (code) return code;
  return "Comprador não informado";
}

export function labelDeliveryStatus(status: string | null | undefined): string {
  switch (status as DeliveryStatus) {
    case "overdue":
      return "Atrasado";
    case "on_time":
      return "No prazo";
    case "received":
      return "Recebido";
    case "not_applicable":
      return "N/A";
    default:
      return status || "—";
  }
}
