import { httpDelete, httpGet, httpGetBlob, httpPatch, httpPost, httpPut, httpPutFormData, ppcApiUrl, unwrapEnvelope } from "./httpClient";
import type {
  DeliveryMapPayload,
  DeliveryMapProgressPayload,
  DemandPayload,
  MachineLoadLiveStatusPayload,
  MachineLoadLocatePayload,
  MachineLoadOptimizePayload,
  MachineLoadPayload,
  MachineLoadPrioritizePayload,
  MachineLoadTransferPayload,
  MachineLoadWithdrawPayload,
  FinishedProductShortagePayload,
  LineFeederItemStatus,
  LineFeederPickItem,
  LineFeederPickPlan,
  LineFeederPickPlanListPayload,
  LineFeederPickPlanPayload,
  LineFeederRequirementsPayload,
  MaterialsPayload,
  OverviewPayload,
  ProblemDetectorItemsPayload,
  ProblemDetectorsPayload,
  Product3DModel,
  Product3DModelListPayload,
  ReportsCatalogPayload,
  StockBalancesReportPayload,
  ProductionOrdersReportPayload,
  Subplugin,
} from "../types";

export async function fetchSubplugins(signal?: AbortSignal): Promise<Subplugin[]> {
  const envelope = await httpGet<{ success: boolean; message?: string; data: { items: Subplugin[] } }>(
    ppcApiUrl("/subplugins"),
    { signal },
  );
  const data = unwrapEnvelope(envelope, "Não foi possível carregar os subplugins.");
  return data.items ?? [];
}

export async function fetchOverview(params: {
  branch: string;
  volumeView?: "day" | "month_yoy";
  startDate?: string | null;
  endDate?: string | null;
  signal?: AbortSignal;
}): Promise<OverviewPayload> {
  const search = new URLSearchParams({ branch: params.branch });
  if (params.volumeView) search.set("volumeView", params.volumeView);
  if (params.startDate) search.set("startDate", params.startDate);
  if (params.endDate) search.set("endDate", params.endDate);
  const envelope = await httpGet<{
    success: boolean;
    message?: string;
    data: OverviewPayload;
  }>(ppcApiUrl(`/overview?${search.toString()}`), { signal: params.signal });
  return unwrapEnvelope(envelope, "Não foi possível carregar a gestão à vista.");
}

export async function fetchReportsCatalog(params: {
  branch: string;
  signal?: AbortSignal;
}): Promise<ReportsCatalogPayload> {
  const search = new URLSearchParams({ branch: params.branch });
  const envelope = await httpGet<{
    success: boolean;
    message?: string;
    data: ReportsCatalogPayload;
  }>(ppcApiUrl(`/reports?${search.toString()}`), { signal: params.signal });
  return unwrapEnvelope(envelope, "Não foi possível carregar os relatórios.");
}

export async function fetchStockBalancesReport(params: {
  branch: string;
  search?: string;
  sort?: string | null;
  page?: number;
  pageSize?: number;
  refresh?: boolean;
  signal?: AbortSignal;
}): Promise<StockBalancesReportPayload> {
  const search = new URLSearchParams({ branch: params.branch });
  if (params.search) search.set("search", params.search);
  if (params.sort) search.set("sort", params.sort);
  if (params.page) search.set("page", String(params.page));
  if (params.pageSize) search.set("pageSize", String(params.pageSize));
  if (params.refresh) search.set("refresh", "true");
  const envelope = await httpGet<{
    success: boolean;
    message?: string;
    data: StockBalancesReportPayload;
  }>(ppcApiUrl(`/reports/stock-balances?${search.toString()}`), { signal: params.signal });
  return unwrapEnvelope(envelope, "Não foi possível carregar o relatório de saldos.");
}

