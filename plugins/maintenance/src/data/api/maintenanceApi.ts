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
