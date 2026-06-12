import { maintenanceFetch } from "./maintenanceApiBase";

export type FerramentaItem = {
  id: number;
  codigo: string;
  descricao: string;
  grupo?: string;
};

export type FerramentasPage = {
  items: FerramentaItem[];
  total: number;
  page?: number;
  page_size?: number;
  total_pages?: number;
};

export type MaintenanceOptions = {
  filiais: Array<{ id: string; label: string }>;
  modulos: Array<{ id: string; label: string }>;
};

export function fetchMaintenanceOptions(getAccessToken?: () => string | undefined) {
  return maintenanceFetch<MaintenanceOptions>("/options", { getAccessToken });
}

export function fetchFerramentas(
  params: {
    codigo?: string;
    descricao?: string;
    filial?: string;
    page?: number;
    page_size?: number;
  },
  getAccessToken?: () => string | undefined,
) {
  const search = new URLSearchParams();
  if (params.codigo) search.set("codigo", params.codigo);
  if (params.descricao) search.set("descricao", params.descricao);
  if (params.filial) search.set("filial", params.filial);
  if (params.page) search.set("page", String(params.page));
  if (params.page_size) search.set("page_size", String(params.page_size));

  const query = search.toString();
  return maintenanceFetch<FerramentasPage>(
    `/mini-aplicadores/ferramentas${query ? `?${query}` : ""}`,
    { getAccessToken },
  );
}

export function fetchFerramenta(codigo: string, getAccessToken?: () => string | undefined) {
  return maintenanceFetch<FerramentaItem>(`/mini-aplicadores/ferramentas/${encodeURIComponent(codigo)}`, {
    getAccessToken,
  });
}

export function fetchModuleHealth(getAccessToken?: () => string | undefined) {
  return maintenanceFetch<{
    status: string;
    module: string;
    phase: string;
    db_ready: boolean;
    db_hint?: string | null;
  }>("/health", { getAccessToken });
}

export type MotivoItem = { motivo_id: number; descricao: string };
export type StatusItem = {
  status_id: number;
  descricao: string;
  operador: string;
  percentual: number;
};
export type ReposicaoItem = {
  reposicao_id: string;
  filial: string;
  codigo_ferramenta: string;
  codigo_peca: string;
  data_reposicao: string;
  golpes: number;
  motivo_id: number;
  motivo_descricao?: string;
  observacao?: string | null;
};

export function fetchMotivos(getAccessToken?: () => string | undefined) {
  return maintenanceFetch<{ items: MotivoItem[]; total: number }>("/motivos", { getAccessToken });
}

export function fetchStatusPeca(getAccessToken?: () => string | undefined) {
  return maintenanceFetch<{ items: StatusItem[]; total: number }>("/status-peca", {
    getAccessToken,
  });
}

export function fetchReposicoes(
  params: { filial: string; codigo_ferramenta: string; codigo_peca?: string },
  getAccessToken?: () => string | undefined,
) {
  const search = new URLSearchParams(params as Record<string, string>);
  return maintenanceFetch<{ items: ReposicaoItem[]; total: number }>(
    `/reposicoes?${search.toString()}`,
    { getAccessToken },
  );
}

export function createReposicao(
  body: {
    filial: string;
    codigo_ferramenta: string;
    codigo_peca: string;
    data_reposicao: string;
    golpes: number;
    motivo_id: number;
    observacao?: string;
  },
  getAccessToken?: () => string | undefined,
) {
  return maintenanceFetch<ReposicaoItem>("/reposicoes", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    getAccessToken,
  });
}

export function fetchPecas(codigoFerramenta: string, getAccessToken?: () => string | undefined) {
  return maintenanceFetch<{ items: FerramentaItem[]; total: number }>(
    `/mini-aplicadores/ferramentas/${encodeURIComponent(codigoFerramenta)}/pecas`,
    { getAccessToken },
  );
}

export function suggestGolpes(
  params: { filial: string; codigo_ferramenta: string; codigo_peca: string },
  getAccessToken?: () => string | undefined,
) {
  const search = new URLSearchParams(params);
  return maintenanceFetch<{ total_golpes: number }>(
    `/mini-aplicadores/sugerir-golpes?${search.toString()}`,
    { getAccessToken },
  );
}