export async function fetchProductionOrdersReport(params: {
  branch: string;
  opKey?: string;
  productCode?: string;
  motherOnly?: "yes" | "no" | "all";
  openOnly?: "yes" | "no" | "all";
  deliveryStart?: string | null;
  deliveryEnd?: string | null;
  actualEndStart?: string | null;
  actualEndEnd?: string | null;
  sort?: string | null;
  page?: number;
  pageSize?: number;
  signal?: AbortSignal;
}): Promise<ProductionOrdersReportPayload> {
  const search = new URLSearchParams({ branch: params.branch });
  if (params.opKey) search.set("opKey", params.opKey);
  if (params.productCode) search.set("productCode", params.productCode);
  if (params.motherOnly) search.set("motherOnly", params.motherOnly);
  if (params.openOnly) search.set("openOnly", params.openOnly);
  if (params.deliveryStart) search.set("deliveryStart", params.deliveryStart);
  if (params.deliveryEnd) search.set("deliveryEnd", params.deliveryEnd);
  if (params.actualEndStart) search.set("actualEndStart", params.actualEndStart);
  if (params.actualEndEnd) search.set("actualEndEnd", params.actualEndEnd);
  if (params.sort) search.set("sort", params.sort);
  if (params.page) search.set("page", String(params.page));
  if (params.pageSize) search.set("pageSize", String(params.pageSize));
  const envelope = await httpGet<{
    success: boolean;
    message?: string;
    data: ProductionOrdersReportPayload;
  }>(ppcApiUrl(`/reports/production-orders?${search.toString()}`), { signal: params.signal });
  return unwrapEnvelope(envelope, "Não foi possível carregar o relatório de ordens de produção.");
}

export type StockBalancesEmailSchedule = {
  branch: string;
  configured: boolean;
  enabled: boolean;
  hour: number;
  minute: number;
  timezone: string;
  scheduleKind: string;
  nextRunAt: string | null;
  definitionId: string | null;
};

export async function fetchStockBalancesEmailSchedule(params: {
  branch: string;
  signal?: AbortSignal;
}): Promise<StockBalancesEmailSchedule> {
  const search = new URLSearchParams({ branch: params.branch });
  const envelope = await httpGet<{
    success: boolean;
    message?: string;
    data: StockBalancesEmailSchedule;
  }>(ppcApiUrl(`/reports/stock-balances/email-schedule?${search.toString()}`), {
    signal: params.signal,
  });
  return unwrapEnvelope(envelope, "Não foi possível carregar o agendamento de e-mail.");
}

export async function saveStockBalancesEmailSchedule(params: {
  branch: string;
  hour: number;
  minute: number;
  enabled: boolean;
}): Promise<StockBalancesEmailSchedule> {
  const search = new URLSearchParams({ branch: params.branch });
  const envelope = await httpPut<{
    success: boolean;
    message?: string;
    data: StockBalancesEmailSchedule;
  }>(ppcApiUrl(`/reports/stock-balances/email-schedule?${search.toString()}`), {
    hour: params.hour,
    minute: params.minute,
    enabled: params.enabled,
  });
  return unwrapEnvelope(envelope, "Não foi possível salvar o agendamento de e-mail.");
}

export async function fetchDemand(params: {
  branch: string;
  search?: string;
  status?: string;
  dueFrom?: string | null;
  dueTo?: string | null;
  sort?: string | null;
  direction?: "asc" | "desc";
  page?: number;
  pageSize?: number;
  refresh?: boolean;
  signal?: AbortSignal;
}): Promise<DemandPayload> {
  const search = new URLSearchParams({ branch: params.branch });
  if (params.search) search.set("search", params.search);
  if (params.status) search.set("status", params.status);
  if (params.dueFrom) search.set("dueFrom", params.dueFrom);
  if (params.dueTo) search.set("dueTo", params.dueTo);
  if (params.sort) search.set("sort", params.sort);
  if (params.direction) search.set("direction", params.direction);
  if (params.page) search.set("page", String(params.page));
  if (params.pageSize) search.set("pageSize", String(params.pageSize));
  if (params.refresh) search.set("refresh", "true");
  const envelope = await httpGet<{
    success: boolean;
    message?: string;
    data: DemandPayload;
  }>(ppcApiUrl(`/demand?${search.toString()}`), { signal: params.signal });
  return unwrapEnvelope(envelope, "Não foi possível carregar a demanda.");
}

