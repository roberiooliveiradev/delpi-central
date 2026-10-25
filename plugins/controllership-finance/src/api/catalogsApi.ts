/** Cliente da BFF — catálogos governados P6 (MANAGE efetivo). */
import { cfApiUrl, httpGet, httpPost, httpPut } from "./httpClient";

type Envelope<T> = { data?: T };

export type CatalogKey =
  | "BANK_ACCOUNT"
  | "REJECTION_REASON"
  | "ATTACHMENT_ROLE"
  | "NOTIFICATION_TARGET"
  | "PACKAGE_REQUIRED_AREA"
  | "REVIEW_ELIGIBILITY";

export type CatalogSummary = {
  catalog_key: CatalogKey;
  active: number;
  inactive: number;
};

export type CatalogEntry = {
  entry_id: string;
  catalog_key: CatalogKey;
  code: string;
  label: string;
  attributes: Record<string, unknown>;
  effective_from_period: string | null;
  active: boolean;
  revision: number;
  created_by: string;
  created_at: string;
  updated_by: string | null;
  updated_at: string | null;
  deactivated_by: string | null;
  deactivated_at: string | null;
};

const BASE = "/admin/closing-catalogs";

export async function listCatalogs(
  options?: { signal?: AbortSignal },
): Promise<CatalogSummary[]> {
  const envelope = await httpGet<Envelope<{ catalogs: CatalogSummary[] }>>(
    cfApiUrl(BASE),
    options,
  );
  return envelope?.data?.catalogs ?? [];
}

export async function listCatalogEntries(
  catalogKey: CatalogKey,
  options?: { includeInactive?: boolean; signal?: AbortSignal },
): Promise<CatalogEntry[]> {
  const include = options?.includeInactive === false ? "false" : "true";
  const envelope = await httpGet<Envelope<{ items: CatalogEntry[] }>>(
    cfApiUrl(
      `${BASE}/${catalogKey}/entries?include_inactive=${include}`,
    ),
    options,
  );
  return envelope?.data?.items ?? [];
}

export function createCatalogEntry(
  catalogKey: CatalogKey,
  payload: {
    code: string;
    label: string;
    attributes?: Record<string, unknown>;
    effective_from_period?: string | null;
  },
): Promise<CatalogEntry> {
  return httpPost<Envelope<CatalogEntry>>(
    cfApiUrl(`${BASE}/${catalogKey}/entries`),
    payload,
  ).then((envelope) => {
    if (!envelope?.data) throw new Error("Resposta vazia da operação.");
    return envelope.data;
  });
}

export function updateCatalogEntry(
  catalogKey: CatalogKey,
  code: string,
  payload: {
    label?: string | null;
    attributes?: Record<string, unknown> | null;
    revision: number;
  },
): Promise<CatalogEntry> {
  return httpPut<Envelope<CatalogEntry>>(
    cfApiUrl(`${BASE}/${catalogKey}/entries/${code}`),
    payload,
  ).then((envelope) => {
    if (!envelope?.data) throw new Error("Resposta vazia da operação.");
    return envelope.data;
  });
}

export function deactivateCatalogEntry(
  catalogKey: CatalogKey,
  code: string,
  revision: number,
): Promise<CatalogEntry> {
  return httpPost<Envelope<CatalogEntry>>(
    cfApiUrl(
      `${BASE}/${catalogKey}/entries/${code}/deactivate`,
    ),
    { revision },
  ).then((envelope) => {
    if (!envelope?.data) throw new Error("Resposta vazia da operação.");
    return envelope.data;
  });
}

export function reactivateCatalogEntry(
  catalogKey: CatalogKey,
  code: string,
): Promise<CatalogEntry> {
  return httpPost<Envelope<CatalogEntry>>(
    cfApiUrl(
      `${BASE}/${catalogKey}/entries/${code}/reactivate`,
    ),
    {},
  ).then((envelope) => {
    if (!envelope?.data) throw new Error("Resposta vazia da operação.");
    return envelope.data;
  });
}
