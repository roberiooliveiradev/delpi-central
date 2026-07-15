import { httpGet } from "./httpClient";
import { unwrapApiDelpiEnvelope } from "../types/api";
import type {
  ClientesQueryParams,
  InadimplenciaClientesData,
  InadimplenciaFaixasData,
  InadimplenciaMensalData,
  InadimplenciaResumoData,
  InadimplenciaTitulosData,
  MensalQueryParams,
  PeriodFilter,
  TitulosQueryParams,
} from "../types/inadimplencia";
import {
  buildClientesQuery,
  buildMensalQuery,
  buildPeriodQuery,
  buildTitulosQuery,
  queryString,
} from "../utils/queryParams";

const API_BASE = "/apps/api-delpi/financeiro/inadimplencia";

type RequestOptions = {
  signal?: AbortSignal;
};

async function getEnvelope<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const payload = await httpGet<unknown>(`${API_BASE}${path}`, options);
  return unwrapApiDelpiEnvelope<T>(payload);
}

export async function fetchInadimplenciaResumo(
  filters: PeriodFilter = {},
  options: RequestOptions = {},
): Promise<InadimplenciaResumoData> {
  return getEnvelope<InadimplenciaResumoData>(
    `/resumo${queryString(buildPeriodQuery(filters))}`,
    options,
  );
}

export async function fetchInadimplenciaMensal(
  filters: MensalQueryParams = {},
  options: RequestOptions = {},
): Promise<InadimplenciaMensalData> {
  return getEnvelope<InadimplenciaMensalData>(
    `/mensal${queryString(buildMensalQuery(filters))}`,
    options,
  );
}

export async function fetchInadimplenciaFaixas(
  filters: PeriodFilter = {},
  options: RequestOptions = {},
): Promise<InadimplenciaFaixasData> {
  return getEnvelope<InadimplenciaFaixasData>(
    `/faixas-atraso${queryString(buildPeriodQuery(filters))}`,
    options,
  );
}

export async function fetchInadimplenciaClientes(
  params: ClientesQueryParams,
  options: RequestOptions = {},
): Promise<InadimplenciaClientesData> {
  return getEnvelope<InadimplenciaClientesData>(
    `/clientes${queryString(buildClientesQuery(params))}`,
    options,
  );
}

export async function fetchInadimplenciaTitulos(
  params: TitulosQueryParams,
  options: RequestOptions = {},
): Promise<InadimplenciaTitulosData> {
  return getEnvelope<InadimplenciaTitulosData>(
    `/titulos${queryString(buildTitulosQuery(params))}`,
    options,
  );
}

export const inadimplenciaApiPaths = {
  resumo: `${API_BASE}/resumo`,
  mensal: `${API_BASE}/mensal`,
  faixasAtraso: `${API_BASE}/faixas-atraso`,
  clientes: `${API_BASE}/clientes`,
  titulos: `${API_BASE}/titulos`,
} as const;
