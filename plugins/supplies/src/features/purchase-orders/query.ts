import type { PurchaseOrdersQuery } from "./types";
import { DEFAULT_PAGE_SIZE } from "./types";

export function createDefaultQuery(branch: string): PurchaseOrdersQuery {
  return {
    branch,
    order_number: "",
    product_code: "",
    supplier_code: "",
    expected_delivery_from: "",
    expected_delivery_to: "",
    late_only: false,
    page: 1,
    page_size: DEFAULT_PAGE_SIZE,
    order: "",
  };
}

export function buildListSearchParams(query: PurchaseOrdersQuery): URLSearchParams {
  const params = new URLSearchParams();
  if (query.branch) params.set("branch", query.branch.trim());
  if (query.order_number.trim()) params.set("order_number", query.order_number.trim());
  if (query.product_code.trim()) params.set("product_code", query.product_code.trim());
  if (query.supplier_code.trim()) params.set("supplier_code", query.supplier_code.trim());
  if (query.expected_delivery_from.trim()) {
    params.set("expected_delivery_from", query.expected_delivery_from.trim());
  }
  if (query.expected_delivery_to.trim()) {
    params.set("expected_delivery_to", query.expected_delivery_to.trim());
  }
  if (query.late_only) params.set("late_only", "true");
  params.set("page", String(query.page));
  params.set("page_size", String(query.page_size));
  return params;
}

export function buildOrderKey(branch: string, orderNumber: string): string {
  return `${branch}:${orderNumber}`;
}

export function parseOrderKey(raw: string): { branch: string; orderNumber: string } | null {
  const trimmed = raw.trim();
  if (!trimmed.includes(":")) return null;
  const [branch, ...rest] = trimmed.split(":");
  const orderNumber = rest.join(":").trim();
  if (!branch?.trim() || !orderNumber) return null;
  return { branch: branch.trim(), orderNumber };
}

function readParam(params: URLSearchParams, key: string): string {
  return (params.get(key) ?? "").trim();
}

function readInt(params: URLSearchParams, key: string, fallback: number): number {
  const parsed = Number.parseInt(readParam(params, key), 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

export function parseQueryFromSearch(search: string, fallbackBranch: string): PurchaseOrdersQuery {
  const params = new URLSearchParams(search.startsWith("?") ? search.slice(1) : search);
  const defaults = createDefaultQuery(fallbackBranch);
  const lateRaw = readParam(params, "late_only").toLowerCase();
  return {
    branch: readParam(params, "branch") || defaults.branch,
    order_number: readParam(params, "order_number"),
    product_code: readParam(params, "product_code"),
    supplier_code: readParam(params, "supplier_code"),
    expected_delivery_from: readParam(params, "expected_delivery_from"),
    expected_delivery_to: readParam(params, "expected_delivery_to"),
    late_only: lateRaw === "1" || lateRaw === "true" || lateRaw === "yes",
    page: readInt(params, "page", 1),
    page_size: readInt(params, "page_size", DEFAULT_PAGE_SIZE),
    order: readParam(params, "order"),
  };
}

export function buildUrlSearch(query: PurchaseOrdersQuery): string {
  const params = buildListSearchParams(query);
  if (query.order.trim()) params.set("order", query.order.trim());
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export function formatDatePtBr(iso: string | null | undefined): string {
  if (!iso) return "—";
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  if (!match) return iso;
  return `${match[3]}/${match[2]}/${match[1]}`;
}

export function labelDeliveryStatus(status: string | null | undefined): string {
  switch (status) {
    case "late":
      return "Atrasado";
    case "on_time":
      return "No prazo";
    case "no_date":
      return "Sem data";
    default:
      return status || "—";
  }
}

export function formatProductLabel(
  code: string | null | undefined,
  description: string | null | undefined,
): string {
  const c = (code || "").trim();
  const d = (description || "").trim();
  if (c && d) return `${c} — ${d}`;
  return c || d || "—";
}

export function formatMoneyBr(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return value.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
    maximumFractionDigits: 2,
  });
}
