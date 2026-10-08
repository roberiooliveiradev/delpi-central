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
  scheduled_end_date: string | null;
  scheduled_end_time: string | null;
  production_order: string;
  operation_code: string;
  operation_description: string;
  tool: string;
  resource: string | null;
  product_code: string;
  product_description: string;
  unit: string | null;
  pieces_conversion_factor?: number | null;
  planned_qty: number;
  produced_qty: number;
  /** Saldo do cabeçalho da OP (C2_QUANT − C2_QUJE) — igual em todas as operações. */
  pending_qty: number;
  /** Apontado na própria operação (SH6010); ausente em snapshot antigo. */
  operation_produced_qty?: number | null;
  /** Saldo da própria bancada; é ele que o operador precisa ver. */
  operation_pending_qty?: number | null;
  pa_product_code: string | null;
  pa_product_description: string | null;
  pa_due_date: string | null;
  due_date: string | null;
  production_status: ProductionStatus;
  is_in_production: boolean;
  production_started_date: string | null;
  production_started_time: string | null;
  active_operator_name: string | null;
  active_operator_count: number | null;
  appointment_count: number | null;
  last_appointment_date: string | null;
  has_3d_model?: boolean;
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

export function buildPublicProductModelGlbUrl(
  token: string,
  branch: string,
  productCode: string,
): string {
  const params = new URLSearchParams({ branch });
  return `${API_BASE}/public/machine-load/${encodeURIComponent(token)}/models/${encodeURIComponent(productCode)}/glb?${params}`;
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
    throw new Error(await readError(response, "Desenho não encontrado para este produto."));
  }
  return response.blob();
}

export type FactoryShift = {
  id: string;
  label: string;
  start_time: string;
  end_time: string;
};

export type EfficiencySeriesPoint = {
  date: string;
  efficiency_pct: number | null;
  appointment_count: number | null;
};

export type WorkCenterAppointment = {
  production_order: string;
  operation: string;
  operation_description: string;
  pa_product_code: string | null;
  product_code: string;
  operator_name: string | null;
  quantity: number | null;
  real_hours: number | null;
  planned_hours: number | null;
  efficiency_pct: number | null;
  start_time: string;
  end_time: string;
};

export type DowntimeReason = {
  stop_reason: string;
  stop_reason_description: string;
  hours: number;
  appointment_count: number | null;
};

export type DowntimeSeriesPoint = {
  date: string;
  hours: number;
  appointment_count: number | null;
};

/** Cada bloco degrada sozinho: a api-delpi pode cair sem derrubar a fila. */
export type PerformanceBlock<T> = ({ available: true } & T) | { available: false; message?: string };

export type WorkCenterEfficiency = {
  shift_pct: number | null;
  shift_appointment_count: number | null;
  /** Soma de ``qtd_apontada`` dos apontamentos do turno atual (dia + shift). */
  shift_produced_qty: number | null;
  day_pct: number | null;
  day_appointment_count: number | null;
  period_avg_pct: number | null;
  series: EfficiencySeriesPoint[];
  appointments: WorkCenterAppointment[];
};

export type WorkCenterDowntime = {
  today_hours: number;
  today_appointment_count: number | null;
  period_hours: number;
  period_appointment_count: number;
  by_reason: DowntimeReason[];
  series: DowntimeSeriesPoint[];
};

export type PublicWorkCenterPerformance = {
  branch: string;
  work_center: string;
  resources: string[];
  days: number;
  period: { start_date: string; end_date: string };
  generated_at: string;
  shift: FactoryShift | null;
  efficiency: PerformanceBlock<WorkCenterEfficiency>;
  downtime: PerformanceBlock<WorkCenterDowntime>;
};

export async function fetchPublicWorkCenterPerformance(
  token: string,
  branch: string,
  workCenter: string,
  days?: number,
): Promise<PublicWorkCenterPerformance> {
  const params = new URLSearchParams({ branch, workCenter });
  if (days) params.set("days", String(days));

  const response = await fetch(
    `${API_BASE}/public/machine-load/${encodeURIComponent(token)}/performance?${params}`,
    { headers: { Accept: "application/json" } },
  );
  if (!response.ok) {
    throw new Error(await readError(response, "Desempenho do posto indisponível."));
  }
  const envelope = (await response.json()) as ApiEnvelope<PublicWorkCenterPerformance>;
  if (envelope.success === false || !envelope.data) {
    throw new Error(envelope.message || "Desempenho do posto indisponível.");
  }
  return envelope.data;
}