export async function fetchMaterials(params: {
  branch: string;
  view?: string | null;
  search?: string;
  sort?: string | null;
  direction?: "asc" | "desc";
  page?: number;
  pageSize?: number;
  refresh?: boolean;
  signal?: AbortSignal;
}): Promise<MaterialsPayload> {
  const search = new URLSearchParams({ branch: params.branch });
  if (params.view) search.set("view", params.view);
  if (params.search) search.set("search", params.search);
  if (params.sort) search.set("sort", params.sort);
  if (params.direction) search.set("direction", params.direction);
  if (params.page) search.set("page", String(params.page));
  if (params.pageSize) search.set("pageSize", String(params.pageSize));
  if (params.refresh) search.set("refresh", "true");
  const envelope = await httpGet<{
    success: boolean;
    message?: string;
    data: MaterialsPayload;
  }>(ppcApiUrl(`/materials?${search.toString()}`), { signal: params.signal });
  return unwrapEnvelope(envelope, "Não foi possível carregar os materiais.");
}

export async function fetchFinishedProductShortages(params: {
  branch: string;
  product: string;
  status?: string;
  refresh?: boolean;
  signal?: AbortSignal;
}): Promise<FinishedProductShortagePayload> {
  const search = new URLSearchParams({
    branch: params.branch,
    product: params.product,
  });
  if (params.status) search.set("status", params.status);
  if (params.refresh) search.set("refresh", "true");
  const envelope = await httpGet<{
    success: boolean;
    message?: string;
    data: FinishedProductShortagePayload;
  }>(ppcApiUrl(`/materials/finished-product-shortages?${search.toString()}`), {
    signal: params.signal,
  });
  return unwrapEnvelope(envelope, "Não foi possível consultar a ruptura no conjunto.");
}

export async function fetchDeliveryMap(params: {
  branch: string;
  search?: string;
  signal?: AbortSignal;
}): Promise<DeliveryMapPayload> {
  const search = new URLSearchParams({ branch: params.branch });
  if (params.search) search.set("search", params.search);
  const envelope = await httpGet<{
    success: boolean;
    message?: string;
    data: DeliveryMapPayload;
  }>(ppcApiUrl(`/delivery-map?${search.toString()}`), { signal: params.signal });
  return unwrapEnvelope(envelope, "Não foi possível carregar o mapa de entrega.");
}

export async function refreshDeliveryMap(params: {
  branch: string;
  search?: string;
  signal?: AbortSignal;
}): Promise<DeliveryMapPayload> {
  const search = new URLSearchParams({ branch: params.branch });
  if (params.search) search.set("search", params.search);
  const envelope = await httpPost<{
    success: boolean;
    message?: string;
    data: DeliveryMapPayload;
  }>(ppcApiUrl(`/delivery-map/refresh?${search.toString()}`), undefined, {
    signal: params.signal,
  });
  return unwrapEnvelope(envelope, "Não foi possível atualizar o mapa de entrega.");
}

export async function fetchDeliveryMapProgress(params: {
  branch: string;
  orders: readonly string[];
  signal?: AbortSignal;
}): Promise<DeliveryMapProgressPayload> {
  const search = new URLSearchParams({ branch: params.branch });
  if (params.orders.length > 0) {
    search.set("orders", params.orders.join(","));
  }
  const envelope = await httpGet<{
    success: boolean;
    message?: string;
    data: DeliveryMapProgressPayload;
  }>(ppcApiUrl(`/delivery-map/progress?${search.toString()}`), { signal: params.signal });
  return unwrapEnvelope(envelope, "Não foi possível carregar o progresso das OPs.");
}

export async function patchDeliveryMapOverrides(params: {
  branch: string;
  search?: string;
  updates: Array<{
    production_order: string;
    mp_ok?: boolean;
    work_center?: string;
  }>;
  signal?: AbortSignal;
}): Promise<DeliveryMapPayload> {
  const search = new URLSearchParams({ branch: params.branch });
  if (params.search) search.set("search", params.search);
  const envelope = await httpPatch<{
    success: boolean;
    message?: string;
    data: DeliveryMapPayload;
  }>(
    ppcApiUrl(`/delivery-map/overrides?${search.toString()}`),
    { updates: params.updates },
    { signal: params.signal },
  );
  return unwrapEnvelope(envelope, "Não foi possível salvar as marcações do mapa de entrega.");
}

