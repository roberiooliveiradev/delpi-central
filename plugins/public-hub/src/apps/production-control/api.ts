const API_BASE = "/apps/production-control-api";

export type ProductionStatus = "in_progress" | "started" | "not_started";

export type MachineLoadWorkCenter = {
  work_center: string;
  work_center_name: string;
  operation_count: number;
  order_count: number;
  in_production_count: number;
  first_scheduled_date?: string | null;
  last_scheduled_date?: string | null;
};

export type MachineLoadOperation = {
  work_center: string;
  work_center_name: string;
  scheduled_date: string | null;
  scheduled_start_time: string | null;
  production_order: string;
  operation_code: string;
  operation_description: string;
  tool: string;
  product_code: string;
  product_description: string;
  unit: string | null;
  planned_qty: number;
  pending_qty: number;
  pa_product_code: string | null;
  pa_due_date: string | null;
  production_status: ProductionStatus;
  is_in_production: boolean;
  production_started_time: string | null;
  active_operator_name: string | null;
};

export type PublicMachineLoadPayload = {
  branch: string;
  period: { start_date: string; end_date: string };
  summary: {
    work_center_count: number;
    operation_count: number;
    order_count: number;
    in_production_count: number;
  };
  snapshot: {
    refreshed_at: string | null;
    seeded: boolean;
    sequence_updated_at?: string | null;
  };
  work_centers: MachineLoadWorkCenter[];
  selected: {
    work_center: string | null;
    requested_work_center: string | null;
    items: MachineLoadOperation[];
  };
};

type ApiEnvelope<T> = {
  success: boolean;
  message?: string;
  data: T;
};

async function readError(response: Response, fallback: string): Promise<string> {
  try {
    const body = (await response.json()) as { message?: string };
    if (body.message) return body.message;
  } catch {
    /* ignore */
  }
  return fallback;
}

export async function fetchPublicMachineLoad(
  token: string,
  branch: string,
  workCenter?: string | null,
): Promise<PublicMachineLoadPayload> {
  const params = new URLSearchParams({ branch });
  if (workCenter) params.set("workCenter", workCenter);

  const response = await fetch(
    `${API_BASE}/public/machine-load/${encodeURIComponent(token)}?${params}`,
    { headers: { Accept: "application/json" } },
  );
  if (!response.ok) {
    throw new Error(await readError(response, "Fila de produção indisponível."));
  }
  const envelope = (await response.json()) as ApiEnvelope<PublicMachineLoadPayload>;
  if (envelope.success === false || !envelope.data) {
    throw new Error(envelope.message || "Fila de produção indisponível.");
  }
  return envelope.data;
}

export function buildPublicMachineLoadWsUrl(token: string, branch: string): string {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const path = `${API_BASE}/public/machine-load/${encodeURIComponent(token)}/ws`;
  return `${protocol}//${window.location.host}${path}?branch=${encodeURIComponent(branch)}`;
}

export function buildPublicDrawingPdfUrl(token: string, branch: string, paCode: string): string {
  const params = new URLSearchParams({ branch });
  return `${API_BASE}/public/machine-load/${encodeURIComponent(token)}/drawings/${encodeURIComponent(paCode)}/pdf?${params}`;
}

export async function fetchPublicDrawingPdf(
  token: string,
  branch: string,
  paCode: string,
): Promise<Blob> {
  const response = await fetch(buildPublicDrawingPdfUrl(token, branch, paCode), {
    headers: { Accept: "application/pdf" },
  });
  if (!response.ok) {
    throw new Error(await readError(response, "Desenho não encontrado para este PA."));
  }
  return response.blob();
}

export type DeliveryMapRow = {
  production_order: string;
  product_code: string;
  product_description: string | null;
  due_date: string | null;
  planned_qty: number;
  produced_qty: number;
  pending_qty: number;
  observation: string | null;
  days_late: number;
  is_delayed: boolean;
  mp_ok: boolean;
  work_center: string;
  is_reported: boolean;
};

export type DeliveryMapSection = {
  section_key: string;
  label: string;
  due_date: string | null;
  row_count: number;
  rows: DeliveryMapRow[];
};

export type DeliveryMapOpProgress = {
  conjunto_key: string;
  total: number;
  completed: number;
  in_progress: number;
  percent: number;
};

export type PublicDeliveryMapPayload = {
  branch: string;
  sections: DeliveryMapSection[];
  summary: { order_count: number; section_count: number };
  filters: { search: string };
  snapshot: {
    refreshed_at: string | null;
    horizon_end: string | null;
    seeded: boolean;
  };
};

export async function fetchPublicDeliveryMap(
  token: string,
  branch: string,
  search = "",
): Promise<PublicDeliveryMapPayload> {
  const params = new URLSearchParams({ branch });
  if (search.trim()) params.set("search", search.trim());

  const response = await fetch(
    `${API_BASE}/public/delivery-map/${encodeURIComponent(token)}?${params}`,
    { headers: { Accept: "application/json" } },
  );
  if (!response.ok) {
    throw new Error(await readError(response, "Mapa de entrega indisponível."));
  }
  const envelope = (await response.json()) as ApiEnvelope<PublicDeliveryMapPayload>;
  if (envelope.success === false || !envelope.data) {
    throw new Error(envelope.message || "Mapa de entrega indisponível.");
  }
  return envelope.data;
}

export async function fetchPublicDeliveryMapProgress(
  token: string,
  branch: string,
  orders: readonly string[],
): Promise<Record<string, DeliveryMapOpProgress>> {
  if (orders.length === 0) return {};
  const params = new URLSearchParams({ branch, orders: orders.join(",") });
  const response = await fetch(
    `${API_BASE}/public/delivery-map/${encodeURIComponent(token)}/progress?${params}`,
    { headers: { Accept: "application/json" } },
  );
  if (!response.ok) {
    throw new Error(await readError(response, "Progresso indisponível."));
  }
  const envelope = (await response.json()) as ApiEnvelope<{ items: Record<string, DeliveryMapOpProgress> }>;
  if (envelope.success === false || !envelope.data) {
    throw new Error(envelope.message || "Progresso indisponível.");
  }
  return envelope.data.items ?? {};
}

export function buildPublicDeliveryMapDrawingPdfUrl(
  token: string,
  branch: string,
  paCode: string,
): string {
  const params = new URLSearchParams({ branch });
  return `${API_BASE}/public/delivery-map/${encodeURIComponent(token)}/drawings/${encodeURIComponent(paCode)}/pdf?${params}`;
}

export async function fetchPublicDeliveryMapDrawingPdf(
  token: string,
  branch: string,
  paCode: string,
): Promise<Blob> {
  const response = await fetch(buildPublicDeliveryMapDrawingPdfUrl(token, branch, paCode), {
    headers: { Accept: "application/pdf" },
  });
  if (!response.ok) {
    throw new Error(await readError(response, "Desenho não encontrado para este PA."));
  }
  return response.blob();
}