export type PublicDowntimeItem = {
  reference_date: string | null;
  production_order: string | null;
  operation: string | null;
  resource: string | null;
  operator_name: string | null;
  stop_reason: string | null;
  stop_reason_description: string | null;
  observation: string | null;
  hours: number | null;
};

export type PublicWorkCenterDowntimeItems = {
  branch: string;
  work_center: string;
  resources: string[];
  period: { start_date: string; end_date: string };
  shift: FactoryShift | null;
  items: PublicDowntimeItem[];
  summary: {
    appointment_count: number;
    total_hours: number;
  };
};

export async function fetchPublicWorkCenterDowntimeItems(
  token: string,
  branch: string,
  workCenter: string,
): Promise<PublicWorkCenterDowntimeItems> {
  const params = new URLSearchParams({ branch, workCenter });
  const response = await fetch(
    `${API_BASE}/public/machine-load/${encodeURIComponent(token)}/performance/downtime-items?${params}`,
    { headers: { Accept: "application/json" } },
  );
  if (!response.ok) {
    throw new Error(await readError(response, "Paradas do turno indisponíveis."));
  }
  const envelope = (await response.json()) as ApiEnvelope<PublicWorkCenterDowntimeItems>;
  if (envelope.success === false || !envelope.data) {
    throw new Error(envelope.message || "Paradas do turno indisponíveis.");
  }
  return envelope.data;
}

export type PublicOperationAppointment = {
  produced_on: string | null;
  start_time: string | null;
  end_time: string | null;
  quantity: number | null;
  unit: string | null;
  work_center: string | null;
  operator_name: string | null;
};

export type PublicOperationAppointments = {
  branch: string;
  production_order: string;
  operation_code: string;
  period: { start_date: string; end_date: string };
  items: PublicOperationAppointment[];
  summary: {
    appointment_count: number;
    produced_qty: number | null;
  };
};

export async function fetchPublicOperationAppointments(
  token: string,
  branch: string,
  productionOrder: string,
  operationCode: string,
): Promise<PublicOperationAppointments> {
  const params = new URLSearchParams({
    branch,
    productionOrder,
    operationCode,
  });
  const response = await fetch(
    `${API_BASE}/public/machine-load/${encodeURIComponent(token)}/operations/appointments?${params}`,
    { headers: { Accept: "application/json" } },
  );
  if (!response.ok) {
    throw new Error(await readError(response, "Apontamentos indisponíveis."));
  }
  const envelope = (await response.json()) as ApiEnvelope<PublicOperationAppointments>;
  if (envelope.success === false || !envelope.data) {
    throw new Error(envelope.message || "Apontamentos indisponíveis.");
  }
  return envelope.data;
}

export type PublicOperationMaterial = {
  product_code: string;
  description: string;
  unit: string;
  original_qty: number;
  open_qty: number;
  consumed_qty: number;
  commitment_count: number;
};

export type PublicOperationMaterials = {
  branch: string;
  production_order: string;
  operation_code: string;
  items: PublicOperationMaterial[];
  summary: {
    material_count: number;
    commitment_count: number;
  };
};

export function buildPublicOperationMaterialsUrl(
  token: string,
  branch: string,
  productionOrder: string,
  operationCode: string,
): string {
  const params = new URLSearchParams({
    branch,
    productionOrder,
    operationCode,
  });
  return `${API_BASE}/public/machine-load/${encodeURIComponent(token)}/operations/materials?${params}`;
}

export async function fetchPublicOperationMaterials(
  token: string,
  branch: string,
  productionOrder: string,
  operationCode: string,
): Promise<PublicOperationMaterials> {
  const response = await fetch(
    buildPublicOperationMaterialsUrl(token, branch, productionOrder, operationCode),
    { headers: { Accept: "application/json" } },
  );
  if (!response.ok) {
    throw new Error(await readError(response, "Materiais da operação indisponíveis."));
  }
  const envelope = (await response.json()) as ApiEnvelope<PublicOperationMaterials>;
  if (envelope.success === false || !envelope.data) {
    throw new Error(envelope.message || "Materiais da operação indisponíveis.");
  }
  return envelope.data;
}