export async function fetchDeliveryMapDrawingPdf(params: {
  branch: string;
  productCode: string;
  signal?: AbortSignal;
}): Promise<Blob> {
  const search = new URLSearchParams({ branch: params.branch });
  return httpGetBlob(
    ppcApiUrl(
      `/delivery-map/drawings/${encodeURIComponent(params.productCode)}/pdf?${search.toString()}`,
    ),
    { signal: params.signal },
  );
}

/**
 * A fila da filial é uma só — o centro de trabalho é recorte de apresentação.
 * Pedindo todos os centros, trocar de aba não custa nova leitura.
 */
function machineLoadSearch(init: Record<string, string>): URLSearchParams {
  const search = new URLSearchParams(init);
  search.set("includeAllCenters", "true");
  return search;
}

export async function fetchMachineLoad(params: {
  branch: string;
  workCenter?: string | null;
  startDate?: string | null;
  endDate?: string | null;
  signal?: AbortSignal;
}): Promise<MachineLoadPayload> {
  const search = machineLoadSearch({ branch: params.branch });
  if (params.workCenter) search.set("workCenter", params.workCenter);
  if (params.startDate) search.set("startDate", params.startDate);
  if (params.endDate) search.set("endDate", params.endDate);
  const envelope = await httpGet<{
    success: boolean;
    message?: string;
    data: MachineLoadPayload;
  }>(ppcApiUrl(`/machine-load?${search.toString()}`), { signal: params.signal });
  return unwrapEnvelope(envelope, "Não foi possível carregar a carga máquina.");
}

export async function refreshMachineLoad(params: {
  branch: string;
  workCenter?: string | null;
  startDate?: string | null;
  endDate?: string | null;
  signal?: AbortSignal;
}): Promise<MachineLoadPayload> {
  const search = machineLoadSearch({ branch: params.branch });
  if (params.workCenter) search.set("workCenter", params.workCenter);
  if (params.startDate) search.set("startDate", params.startDate);
  if (params.endDate) search.set("endDate", params.endDate);
  const envelope = await httpPost<{
    success: boolean;
    message?: string;
    data: MachineLoadPayload;
  }>(ppcApiUrl(`/machine-load/refresh?${search.toString()}`), undefined, {
    signal: params.signal,
  });
  return unwrapEnvelope(envelope, "Não foi possível atualizar a carga máquina.");
}

export async function patchMachineLoadSequence(params: {
  branch: string;
  workCenter: string;
  orderedKeys: Array<{ production_order: string; operation_code: string }>;
  signal?: AbortSignal;
}): Promise<MachineLoadPayload> {
  const search = machineLoadSearch({
    branch: params.branch,
    workCenter: params.workCenter,
  });
  const envelope = await httpPatch<{
    success: boolean;
    message?: string;
    data: MachineLoadPayload;
  }>(
    ppcApiUrl(`/machine-load/sequence?${search.toString()}`),
    { ordered_keys: params.orderedKeys },
    { signal: params.signal },
  );
  return unwrapEnvelope(envelope, "Não foi possível salvar a sequência da carga máquina.");
}

/** Leva todas as OPs do conjunto (C2_NUM) ao topo da fila de cada centro de trabalho. */
export async function prioritizeMachineLoadConjunto(params: {
  branch: string;
  orderNumber: string;
  workCenter?: string | null;
  signal?: AbortSignal;
}): Promise<MachineLoadPrioritizePayload> {
  const search = machineLoadSearch({
    branch: params.branch,
    orderNumber: params.orderNumber,
  });
  if (params.workCenter) search.set("workCenter", params.workCenter);
  const envelope = await httpPost<{
    success: boolean;
    message?: string;
    data: MachineLoadPrioritizePayload;
  }>(ppcApiUrl(`/machine-load/prioritize?${search.toString()}`), undefined, {
    signal: params.signal,
  });
  return unwrapEnvelope(envelope, "Não foi possível priorizar o conjunto.");
}

/** Reordena a fila de todos os centros pela entrega do PA, sem ultrapassar ops já iniciadas. */
export async function optimizeMachineLoadDeliverySequence(params: {
  branch: string;
  workCenter?: string | null;
  signal?: AbortSignal;
}): Promise<MachineLoadOptimizePayload> {
  const search = machineLoadSearch({ branch: params.branch });
  if (params.workCenter) search.set("workCenter", params.workCenter);
  const envelope = await httpPost<{
    success: boolean;
    message?: string;
    data: MachineLoadOptimizePayload;
  }>(ppcApiUrl(`/machine-load/optimize-delivery?${search.toString()}`), undefined, {
    signal: params.signal,
  });
  return unwrapEnvelope(envelope, "Não foi possível otimizar a fila pela entrega do PA.");
}

