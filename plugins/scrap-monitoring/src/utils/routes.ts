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

export function buildRegistroDetailPath(
  branchRoute: BranchRouteCode,
  item: ScrapRegistroItem,
): string {
  const params = new URLSearchParams();
  params.set("filial", item.filial || "");
  params.set("dataPerda", item.dataPerda || "");
  params.set("op", item.op || "");
  params.set("pa", item.pa || "");
  params.set("mp", item.mp || "");
  params.set("descricao", item.descricao || "");
  params.set("um", item.um || "");
  params.set("motivoCodigo", item.motivoCodigo || "");
  params.set("motivo", item.motivo || "");
  params.set("quantidade", String(item.quantidade ?? ""));
  params.set("valor", String(item.valor ?? ""));
  params.set("centroTrabalho", item.centroTrabalho || "");
  params.set("codigoOperador", item.codigoOperador || "");
  params.set("nomeOperador", item.nomeOperador || "");
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

  return {
    filial: params.get("filial") ?? "",
    dataPerda,
    op: params.get("op") ?? "",
    pa: params.get("pa") ?? "",
    mp: params.get("mp") ?? "",
    descricao: params.get("descricao") ?? "",
    um: params.get("um") ?? "",
    motivoCodigo: params.get("motivoCodigo") ?? "",
    motivo: params.get("motivo") ?? "",
    quantidade: Number(params.get("quantidade") || 0),
    valor: Number(params.get("valor") || 0),
    centroTrabalho: params.get("centroTrabalho") ?? "",
    codigoOperador: params.get("codigoOperador") ?? "",
    nomeOperador: params.get("nomeOperador") ?? "",
  };
}
