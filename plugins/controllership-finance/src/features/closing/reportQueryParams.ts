/**
 * Persistência de filtros das páginas contextuais de relatório — RW01.
 *
 * A URL é a única fonte recuperável do estado de navegação: a página
 * serializa os filtros vigentes na query da própria rota contextual
 * (`replace: true`, sem poluir o histórico) e reidrata o estado a partir
 * dela na montagem e em cada `popstate` (F5, deep link, voltar/avançar).
 *
 * Os parâmetros pertencem à família do relatório — no hub, o parâmetro
 * `report=` identifica de qual família eles vieram; abrir outra família
 * descarta o contexto da anterior. Nenhum dado financeiro vai para a
 * URL — somente filtros/códigos de consulta.
 */
import { useEffect, useRef } from "react";

import { navigatePluginPath } from "../../app/pluginNavigation";

export const SETTLEMENT_PARAMS = [
  "side",
  "start",
  "end",
  "nature",
  "movement",
  "sort",
  "dir",
  "page",
] as const;

export const STOCK_PARAMS = [
  "branch",
  "scope",
  "warehouse",
  "page",
] as const;

const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

export type ReportDateRange = { startDate: string; endDate: string };

export type SettlementsQueryFilters = {
  side: "payable" | "receivable";
  startDate: string;
  endDate: string;
  natureCode: string;
  movementType: string;
  sortBy: string;
  sortDir: "asc" | "desc";
  page: number;
};

export type StockQueryFilters = {
  branch: "all" | "01" | "02";
  scope: "all_products" | "mp_pi_pa";
  warehouse: string;
  page: number;
};

export function readReportSearchParams(): URLSearchParams {
  if (typeof window === "undefined") return new URLSearchParams();
  return new URLSearchParams(window.location.search);
}

/** Somente os parâmetros pertencentes à família — usado no retorno ao hub. */
export function pickFamilyParams(
  search: URLSearchParams,
  names: readonly string[],
): URLSearchParams {
  const picked = new URLSearchParams();
  for (const name of names) {
    const value = search.get(name);
    if (value !== null) picked.set(name, value);
  }
  return picked;
}

function parsePage(raw: string | null): number {
  const value = Number.parseInt(raw ?? "", 10);
  return Number.isFinite(value) && value > 1 ? value : 1;
}

/**
 * Baixas financeiras — datas fora da competência da rota descartam o
 * par inteiro (nunca restaura intervalo de outro mês silenciosamente).
 */
export function parseSettlementsQuery(
  search: URLSearchParams,
  range: ReportDateRange,
): SettlementsQueryFilters {
  const rawStart = search.get("start");
  const rawEnd = search.get("end");
  const validPair =
    rawStart !== null &&
    rawEnd !== null &&
    DATE_RE.test(rawStart) &&
    DATE_RE.test(rawEnd) &&
    rawStart <= rawEnd &&
    rawStart >= range.startDate &&
    rawEnd <= range.endDate;
  return {
    side: search.get("side") === "receivable" ? "receivable" : "payable",
    startDate: validPair ? rawStart : range.startDate,
    endDate: validPair ? rawEnd : range.endDate,
    natureCode: search.get("nature") ?? "",
    movementType: search.get("movement") ?? "",
    sortBy: search.get("sort") === "nature" ? "nature" : "settlement_date",
    sortDir: search.get("dir") === "asc" ? "asc" : "desc",
    page: parsePage(search.get("page")),
  };
}

export function serializeSettlementsQuery(
  filters: SettlementsQueryFilters,
): string {
  const params = new URLSearchParams();
  params.set("side", filters.side);
  params.set("start", filters.startDate);
  params.set("end", filters.endDate);
  if (filters.natureCode) params.set("nature", filters.natureCode);
  if (filters.movementType) params.set("movement", filters.movementType);
  params.set("sort", filters.sortBy);
  params.set("dir", filters.sortDir);
  if (filters.page > 1) params.set("page", String(filters.page));
  return params.toString();
}

export function parseStockQuery(
  search: URLSearchParams,
): StockQueryFilters {
  const rawBranch = search.get("branch");
  const rawScope = search.get("scope");
  return {
    branch:
      rawBranch === "01" || rawBranch === "02" ? rawBranch : "all",
    scope: rawScope === "mp_pi_pa" ? "mp_pi_pa" : "all_products",
    warehouse: search.get("warehouse") ?? "",
    page: parsePage(search.get("page")),
  };
}

export function serializeStockQuery(filters: StockQueryFilters): string {
  const params = new URLSearchParams();
  params.set("branch", filters.branch);
  params.set("scope", filters.scope);
  if (filters.warehouse) params.set("warehouse", filters.warehouse);
  if (filters.page > 1) params.set("page", String(filters.page));
  return params.toString();
}

/**
 * Espelha o estado na query da rota contextual e reidrata no `popstate`.
 * `serialize` roda a cada render e só navega quando a query difere —
 * sem loops porque reidratar com os mesmos valores gera `setState`
 * idêntico (React baila) e `navigatePluginPath` ignora alvo igual.
 */
export function useReportQuerySync({
  enabled,
  serialize,
  hydrate,
}: {
  enabled: boolean;
  serialize: () => string;
  hydrate: (params: URLSearchParams) => void;
}) {
  const hydrateRef = useRef(hydrate);
  const serializeRef = useRef(serialize);
  useEffect(() => {
    hydrateRef.current = hydrate;
    serializeRef.current = serialize;
  });

  useEffect(() => {
    if (!enabled) return;
    const query = serializeRef.current();
    if (query !== window.location.search) {
      navigatePluginPath(
        `${window.location.pathname}${query}`,
        { replace: true },
      );
    }
  });

  useEffect(() => {
    if (!enabled) return;
    const onPopState = () => {
      // O próprio replace do serialize dispara popstate — hidratar só
      // quando a query difere do eco do estado atual, senão um valor
      // inválido em edição (ex.: data parcial) seria sobrescrito pelo
      // parse normalizado durante a digitação.
      if (serializeRef.current() !== window.location.search) {
        hydrateRef.current(readReportSearchParams());
      }
    };
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, [enabled]);
}