/** Tira o conjunto (C2_NUM) da programação: some da fila de todos os centros e do cockpit. */
export async function withdrawMachineLoadConjunto(params: {
  branch: string;
  orderNumber: string;
  workCenter?: string | null;
  signal?: AbortSignal;
}): Promise<MachineLoadWithdrawPayload> {
  return postMachineLoadWithdrawal("withdraw", params, "Não foi possível retirar o conjunto da programação.");
}

/** Devolve o conjunto retirado à fila, na posição original. */
export async function restoreMachineLoadConjunto(params: {
  branch: string;
  orderNumber: string;
  workCenter?: string | null;
  signal?: AbortSignal;
}): Promise<MachineLoadWithdrawPayload> {
  return postMachineLoadWithdrawal("restore", params, "Não foi possível devolver o conjunto à fila.");
}

async function postMachineLoadWithdrawal(
  action: "withdraw" | "restore",
  params: {
    branch: string;
    orderNumber: string;
    workCenter?: string | null;
    signal?: AbortSignal;
  },
  errorMessage: string,
): Promise<MachineLoadWithdrawPayload> {
  const search = machineLoadSearch({
    branch: params.branch,
    orderNumber: params.orderNumber,
  });
  if (params.workCenter) search.set("workCenter", params.workCenter);
  const envelope = await httpPost<{
    success: boolean;
    message?: string;
    data: MachineLoadWithdrawPayload;
  }>(ppcApiUrl(`/machine-load/${action}?${search.toString()}`), undefined, {
    signal: params.signal,
  });
  return unwrapEnvelope(envelope, errorMessage);
}

/** Move uma operação para o fim da fila de outro centro de trabalho. */
export async function transferMachineLoadOperation(params: {
  branch: string;
  productionOrder: string;
  operationCode: string;
  targetWorkCenter: string;
  workCenter?: string | null;
  signal?: AbortSignal;
}): Promise<MachineLoadTransferPayload> {
  const search = machineLoadSearch({
    branch: params.branch,
    productionOrder: params.productionOrder,
    operationCode: params.operationCode,
    targetWorkCenter: params.targetWorkCenter,
  });
  if (params.workCenter) search.set("workCenter", params.workCenter);
  const envelope = await httpPost<{
    success: boolean;
    message?: string;
    data: MachineLoadTransferPayload;
  }>(ppcApiUrl(`/machine-load/transfer?${search.toString()}`), undefined, {
    signal: params.signal,
  });
  return unwrapEnvelope(envelope, "Não foi possível transferir a operação de centro de trabalho.");
}

/** Move as OPs do conjunto que estão no centro de origem para o destino. */
export async function transferMachineLoadConjunto(params: {
  branch: string;
  orderNumber: string;
  sourceWorkCenter: string;
  targetWorkCenter: string;
  workCenter?: string | null;
  signal?: AbortSignal;
}): Promise<MachineLoadTransferPayload> {
  const search = machineLoadSearch({
    branch: params.branch,
    orderNumber: params.orderNumber,
    sourceWorkCenter: params.sourceWorkCenter,
    targetWorkCenter: params.targetWorkCenter,
  });
  if (params.workCenter) search.set("workCenter", params.workCenter);
  const envelope = await httpPost<{
    success: boolean;
    message?: string;
    data: MachineLoadTransferPayload;
  }>(ppcApiUrl(`/machine-load/transfer-set?${search.toString()}`), undefined, {
    signal: params.signal,
  });
  return unwrapEnvelope(
    envelope,
    "Não foi possível transferir o conjunto para outro centro de trabalho.",
  );
}

