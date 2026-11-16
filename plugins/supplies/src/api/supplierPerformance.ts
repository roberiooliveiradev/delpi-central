import { httpGet, httpGetBlob, suppliesApiUrl } from "./httpClient";

export type PerformanceComponent = {
  index: number | null;
  assessed_count: number;
  positive_count: number;
  negative_count: number;
  unknown_count: number;
  conditional_count: number;
  urgent_count: number;
};

export type SupplierPerformance = {
  supplier_code: string;
  supplier_store: string;
  supplier_name: string;
  branches: string[];
  quality: PerformanceComponent;
  delivery: PerformanceComponent;
  idf: number | null;
  quality_contribution: number | null;
  delivery_contribution: number | null;
  status: "complete" | "missing_quality" | "missing_delivery" | "inconsistent";
};

export type SupplierPerformanceResponse = {
  items: SupplierPerformance[];
  summary: {
    suppliers: number;
    evaluated: number;
    incomplete: number;
    average_idf: number | null;
    average_quality: number | null;
    average_delivery: number | null;
    inspection_count: number;
    receipt_count: number;
  };
  methodology: {
    quality_weight: 70;
    delivery_weight: 30;
    scale: 100;
    classification_bands: null;
  };
  period: { from: string; to: string };
  branches: string[];
  calculated_at: string;
};

export function buildSupplierPerformanceQuery(filters: {
  branches: string[];
  from: string;
  to: string;
}): string {
  const query = new URLSearchParams();
  for (const branch of filters.branches) query.append("branch", branch);
  query.set("date_from", filters.from);
  query.set("date_to", filters.to);
  return query.toString();
}

export function getSupplierPerformance(
  filters: { branches: string[]; from: string; to: string },
  signal?: AbortSignal,
) {
  return httpGet<SupplierPerformanceResponse>(
    suppliesApiUrl(
      `/analytics/supplier-performance?${buildSupplierPerformanceQuery(filters)}`,
    ),
    { signal },
  );
}

export async function downloadSupplierPerformanceXlsx(
  filters: { branches: string[]; from: string; to: string },
  supplier?: { supplier_code: string; supplier_store: string } | null,
): Promise<void> {
  const params = new URLSearchParams(buildSupplierPerformanceQuery(filters));
  if (supplier) {
    params.set("supplier_code", supplier.supplier_code);
    params.set("supplier_store", supplier.supplier_store);
  }
  const blob = await httpGetBlob(
    suppliesApiUrl(`/analytics/supplier-performance/export?${params.toString()}`),
  );
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = supplier
    ? `idf-${supplier.supplier_code}-${supplier.supplier_store}.xlsx`
    : "idf-fornecedores.xlsx";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1500);
}
