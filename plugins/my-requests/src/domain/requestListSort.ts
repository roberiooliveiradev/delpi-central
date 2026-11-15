/**
 * Ordenação das listas Minhas / Fila — catálogo por fonte efetiva.
 *
 * A listagem Minhas une duas APIs; só campos semanticamente
 * comparáveis nas duas fontes podem ordenar o conjunto mesclado.
 * Os demais campos ficam disponíveis quando o filtro reduz a
 * consulta a uma única fonte (Tipo=PRC → Engineering API; outro
 * tipo → Requests API). Isso preserva a correção do merge global —
 * nunca ordenamos só a página carregada.
 */

import type {
  DashboardSortFieldOption,
  DashboardSortLevel,
} from "@delpi/plugin-ui/index";

export type RequestListSource = "merged" | "requests" | "prc";

/** Tipo requests-api equivalente ao caso PRC da Engineering API. */
export const PRC_TYPE_CODE = "raw-material-creation";

/** Campos ordenáveis do contrato requests-api (`sort=f:d[,f:d]`). */
export const REQUESTS_SORT_FIELDS: readonly DashboardSortFieldOption[] = [
  { value: "created_at", label: "Data" },
  { value: "updated_at", label: "Atualização" },
  { value: "request_number", label: "Número" },
  { value: "status", label: "Status" },
  { value: "type_code", label: "Tipo" },
  { value: "branch", label: "Filial" },
];

/** Campos ordenáveis do contrato PRC (`sortBy`/`sortDir`, 1 nível). */
export const PRC_SORT_FIELDS: readonly DashboardSortFieldOption[] = [
  { value: "createdAt", label: "Data" },
  { value: "requestType", label: "Tipo" },
  { value: "status", label: "Status" },
  { value: "officialCode", label: "Código" },
  { value: "requester", label: "Solicitante" },
];

/** Conjunto mesclado — só o campo comparável nas duas fontes. */
export const MERGED_SORT_FIELDS: readonly DashboardSortFieldOption[] = [
  { value: "created_at", label: "Data" },
];

export function sourceForTypeCode(typeCode: string): RequestListSource {
  const code = (typeCode || "").trim();
  if (!code) return "merged";
  return code === PRC_TYPE_CODE ? "prc" : "requests";
}

export function sortCatalogForSource(source: RequestListSource): {
  fields: readonly DashboardSortFieldOption[];
  maxLevels: number;
} {
  if (source === "prc") return { fields: PRC_SORT_FIELDS, maxLevels: 1 };
  if (source === "requests")
    return { fields: REQUESTS_SORT_FIELDS, maxLevels: 3 };
  return { fields: MERGED_SORT_FIELDS, maxLevels: 1 };
}

export function defaultSortLevels(
  source: RequestListSource,
): DashboardSortLevel[] {
  return [
    {
      field: source === "prc" ? "createdAt" : "created_at",
      direction: "desc",
    },
  ];
}

/** `field:dir,field:dir` → níveis (campos fora do catálogo são ignorados). */
export function parseListSortLevels(
  sort: string,
  fields: readonly DashboardSortFieldOption[],
): DashboardSortLevel[] {
  const allowed = new Set(fields.map((f) => f.value));
  const levels: DashboardSortLevel[] = [];
  for (const chunk of String(sort || "").split(",")) {
    const [field = "", direction = "asc"] = chunk.trim().split(":");
    if (!allowed.has(field) || levels.some((l) => l.field === field)) continue;
    levels.push({ field, direction: direction === "asc" ? "asc" : "desc" });
  }
  return levels;
}

/** Níveis → `field:dir,field:dir` (contrato requests-api e URL). */
export function serializeListSortLevels(
  levels: readonly DashboardSortLevel[],
): string {
  return levels
    .filter((level) => Boolean(level.field))
    .map((level) => `${level.field}:${level.direction === "asc" ? "asc" : "desc"}`)
    .join(",");
}
