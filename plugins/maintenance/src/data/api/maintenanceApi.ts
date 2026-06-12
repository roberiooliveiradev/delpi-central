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

export type MaintenanceSubmodule = {
  id: string;
  label: string;
  description: string;
  icon: string;
  entry_path: string;
  can_manage?: boolean;
};

export type MaintenanceOptions = {
  filiais: Array<{ id: string; label: string }>;
  submodules: MaintenanceSubmodule[];
  modulos: MaintenanceSubmodule[];
  default_filial?: string | null;
  access_scope?: {
    mode: string;
    allowed_filiais: string[];
    scoped_manage: boolean;
  };
};

export function fetchMaintenanceOptions(getAccessToken?: () => string | undefined) {
  return maintenanceFetch<MaintenanceOptions>("/options", { getAccessToken });
}

export function fetchFerramentas(
  params: {
    filial: string;
    codigo?: string;
    descricao?: string;
    page?: number;
    page_size?: number;
  },
  getAccessToken?: () => string | undefined,
) {
  const search = new URLSearchParams();
  search.set("filial", params.filial);
  if (params.codigo) search.set("codigo", params.codigo);
  if (params.descricao) search.set("descricao", params.descricao);
  if (params.page) search.set("page", String(params.page));
  if (params.page_size) search.set("page_size", String(params.page_size));

  const query = search.toString();
  return maintenanceFetch<FerramentasPage>(
    `/mini-aplicadores/ferramentas${query ? `?${query}` : ""}`,
    { getAccessToken },
  );
}

export function fetchFerramenta(
  codigo: string,
  filial: string,
  getAccessToken?: () => string | undefined,
) {
  return maintenanceFetch<FerramentaItem>(
    `/mini-aplicadores/ferramentas/${encodeURIComponent(codigo)}?filial=${encodeURIComponent(filial)}`,
    { getAccessToken },
  );
}


export type PreventivaAlerta = {
  filial: string;
  codigo_ferramenta: string;
  codigo_peca: string;
  data_ultima_reposicao: string;
  media_golpes: number;
  golpes_atuais: number;
  percentual_uso: number;
  status: string;
};

export type PreventivaHistoricoItem = {
  reposicao_id: string;
  data_reposicao: string;
  golpes: number;
};

export function fetchPreventivaAlertas(
  filial: string,
  getAccessToken?: () => string | undefined,
) {
  return maintenanceFetch<{ items: PreventivaAlerta[]; total: number }>(
    `/preventiva/alertas?filial=${encodeURIComponent(filial)}`,
    { getAccessToken },
  );
}

export function fetchPreventivaHistorico(
  params: { filial: string; codigo_ferramenta: string; codigo_peca: string },
  getAccessToken?: () => string | undefined,
) {
  const search = new URLSearchParams(params);
  return maintenanceFetch<{ items: PreventivaHistoricoItem[]; total: number }>(
    `/preventiva/historico?${search.toString()}`,
    { getAccessToken },
  );
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

export function fetchMotivos(filial: string, getAccessToken?: () => string | undefined) {
  return maintenanceFetch<{ items: MotivoItem[]; total: number }>(
    `/motivos?filial=${encodeURIComponent(filial)}`,
    { getAccessToken },
  );
}

export function fetchStatusPeca(filial: string, getAccessToken?: () => string | undefined) {
  return maintenanceFetch<{ items: StatusItem[]; total: number }>(
    `/status-peca?filial=${encodeURIComponent(filial)}`,
    { getAccessToken },
  );
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

export function updateReposicao(
  reposicaoId: string,
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
  return maintenanceFetch<ReposicaoItem>(`/reposicoes/${encodeURIComponent(reposicaoId)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    getAccessToken,
  });
}

export function deleteReposicao(reposicaoId: string, getAccessToken?: () => string | undefined) {
  return maintenanceFetch<null>(`/reposicoes/${encodeURIComponent(reposicaoId)}`, {
    method: "DELETE",
    getAccessToken,
  });
}

export function createMotivo(descricao: string, getAccessToken?: () => string | undefined) {
  return maintenanceFetch<MotivoItem>("/motivos", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ descricao }),
    getAccessToken,
  });
}

export function updateMotivo(
  motivoId: number,
  descricao: string,
  getAccessToken?: () => string | undefined,
) {
  return maintenanceFetch<MotivoItem>(`/motivos/${motivoId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ descricao }),
    getAccessToken,
  });
}

export function deleteMotivo(motivoId: number, getAccessToken?: () => string | undefined) {
  return maintenanceFetch<null>(`/motivos/${motivoId}`, {
    method: "DELETE",
    getAccessToken,
  });
}

export function updateStatusPeca(
  statusId: number,
  body: { descricao?: string; operador?: string; percentual?: number },
  getAccessToken?: () => string | undefined,
) {
  return maintenanceFetch<StatusItem>(`/status-peca/${statusId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    getAccessToken,
  });
}

export function fetchPecas(
  codigoFerramenta: string,
  filial: string,
  getAccessToken?: () => string | undefined,
) {
  return maintenanceFetch<{ items: FerramentaItem[]; total: number }>(
    `/mini-aplicadores/ferramentas/${encodeURIComponent(codigoFerramenta)}/pecas?filial=${encodeURIComponent(filial)}`,
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