/** Status de apontamento vivo (HZA) da fila — aplicado sobre a fila já na tela. */
export async function fetchMachineLoadLiveStatus(params: {
  branch: string;
  signal?: AbortSignal;
}): Promise<MachineLoadLiveStatusPayload> {
  const search = new URLSearchParams({ branch: params.branch });
  const envelope = await httpGet<{
    success: boolean;
    message?: string;
    data: MachineLoadLiveStatusPayload;
  }>(ppcApiUrl(`/machine-load/live-status?${search.toString()}`), { signal: params.signal });
  return unwrapEnvelope(envelope, "Não foi possível atualizar o status da fila.");
}

export async function fetchMachineLoadLocate(params: {
  branch: string;
  query: string;
  signal?: AbortSignal;
}): Promise<MachineLoadLocatePayload> {
  const search = new URLSearchParams({
    branch: params.branch,
    q: params.query,
  });
  const envelope = await httpGet<{
    success: boolean;
    message?: string;
    data: MachineLoadLocatePayload;
  }>(ppcApiUrl(`/machine-load/locate?${search.toString()}`), { signal: params.signal });
  return unwrapEnvelope(envelope, "Não foi possível rastrear a OP ou o conjunto.");
}

/** Cards da Análise de problemas — um por detector do catálogo. */
export async function fetchProblemDetectors(params: {
  branch: string;
  signal?: AbortSignal;
}): Promise<ProblemDetectorsPayload> {
  const search = new URLSearchParams({ branch: params.branch });
  const envelope = await httpGet<{
    success: boolean;
    message?: string;
    data: ProblemDetectorsPayload;
  }>(ppcApiUrl(`/problem-analysis?${search.toString()}`), { signal: params.signal });
  return unwrapEnvelope(envelope, "Não foi possível carregar a análise de problemas.");
}

export async function fetchProblemDetectorItems(params: {
  branch: string;
  detectorId: string;
  page?: number;
  pageSize?: number;
  signal?: AbortSignal;
}): Promise<ProblemDetectorItemsPayload> {
  const search = new URLSearchParams({ branch: params.branch });
  if (params.page) search.set("page", String(params.page));
  if (params.pageSize) search.set("pageSize", String(params.pageSize));
  const envelope = await httpGet<{
    success: boolean;
    message?: string;
    data: ProblemDetectorItemsPayload;
  }>(
    ppcApiUrl(
      `/problem-analysis/${encodeURIComponent(params.detectorId)}?${search.toString()}`,
    ),
    { signal: params.signal },
  );
  return unwrapEnvelope(envelope, "Não foi possível carregar os registros do detector.");
}

export async function fetchProduct3DModels(params: {
  search?: string;
  signal?: AbortSignal;
}): Promise<Product3DModelListPayload> {
  const search = new URLSearchParams();
  if (params.search) search.set("q", params.search);
  const suffix = search.toString() ? `?${search.toString()}` : "";
  const envelope = await httpGet<{
    success: boolean;
    message?: string;
    data: Product3DModelListPayload;
  }>(ppcApiUrl(`/product-3d-models${suffix}`), { signal: params.signal });
  return unwrapEnvelope(envelope, "Não foi possível carregar os modelos 3D.");
}

export async function upsertProduct3DModel(params: {
  productCode: string;
  file: File;
  signal?: AbortSignal;
}): Promise<Product3DModel> {
  const form = new FormData();
  form.append("file", params.file, params.file.name);
  const envelope = await httpPutFormData<{
    success: boolean;
    message?: string;
    data: Product3DModel;
  }>(ppcApiUrl(`/product-3d-models/${encodeURIComponent(params.productCode)}`), form, {
    signal: params.signal,
  });
  return unwrapEnvelope(envelope, "Não foi possível anexar o modelo 3D.");
}

export async function deleteProduct3DModel(params: {
  productCode: string;
  signal?: AbortSignal;
}): Promise<Product3DModel> {
  const envelope = await httpDelete<{
    success: boolean;
    message?: string;
    data: Product3DModel;
  }>(ppcApiUrl(`/product-3d-models/${encodeURIComponent(params.productCode)}`), {
    signal: params.signal,
  });
  return unwrapEnvelope(envelope, "Não foi possível excluir o modelo 3D.");
}