export type PublicOperationProcessInspection = {
  inspector_name: string;
  measurement_date: string | null;
  measurement_time: string | null;
  result: string;
  result_code: string;
};

export type PublicOperationProcessInspections = {
  branch: string;
  production_order: string;
  operation_code: string;
  items: PublicOperationProcessInspection[];
  summary: {
    inspection_count: number;
  };
};

export function buildPublicOperationProcessInspectionsUrl(
  token: string,
  branch: string,
  productionOrder: string,
  operationCode: string,
): string {
  const params = new URLSearchParams({
    branch,
    productionOrder,
    operationCode,
  });
  return `${API_BASE}/public/machine-load/${encodeURIComponent(token)}/operations/process-inspections?${params}`;
}

export async function fetchPublicOperationProcessInspections(
  token: string,
  branch: string,
  productionOrder: string,
  operationCode: string,
): Promise<PublicOperationProcessInspections> {
  const response = await fetch(
    buildPublicOperationProcessInspectionsUrl(token, branch, productionOrder, operationCode),
    { headers: { Accept: "application/json" } },
  );
  if (!response.ok) {
    throw new Error(await readError(response, "Inspeções da operação indisponíveis."));
  }
  const envelope = (await response.json()) as ApiEnvelope<PublicOperationProcessInspections>;
  if (envelope.success === false || !envelope.data) {
    throw new Error(envelope.message || "Inspeções da operação indisponíveis.");
  }
  return envelope.data;
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
    throw new Error(await readError(response, "Desenho não encontrado para este produto."));
  }
  return response.blob();
}

export type ProductionRunSnapshot = {
  id: string;
  branch: string;
  workCenter: string;
  productionOrder: string;
  operationCode: string;
  deviceId: string;
  operatorCode: string;
  operatorName: string | null;
  status: "running" | "paused" | "completed" | "aborted";
  startedAt: string | null;
  endedAt: string | null;
  piecesTotal: number;
  plannedQty: number | null;
  targetPieces: number | null;
  remainingPieces: number | null;
  progressPercent: number | null;
  targetReached: boolean;
  overproductionPieces: number | null;
  countedPieces?: number;
  totvsProducedQty?: number | null;
  /** Divergência na unidade de leitura do operador (peças ÷ fator − produzido TOTVS). */
  divergencePieces?: number | null;
  /** Fator canônico peças→unidade da operação (MI = 1000), vindo da fila publicada. */
  piecesConversionFactor?: number | null;
  device?: {
    deviceId?: string;
    name?: string | null;
    counter?: number | null;
    counterEpoch?: number | null;
    online?: boolean;
    status?: string | null;
    lastSeenAt?: string | null;
    pollIntervalMs?: number | null;
  } | null;
  /** Parada MES atualmente aberta — existe também com `status: "running"`
   * quando a parada foi detectada automaticamente por ausência de peças. */
  downtime?: RunDowntimeView | null;
  /** Estado operacional aberto do run ("producing" | "stopped" | ...). */
  operationalState?: string | null;
  /** Parada já encerrada ainda sem motivo — cockpit deve oferecer a
   * classificação mesmo com a máquina produzindo (sobrevive a F5). */
  pendingDowntime?: RunDowntimeView | null;
  pendingDowntimeCount?: number;
};

/** Parada MES aberta do run (fato realtime — diferente das paradas TOTVS). */
export type RunDowntimeView = {
  id: string;
  runId: string;
  reasonCode: string | null;
  reasonLabel: string | null;
  category: string | null;
  note: string | null;
  confirmed: boolean;
  /** "operator_pause" (manual) | "system" (parada automática por inatividade). */
  source?: string | null;
  startedAt: string | null;
  endedAt: string | null;
};

/** Motivo de parada do catálogo MES (`downtime_reason_catalog`). */
export type MesDowntimeReason = {
  code: string;
  label: string;
  category: string | null;
  requiresNote: boolean;
};

