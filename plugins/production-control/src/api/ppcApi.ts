import { httpGet, httpPatch, httpPost, ppcApiUrl, unwrapEnvelope } from "./httpClient";
import type {
  MachineLoadPayload,
  OverviewPayload,
  ProblemAnalysisPayload,
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
  signal?: AbortSignal;
}): Promise<OverviewPayload> {
  const search = new URLSearchParams({ branch: params.branch });
  const envelope = await httpGet<{
    success: boolean;
    message?: string;
    data: OverviewPayload;
  }>(ppcApiUrl(`/overview?${search.toString()}`), { signal: params.signal });
  return unwrapEnvelope(envelope, "Não foi possível carregar a gestão à vista.");
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
  startDate?: string | null;
  endDate?: string | null;
  orderedKeys: Array<{ production_order: string; operation_code: string }>;
  signal?: AbortSignal;
}): Promise<MachineLoadPayload> {
  const search = new URLSearchParams({
    branch: params.branch,
    workCenter: params.workCenter,
  });
  if (params.startDate) search.set("startDate", params.startDate);
  if (params.endDate) search.set("endDate", params.endDate);
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

export async function fetchProblemAnalysis(params: {
  branch: string;
  issueId?: string | null;
  signal?: AbortSignal;
}): Promise<ProblemAnalysisPayload> {
  const search = new URLSearchParams({ branch: params.branch });
  if (params.issueId) search.set("issueId", params.issueId);
  const envelope = await httpGet<{
    success: boolean;
    message?: string;
    data: ProblemAnalysisPayload;
  }>(ppcApiUrl(`/problem-analysis?${search.toString()}`), { signal: params.signal });
  return unwrapEnvelope(envelope, "Não foi possível carregar a análise de problemas.");
}
