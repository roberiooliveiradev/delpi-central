import { httpGet } from "../../api/httpClient";
import { API_BASE, unwrapEnvelope } from "../../api/requestsApi";
import type { Envelope } from "../../types/requests";
import type { Carrier, Party, PartyType, ProductHit, WarehouseBalance } from "./domain/types";

const LOOKUPS = `${API_BASE}/request-types/invoice-issuance/lookups`;

export async function searchParties(
  partyType: PartyType,
  query: string,
  limit = 20,
  signal?: AbortSignal,
): Promise<Party[]> {
  const qs = new URLSearchParams({
    party_type: partyType,
    query,
    limit: String(limit),
  });
  const body = await httpGet<Envelope<{ items: Party[] }>>(`${LOOKUPS}/parties?${qs}`, {
    signal,
  });
  return unwrapEnvelope(body).items || [];
}

export async function searchProducts(
  query: string,
  limit = 20,
  signal?: AbortSignal,
): Promise<ProductHit[]> {
  const qs = new URLSearchParams({ query, limit: String(limit) });
  const body = await httpGet<Envelope<{ items: ProductHit[] }>>(
    `${LOOKUPS}/products?${qs}`,
    { signal },
  );
  const items = unwrapEnvelope(body).items || [];
  return items.map((item) => ({
    ...item,
    code: (item as ProductHit & { product_code?: string }).code
      || (item as ProductHit & { product_code?: string }).product_code
      || "",
  }));
}

export async function searchCarriers(
  query: string,
  limit = 20,
  signal?: AbortSignal,
): Promise<Carrier[]> {
  const qs = new URLSearchParams({ query, limit: String(limit) });
  const body = await httpGet<Envelope<{ items: Carrier[] }>>(
    `${LOOKUPS}/carriers?${qs}`,
    { signal },
  );
  return unwrapEnvelope(body).items || [];
}

export async function getWarehouse01Balance(
  code: string,
  branch: string,
  signal?: AbortSignal,
): Promise<WarehouseBalance> {
  const qs = new URLSearchParams({ branch });
  const body = await httpGet<
    Envelope<WarehouseBalance & { balance?: number; quantity?: number }>
  >(`${LOOKUPS}/products/${encodeURIComponent(code)}/warehouse-01-balance?${qs}`, {
    signal,
  });
  const data = unwrapEnvelope(body);
  return {
    product_code: data.product_code,
    branch_code: data.branch_code,
    warehouse: data.warehouse,
    quantity: Number(data.quantity ?? data.balance ?? 0),
  };
}