/** Item da timeline operacional do run (Etapa 04). */
export type RunTimelineItem = {
  id: string;
  state: "producing" | "stopped" | "setup" | "idle" | "planned_stop" | string;
  startedAt: string;
  endedAt: string | null;
  durationSeconds: number;
  source: string | null;
  downtime: {
    id: string;
    reasonCode: string | null;
    reasonLabel: string | null;
    category: string | null;
    note: string | null;
    confirmed: boolean;
    source?: string | null;
  } | null;
};

export type RunTimeline = {
  runId: string;
  branch: string;
  workCenter: string;
  status: string;
  /** Horário atual do backend em UTC — base do relógio do cockpit. */
  referenceAt: string;
  summary: {
    elapsedSeconds: number;
    producingSeconds: number;
    stoppedSeconds: number;
    stopCount: number;
  };
  items: RunTimelineItem[];
};

export type BenchSessionSnapshot = {
  sessionToken: string;
  expiresAt: string | null;
  branch: string;
  workCenter: string;
  operatorCode: string;
  operatorName: string | null;
};

const BENCH_SESSION_HEADER = "X-Delpi-Bench-Session";

/** Erro de API com status HTTP preservado (ex.: 401 = sessão expirada). */
export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export function isAuthError(err: unknown): boolean {
  return err instanceof ApiError && err.status === 401;
}

async function readEnvelope<T>(response: Response, fallback: string): Promise<T> {
  if (!response.ok) {
    throw new ApiError(await readError(response, fallback), response.status);
  }
  const envelope = (await response.json()) as ApiEnvelope<T>;
  if (envelope.success === false) {
    throw new ApiError(envelope.message || fallback, response.status);
  }
  return envelope.data;
}

export async function createBenchSession(
  token: string,
  body: {
    branch: string;
    workCenter: string;
    /** Matrícula oficial do colaborador — o nome vem do Portal RH (C4). */
    registration: string;
  },
): Promise<BenchSessionSnapshot> {
  const response = await fetch(
    `${API_BASE}/public/machine-load/${encodeURIComponent(token)}/bench-sessions`,
    {
      method: "POST",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: JSON.stringify({
        branch: body.branch,
        workCenter: body.workCenter,
        registration: body.registration,
        website: "",
      }),
    },
  );
  return readEnvelope<BenchSessionSnapshot>(response, "Não foi possível identificar o operador.");
}

/**
 * Restore do cockpit: devolve a bench-session persistida — sem lookup no
 * Portal RH. 401 (ApiError) = sessão inválida/expirada/encerrada.
 */
export async function fetchCurrentBenchSession(
  token: string,
  sessionToken: string,
): Promise<BenchSessionSnapshot> {
  const response = await fetch(
    `${API_BASE}/public/machine-load/${encodeURIComponent(token)}/bench-sessions/current`,
    {
      headers: {
        Accept: "application/json",
        [BENCH_SESSION_HEADER]: sessionToken,
      },
    },
  );
  return readEnvelope<BenchSessionSnapshot>(response, "Sessão inválida.");
}

export async function endBenchSession(token: string, sessionToken: string): Promise<void> {
  const response = await fetch(
    `${API_BASE}/public/machine-load/${encodeURIComponent(token)}/bench-sessions/current`,
    {
      method: "DELETE",
      headers: {
        Accept: "application/json",
        [BENCH_SESSION_HEADER]: sessionToken,
      },
    },
  );
  await readEnvelope<{ ended: boolean }>(response, "Não foi possível encerrar a sessão.");
}

export async function fetchMesDowntimeReasons(token: string): Promise<MesDowntimeReason[]> {
  const response = await fetch(
    `${API_BASE}/public/machine-load/${encodeURIComponent(token)}/mes/downtime-reasons`,
    { headers: { Accept: "application/json" } },
  );
  const data = await readEnvelope<{ items: MesDowntimeReason[] }>(
    response,
    "Motivos de parada indisponíveis.",
  );
  return data.items ?? [];
}

/** Parada MES encerrada do posto ainda sem motivo (inclui runs finalizados). */
export type PendingMesDowntime = {
  id: string;
  runId: string | null;
  productionOrder: string | null;
  operationCode: string | null;
  source: string | null;
  reasonCode: string | null;
  note: string | null;
  confirmed: boolean;
  startedAt: string | null;
  endedAt: string | null;
  durationSeconds: number;
};

