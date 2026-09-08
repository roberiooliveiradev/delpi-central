import type { OverallStage, PurchaseRequestsQuery } from "./types";
import { DEFAULT_PAGE_SIZE, OVERALL_STAGE_VALUES } from "./types";

const LOOKBACK_DAYS = 90;

function pad2(value: number): string {
  return String(value).padStart(2, "0");
}

function formatIsoDate(date: Date): string {
  return `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())}`;
}

export function defaultPeriod(): { date_from: string; date_to: string } {
  const end = new Date();
  end.setHours(0, 0, 0, 0);
  const start = new Date(end);
  start.setDate(start.getDate() - LOOKBACK_DAYS);
  return { date_from: formatIsoDate(start), date_to: formatIsoDate(end) };
}

export function createDefaultQuery(branch: string): PurchaseRequestsQuery {
  const period = defaultPeriod();
  return {
    branch,
    date_from: period.date_from,
    date_to: period.date_to,
    request_number: "",
    product_code: "",
    overall_stages: [],
    page: 1,
    page_size: DEFAULT_PAGE_SIZE,
    request: "",
  };
}

export function buildListSearchParams(query: PurchaseRequestsQuery): URLSearchParams {
  const params = new URLSearchParams();
  if (query.branch) params.set("branch", query.branch.trim());
  if (query.date_from.trim()) params.set("date_from", query.date_from.trim());
  if (query.date_to.trim()) params.set("date_to", query.date_to.trim());
  if (query.request_number.trim()) params.set("request_number", query.request_number.trim());
  if (query.product_code.trim()) params.set("product_code", query.product_code.trim());
  for (const stage of query.overall_stages) {
    params.append("overall_stage", stage);
  }
  params.set("page", String(query.page));
  params.set("page_size", String(query.page_size));
  return params;
}

export function buildRequestKey(branch: string, requestNumber: string): string {
  return `${branch}:${requestNumber}`;
}

export function parseRequestKey(raw: string): { branch: string; requestNumber: string } | null {
  const trimmed = raw.trim();
  if (!trimmed.includes(":")) return null;
  const [branch, ...rest] = trimmed.split(":");
  const requestNumber = rest.join(":").trim();
  if (!branch?.trim() || !requestNumber) return null;
  return { branch: branch.trim(), requestNumber };
}

function readParam(params: URLSearchParams, key: string): string {
  return (params.get(key) ?? "").trim();
}

function readInt(params: URLSearchParams, key: string, fallback: number): number {
  const parsed = Number.parseInt(readParam(params, key), 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

export function parseQueryFromSearch(search: string, fallbackBranch: string): PurchaseRequestsQuery {
  const params = new URLSearchParams(search.startsWith("?") ? search.slice(1) : search);
  const defaults = createDefaultQuery(fallbackBranch);
  const allowed = new Set<string>(OVERALL_STAGE_VALUES);
  const stages = params
    .getAll("overall_stage")
    .map((item) => item.trim())
    .filter((item): item is OverallStage => allowed.has(item));
  return {
    branch: readParam(params, "branch") || defaults.branch,
    date_from: readParam(params, "date_from") || defaults.date_from,
    date_to: readParam(params, "date_to") || defaults.date_to,
    request_number: readParam(params, "request_number"),
    product_code: readParam(params, "product_code"),
    overall_stages: stages,
    page: readInt(params, "page", 1),
    page_size: readInt(params, "page_size", DEFAULT_PAGE_SIZE),
    request: readParam(params, "request"),
  };
}

export function buildUrlSearch(query: PurchaseRequestsQuery): string {
  const params = buildListSearchParams(query);
  if (query.request.trim()) params.set("request", query.request.trim());
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export function formatDatePtBr(iso: string | null | undefined): string {
  if (!iso) return "—";
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  if (!match) return iso;
  return `${match[3]}/${match[2]}/${match[1]}`;
}

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

export function formatRequestNumber(value: string | null | undefined): string {
  const trimmed = (value || "").trim();
  return trimmed || "—";
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
