import {
  EMPTY_QUERY,
  SHIPMENT_STATUS_VALUES,
  type ShipmentStatus,
  type ThirdPartyMaterialsQuery,
} from "../types/thirdPartyMaterials";

export const BASE_PATH = "/apps/materiais-terceiros";

export type UrlState = ThirdPartyMaterialsQuery & {
  shipmentRecno: string;
};

export const EMPTY_URL_STATE: UrlState = {
  ...EMPTY_QUERY,
  shipmentRecno: "",
};

function readParam(params: URLSearchParams, key: string): string {
  return (params.get(key) ?? "").trim();
}

function readBool(params: URLSearchParams, key: string): boolean {
  const raw = (params.get(key) ?? "").trim().toLowerCase();
  return raw === "1" || raw === "true";
}

function readStatus(params: URLSearchParams): ShipmentStatus | "" {
  const raw = readParam(params, "status");
  return (SHIPMENT_STATUS_VALUES as readonly string[]).includes(raw)
    ? (raw as ShipmentStatus)
    : "";
}

export function parseUrlState(search: string): UrlState {
  const params = new URLSearchParams(search.startsWith("?") ? search.slice(1) : search);
  return {
    branch: readParam(params, "branch"),
    product: readParam(params, "product"),
    customerReference: readParam(params, "customerReference"),
    partnerCode: readParam(params, "partnerCode"),
    partnerStore: readParam(params, "partnerStore"),
    receiptNumber: readParam(params, "receiptNumber"),
    returnNumber: readParam(params, "returnNumber"),
    issuedFrom: readParam(params, "issuedFrom"),
    issuedTo: readParam(params, "issuedTo"),
    status: readStatus(params),
    onlyWithBalance: readBool(params, "onlyWithBalance"),
    includeTestProducts: readBool(params, "includeTestProducts"),
    shipmentRecno: readParam(params, "shipment"),
  };
}

export function buildUrlSearch(state: UrlState): string {
  const params = new URLSearchParams();
  if (state.branch) params.set("branch", state.branch);
  if (state.product) params.set("product", state.product);
  if (state.customerReference) params.set("customerReference", state.customerReference);
  if (state.partnerCode) params.set("partnerCode", state.partnerCode);
  if (state.partnerStore) params.set("partnerStore", state.partnerStore);
  if (state.receiptNumber) params.set("receiptNumber", state.receiptNumber);
  if (state.returnNumber) params.set("returnNumber", state.returnNumber);
  if (state.issuedFrom) params.set("issuedFrom", state.issuedFrom);
  if (state.issuedTo) params.set("issuedTo", state.issuedTo);
  if (state.status) params.set("status", state.status);
  if (state.onlyWithBalance) params.set("onlyWithBalance", "true");
  if (state.includeTestProducts) params.set("includeTestProducts", "true");
  if (state.shipmentRecno) params.set("shipment", state.shipmentRecno);
  const serialized = params.toString();
  return serialized ? `?${serialized}` : "";
}

export function replaceUrlState(pathname: string, state: UrlState): void {
  if (typeof window === "undefined") return;
  const next = `${pathname || BASE_PATH}${buildUrlSearch(state)}`;
  const current = `${window.location.pathname}${window.location.search}`;
  if (next === current) return;
  window.history.replaceState(window.history.state, "", next);
}

export function queryFromUrlState(state: UrlState): ThirdPartyMaterialsQuery {
  const { shipmentRecno: _ignored, ...query } = state;
  void _ignored;
  return query;
}