export async function fetchPendingMesDowntimes(
  token: string,
  sessionToken: string,
  branch: string,
  workCenter: string,
): Promise<PendingMesDowntime[]> {
  const params = new URLSearchParams({ branch, workCenter });
  const response = await fetch(
    `${API_BASE}/public/machine-load/${encodeURIComponent(token)}/mes/downtimes/pending?${params}`,
    {
      headers: {
        Accept: "application/json",
        [BENCH_SESSION_HEADER]: sessionToken,
      },
    },
  );
  const data = await readEnvelope<{ items: PendingMesDowntime[] }>(
    response,
    "Paradas sem motivo indisponíveis.",
  );
  return data.items ?? [];
}

export async function classifyRunDowntime(
  token: string,
  sessionToken: string,
  runId: string,
  body: { reasonCode: string; note?: string | null; downtimeId?: string | null },
): Promise<RunDowntimeView> {
  const path = body.downtimeId
    ? `${API_BASE}/public/machine-load/${encodeURIComponent(token)}/runs/${encodeURIComponent(runId)}/downtimes/${encodeURIComponent(body.downtimeId)}/classify`
    : `${API_BASE}/public/machine-load/${encodeURIComponent(token)}/runs/${encodeURIComponent(runId)}/downtime/classify`;
  const response = await fetch(
    path,
    {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        [BENCH_SESSION_HEADER]: sessionToken,
      },
      body: JSON.stringify({
        reasonCode: body.reasonCode,
        note: body.note ?? null,
        website: "",
      }),
    },
  );
  return readEnvelope<RunDowntimeView>(response, "Não foi possível registrar o motivo.");
}

export async function fetchRunTimeline(
  token: string,
  sessionToken: string,
  runId: string,
): Promise<RunTimeline> {
  const response = await fetch(
    `${API_BASE}/public/machine-load/${encodeURIComponent(token)}/runs/${encodeURIComponent(runId)}/timeline`,
    {
      headers: {
        Accept: "application/json",
        [BENCH_SESSION_HEADER]: sessionToken,
      },
    },
  );
  return readEnvelope<RunTimeline>(response, "Linha do tempo indisponível.");
}

export async function fetchActiveProductionRun(
  token: string,
  branch: string,
  workCenter: string,
): Promise<ProductionRunSnapshot | null> {
  const params = new URLSearchParams({ branch, workCenter });
  const response = await fetch(
    `${API_BASE}/public/machine-load/${encodeURIComponent(token)}/runs/active?${params}`,
    { headers: { Accept: "application/json" } },
  );
  return readEnvelope<ProductionRunSnapshot | null>(response, "Contagem indisponível.");
}

export async function startProductionRun(
  token: string,
  sessionToken: string,
  body: {
    branch: string;
    workCenter: string;
    productionOrder: string;
    operationCode: string;
  },
): Promise<ProductionRunSnapshot> {
  const response = await fetch(
    `${API_BASE}/public/machine-load/${encodeURIComponent(token)}/runs`,
    {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        [BENCH_SESSION_HEADER]: sessionToken,
      },
      body: JSON.stringify({
        branch: body.branch,
        workCenter: body.workCenter,
        productionOrder: body.productionOrder,
        operationCode: body.operationCode,
        website: "",
      }),
    },
  );
  return readEnvelope<ProductionRunSnapshot>(response, "Não foi possível iniciar a produção.");
}

export async function pauseProductionRun(
  token: string,
  sessionToken: string,
  runId: string,
): Promise<ProductionRunSnapshot> {
  const response = await fetch(
    `${API_BASE}/public/machine-load/${encodeURIComponent(token)}/runs/${encodeURIComponent(runId)}/pause`,
    {
      method: "POST",
      headers: {
        Accept: "application/json",
        [BENCH_SESSION_HEADER]: sessionToken,
      },
    },
  );
  return readEnvelope<ProductionRunSnapshot>(response, "Não foi possível pausar.");
}

