import { httpGet, httpPatch, httpPost, ppcApiUrl, unwrapEnvelope } from "./httpClient";
import type {
  DemandPayload,
  MachineLoadLocatePayload,
  MachineLoadOptimizePayload,
  MachineLoadPayload,
  MachineLoadPrioritizePayload,
  MachineLoadTransferPayload,
  MachineLoadWithdrawPayload,
  OverviewPayload,
  ProblemDetectorItemsPayload,
  ProblemDetectorsPayload,
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
  signal?: AbortSignal;
}): Promise<OverviewPayload> {
  const search = new URLSearchParams({ branch: params.branch });
  if (params.volumeView) search.set("volumeView", params.volumeView);
  const envelope = await httpGet<{
    success: boolean;
    message?: string;
    data: OverviewPayload;
  }>(ppcApiUrl(`/overview?${search.toString()}`), { signal: params.signal });
  return unwrapEnvelope(envelope, "Não foi possível carregar a gestão à vista.");
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

export async function fetchMachineLoad(params: {
  branch: string;
  workCenter?: string | null;
  startDate?: string | null;
  endDate?: string | null;
  signal?: AbortSignal;
}): Promise<MachineLoadPayload> {
  const search = new URLSearchParams({ branch: params.branch });
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
  const search = new URLSearchParams({ branch: params.branch });
  if (params.workCenter) search.set("workCenter", params.workCenter);
  if (params.startDate) search.set("startDate", params.startDate);
  if (params.endDate) search.set("endDate", params.endDate);
  const envelope = await httpPost<{
    success: boolean;
    message?: string;
    data: MachineLoadPayload;
  }>(ppcApiUrl(`/machine-load/refresh?${search.toString()}`), { signal: params.signal });
  return unwrapEnvelope(envelope, "Não foi possível atualizar a carga máquina.");
}

export async function patchMachineLoadSequence(params: {
  branch: string;
  workCenter: string;
  orderedKeys: Array<{ production_order: string; operation_code: string }>;
  signal?: AbortSignal;
}): Promise<MachineLoadPayload> {
  const search = new URLSearchParams({
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
  const search = new URLSearchParams({
    branch: params.branch,
    orderNumber: params.orderNumber,
  });
  if (params.workCenter) search.set("workCenter", params.workCenter);
  const envelope = await httpPost<{
    success: boolean;
    message?: string;
    data: MachineLoadPrioritizePayload;
  }>(ppcApiUrl(`/machine-load/prioritize?${search.toString()}`), { signal: params.signal });
  return unwrapEnvelope(envelope, "Não foi possível priorizar o conjunto.");
}

/** Reordena a fila de todos os centros pela entrega do PA, sem ultrapassar ops já iniciadas. */
export async function optimizeMachineLoadDeliverySequence(params: {
  branch: string;
  workCenter?: string | null;
  signal?: AbortSignal;
}): Promise<MachineLoadOptimizePayload> {
  const search = new URLSearchParams({ branch: params.branch });
  if (params.workCenter) search.set("workCenter", params.workCenter);
  const envelope = await httpPost<{
    success: boolean;
    message?: string;
    data: MachineLoadOptimizePayload;
  }>(ppcApiUrl(`/machine-load/optimize-delivery?${search.toString()}`), { signal: params.signal });
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
  const search = new URLSearchParams({
    branch: params.branch,
    orderNumber: params.orderNumber,
  });
  if (params.workCenter) search.set("workCenter", params.workCenter);
  const envelope = await httpPost<{
    success: boolean;
    message?: string;
    data: MachineLoadWithdrawPayload;
  }>(ppcApiUrl(`/machine-load/${action}?${search.toString()}`), { signal: params.signal });
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
  const search = new URLSearchParams({
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
  }>(ppcApiUrl(`/machine-load/transfer?${search.toString()}`), { signal: params.signal });
  return unwrapEnvelope(envelope, "Não foi possível transferir a operação de centro de trabalho.");
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