export async function fetchLineFeederRequirements(params: {
  branch: string;
  cutoffDate: string;
  cutoffTime?: string | null;
  workCenter?: string | null;
  status?: string | null;
  refresh?: boolean;
  signal?: AbortSignal;
}): Promise<LineFeederRequirementsPayload> {
  const search = new URLSearchParams({ branch: params.branch, cutoffDate: params.cutoffDate });
  if (params.cutoffTime) search.set("cutoffTime", params.cutoffTime);
  if (params.workCenter) search.set("workCenter", params.workCenter);
  if (params.status) search.set("status", params.status);
  if (params.refresh) search.set("refresh", "true");
  const envelope = await httpGet<{
    success: boolean;
    message?: string;
    data: LineFeederRequirementsPayload;
  }>(ppcApiUrl(`/line-feeder/requirements?${search.toString()}`), { signal: params.signal });
  return unwrapEnvelope(envelope, "Não foi possível carregar a necessidade das bancadas.");
}

export async function createLineFeederPickPlan(params: {
  branch: string;
  cutoffDate: string;
  cutoffTime?: string | null;
  workCenter?: string | null;
  signal?: AbortSignal;
}): Promise<LineFeederPickPlanPayload> {
  const envelope = await httpPost<{
    success: boolean;
    message?: string;
    data: LineFeederPickPlanPayload;
  }>(
    ppcApiUrl("/line-feeder/pick-plans"),
    {
      branch: params.branch,
      cutoffDate: params.cutoffDate,
      cutoffTime: params.cutoffTime || null,
      workCenter: params.workCenter || null,
    },
    { signal: params.signal },
  );
  return unwrapEnvelope(envelope, "Não foi possível gerar a lista de coleta.");
}

export async function fetchLineFeederPickPlans(params: {
  branch: string;
  status?: string | null;
  limit?: number;
  signal?: AbortSignal;
}): Promise<LineFeederPickPlanListPayload> {
  const search = new URLSearchParams({ branch: params.branch });
  if (params.status) search.set("status", params.status);
  if (params.limit) search.set("limit", String(params.limit));
  const envelope = await httpGet<{
    success: boolean;
    message?: string;
    data: LineFeederPickPlanListPayload;
  }>(ppcApiUrl(`/line-feeder/pick-plans?${search.toString()}`), { signal: params.signal });
  return unwrapEnvelope(envelope, "Não foi possível carregar as listas de coleta.");
}

export async function fetchLineFeederPickPlan(params: {
  branch: string;
  planId: string;
  signal?: AbortSignal;
}): Promise<LineFeederPickPlanPayload> {
  const search = new URLSearchParams({ branch: params.branch });
  const envelope = await httpGet<{
    success: boolean;
    message?: string;
    data: LineFeederPickPlanPayload;
  }>(
    ppcApiUrl(`/line-feeder/pick-plans/${encodeURIComponent(params.planId)}?${search.toString()}`),
    { signal: params.signal },
  );
  return unwrapEnvelope(envelope, "Não foi possível carregar a lista de coleta.");
}

export async function patchLineFeederPickItem(params: {
  branch: string;
  planId: string;
  itemId: string;
  status: LineFeederItemStatus;
  signal?: AbortSignal;
}): Promise<{ branch: string; plan_id: string; item: LineFeederPickItem }> {
  const envelope = await httpPatch<{
    success: boolean;
    message?: string;
    data: { branch: string; plan_id: string; item: LineFeederPickItem };
  }>(
    ppcApiUrl(
      `/line-feeder/pick-plans/${encodeURIComponent(params.planId)}/items/${encodeURIComponent(params.itemId)}`,
    ),
    { branch: params.branch, status: params.status },
    { signal: params.signal },
  );
  return unwrapEnvelope(envelope, "Não foi possível atualizar o item da coleta.");
}

export async function closeLineFeederPickPlan(params: {
  branch: string;
  planId: string;
  signal?: AbortSignal;
}): Promise<{ branch: string; plan: LineFeederPickPlan }> {
  const envelope = await httpPost<{
    success: boolean;
    message?: string;
    data: { branch: string; plan: LineFeederPickPlan };
  }>(
    ppcApiUrl(`/line-feeder/pick-plans/${encodeURIComponent(params.planId)}/close`),
    { branch: params.branch },
    { signal: params.signal },
  );
  return unwrapEnvelope(envelope, "Não foi possível fechar a lista de coleta.");
}