export async function resumeProductionRun(
  token: string,
  sessionToken: string,
  runId: string,
): Promise<ProductionRunSnapshot> {
  const response = await fetch(
    `${API_BASE}/public/machine-load/${encodeURIComponent(token)}/runs/${encodeURIComponent(runId)}/resume`,
    {
      method: "POST",
      headers: {
        Accept: "application/json",
        [BENCH_SESSION_HEADER]: sessionToken,
      },
    },
  );
  return readEnvelope<ProductionRunSnapshot>(response, "Não foi possível retomar.");
}

export async function stopProductionRun(
  token: string,
  sessionToken: string,
  runId: string,
): Promise<ProductionRunSnapshot> {
  const response = await fetch(
    `${API_BASE}/public/machine-load/${encodeURIComponent(token)}/runs/${encodeURIComponent(runId)}/stop`,
    {
      method: "POST",
      headers: {
        Accept: "application/json",
        [BENCH_SESSION_HEADER]: sessionToken,
      },
    },
  );
  return readEnvelope<ProductionRunSnapshot>(response, "Não foi possível encerrar.");
}

/* ---------- Operator Feedback (C3) — impedimentos do operador ao PCP ---------- */

export type OperatorFeedbackStatus = "open" | "acknowledged" | "resolved";

export type OperatorFeedbackMaterialStatus = "pending" | "picked" | "delivered";

/** Material informado como faltante (C5) — snapshot congelado no backend. */
export type PublicOperatorFeedbackMaterial = {
  productCode: string;
  description: string;
  unit: string;
  status: OperatorFeedbackMaterialStatus;
};

export type PublicOperatorFeedback = {
  id: string;
  productionOrder: string;
  operationCode: string;
  reportedWorkCenter: string;
  feedbackType: string;
  reasonCode: string;
  note: string | null;
  status: OperatorFeedbackStatus;
  createdAt: string;
  acknowledgedAt: string | null;
  resolvedAt: string | null;
  /** C5: ausente/vazio em feedbacks antigos (C1–C4). */
  materials?: PublicOperatorFeedbackMaterial[];
};

/**
 * Impedimentos ativos (open|acknowledged) da OP/operação — identidade e posto
 * vêm da bench session; resolved não entra na coleção.
 */
export async function fetchActiveOperatorFeedbacks(
  token: string,
  sessionToken: string,
  productionOrder: string,
  operationCode: string,
): Promise<PublicOperatorFeedback[]> {
  const params = new URLSearchParams({
    productionOrder,
    operationCode,
  });
  const path =
    API_BASE +
    "/public/machine-load/" +
    encodeURIComponent(token) +
    "/operator-feedbacks/active?" +
    params;
  const response = await fetch(path, {
    headers: {
      Accept: "application/json",
      [BENCH_SESSION_HEADER]: sessionToken,
    },
  });
  const data = await readEnvelope<{ items: PublicOperatorFeedback[] }>(
    response,
    "Avisos ao PCP indisponíveis.",
  );
  return data.items ?? [];
}

/**
 * Registra impedimento ao PCP. O corpo vai só com OP/operação/tipo/motivo/nota:
 * identidade, filial, posto e contexto da OP são resolvidos no backend (C2).
 */
export async function createOperatorFeedback(
  token: string,
  sessionToken: string,
  body: {
    productionOrder: string;
    operationCode: string;
    feedbackType: string;
    reasonCode: string;
    /** C5: apenas códigos — descrição/unidade/saldo são relidos na SD4. */
    materialCodes?: string[];
    note?: string | null;
  },
): Promise<PublicOperatorFeedback> {
  const path =
    API_BASE +
    "/public/machine-load/" +
    encodeURIComponent(token) +
    "/operator-feedbacks";
  const response = await fetch(path, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      [BENCH_SESSION_HEADER]: sessionToken,
    },
    body: JSON.stringify({
      productionOrder: body.productionOrder,
      operationCode: body.operationCode,
      feedbackType: body.feedbackType,
      reasonCode: body.reasonCode,
      materialCodes: body.materialCodes ?? [],
      note: body.note ?? null,
      website: "",
    }),
  });
  return readEnvelope<PublicOperatorFeedback>(
    response,
    "Não foi possível enviar o aviso ao PCP.",
  );
}
