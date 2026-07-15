import type { BranchRouteCode } from "../constants/branches";
import { SCRAP_MONITORING_BASE_PATH } from "../constants/branches";
import type { ScrapRegistroItem } from "../types/scrap";

export type ScrapRouteView = "dashboard" | "registro-detail";

export type ScrapParsedRoute = {
  view: ScrapRouteView;
  branchRoute: BranchRouteCode;
};

export function branchHomePath(branchRoute: BranchRouteCode): string {
  return `${SCRAP_MONITORING_BASE_PATH}/${branchRoute.toLowerCase()}`;
}

export function parseScrapPath(pathname: string): ScrapParsedRoute {
  const normalized = pathname.toLowerCase();
  const branchRoute: BranchRouteCode = normalized.includes("/es") ? "ES" : "SC";
  const view: ScrapRouteView = normalized.includes("/registro")
    ? "registro-detail"
    : "dashboard";
  return { view, branchRoute };
}

function setParam(params: URLSearchParams, key: string, value: string | number | undefined) {
  if (value == null) return;
  const text = String(value).trim();
  if (!text) return;
  params.set(key, text);
}

export function buildRegistroDetailPath(
  branchRoute: BranchRouteCode,
  item: ScrapRegistroItem,
): string {
  const params = new URLSearchParams();
  setParam(params, "filial", item.filial);
  setParam(params, "dataPerda", item.dataPerda);
  setParam(params, "op", item.op);
  setParam(params, "pa", item.pa);
  setParam(params, "paDescricao", item.paDescricao);
  setParam(params, "mp", item.mp);
  setParam(params, "descricao", item.descricao);
  setParam(params, "um", item.um);
  setParam(params, "motivoCodigo", item.motivoCodigo);
  setParam(params, "motivo", item.motivo);
  setParam(params, "quantidade", item.quantidade);
  setParam(params, "valor", item.valor);
  setParam(params, "custoUnitario", item.custoUnitario);
  setParam(params, "centroTrabalho", item.centroTrabalho);
  setParam(params, "codigoOperador", item.codigoOperador);
  setParam(params, "nomeOperador", item.nomeOperador);
  return `${branchHomePath(branchRoute)}/registro?${params.toString()}`;
}

export function readRegistroFromSearch(search: string): ScrapRegistroItem | null {
  const params = new URLSearchParams(
    search.startsWith("?") ? search : search ? `?${search}` : window.location.search,
  );
  const dataPerda = params.get("dataPerda")?.trim() ?? "";
  if (!dataPerda && !params.get("op") && !params.get("mp")) {
    return null;
  }

  const custoRaw = params.get("custoUnitario");
  const custoUnitario =
    custoRaw == null || custoRaw === ""
      ? undefined
      : Number(custoRaw);

  return {
    filial: params.get("filial") ?? "",
    dataPerda,
    op: params.get("op") ?? "",
    pa: params.get("pa") ?? "",
    paDescricao: params.get("paDescricao") ?? "",
    mp: params.get("mp") ?? "",
    descricao: params.get("descricao") ?? "",
    um: params.get("um") ?? "",
    motivoCodigo: params.get("motivoCodigo") ?? "",
    motivo: params.get("motivo") ?? "",
    quantidade: Number(params.get("quantidade") || 0),
    valor: Number(params.get("valor") || 0),
    custoUnitario:
      custoUnitario != null && !Number.isNaN(custoUnitario) ? custoUnitario : undefined,
    centroTrabalho: params.get("centroTrabalho") ?? "",
    codigoOperador: params.get("codigoOperador") ?? "",
    nomeOperador: params.get("nomeOperador") ?? "",
  };
}
