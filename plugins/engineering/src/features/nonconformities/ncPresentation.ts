/** Modelo de apresentação da feature NC — funções puras testáveis em
 * node, sem dependência de DOM. Renderização fica nas páginas. */
import type { PageHeroHighlight } from "@delpi/plugin-ui/index";

import { formatNcDate, formatNcDateTime } from "./ncCopy";
import type {
  NcHistoryEvent,
  NcHistoryField,
  NcIndicators,
  NcProduct,
} from "./types";

const DATE_FIELDS = new Set([
  "occurrence_date",
  "launch_date",
  "last_revision_date",
]);
const DATETIME_FIELDS = new Set([
  "registered_at",
  "created_at",
  "updated_at",
]);

function isProductLike(value: unknown): value is NcProduct {
  return (
    typeof value === "object" &&
    value !== null &&
    typeof (value as NcProduct).product_code === "string"
  );
}

export function describeNcProduct(product: NcProduct): string {
  const code = product.product_code.trim();
  const description = product.product_description?.trim();
  return description ? `${code} — ${description}` : code;
}

/** Formata um valor de histórico por tipo — nunca `[object Object]` nem
 * JSON bruto. Campos de data usam os formatters oficiais da feature. */
export function formatNcHistoryValue(
  field: string,
  value: unknown,
  depth = 0,
): string {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "string") {
    if (DATE_FIELDS.has(field)) return formatNcDate(value);
    if (DATETIME_FIELDS.has(field)) return formatNcDateTime(value);
    return value;
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  if (Array.isArray(value)) {
    if (!value.length) return "—";
    const parts = value.map((item) => {
      if (isProductLike(item)) return describeNcProduct(item);
      return formatNcHistoryValue(field, item, depth + 1);
    });
    return parts.join("; ");
  }
  if (isProductLike(value)) return describeNcProduct(value);
  if (depth >= 2) return "—";
  const entries = Object.entries(value as Record<string, unknown>).filter(
    ([, v]) => v !== undefined,
  );
  if (!entries.length) return "—";
  return entries
    .map(([key, v]) => `${key}: ${formatNcHistoryValue(key, v, depth + 1)}`)
    .join("; ");
}

export function formatNcHistoryChange(change: NcHistoryField): string {
  const before = formatNcHistoryValue(change.field, change.old);
  const after = formatNcHistoryValue(change.field, change.new);
  return `${change.label}: ${before} → ${after}`;
}

/** Resumo textual das alterações de um evento — alimenta o `detail` da
 * Timeline oficial. */
export function ncHistoryChangeLines(event: NcHistoryEvent): string[] {
  return (event.changes?.fields ?? []).map(formatNcHistoryChange);
}

export function ncHistoryActorLabel(event: NcHistoryEvent): string {
  return event.actor_name ?? event.actor_email ?? "Usuário do Portal";
}

/** Indicadores oficiais dentro do hero — valores sempre consumidos da
 * Engineering API; `loading` mantém placeholder honesto até o fetch. */
export function buildNcHeroHighlights(
  indicators: NcIndicators | null,
): PageHeroHighlight[] {
  const loading = indicators === null;
  return [
    {
      id: "days-without-nc",
      label: "Dias sem NC",
      value: loading
        ? "…"
        : String(indicators.current_days_without_nc),
      description: loading
        ? "Carregando indicadores oficiais…"
        : indicators.last_nc_date
          ? `Última NC em ${formatNcDate(indicators.last_nc_date)}`
          : "Sem ocorrências registradas",
      loading,
    },
    {
      id: "record-days-without-nc",
      label: "Recorde de dias sem NC",
      value: loading ? "…" : String(indicators.record_days_without_nc),
      description: loading
        ? "Carregando indicadores oficiais…"
        : `${indicators.nc_count} NC(s) registrada(s)`,
      loading,
    },
  ];
}

export type NcProductsSummary = {
  visible: NcProduct[];
  overflowCount: number;
  /** Lista completa em texto — `title`/`aria-label` da célula. */
  fullLabel: string;
};

/** Compacta a célula de produtos da tabela — primeiros `maxVisible`
 * itens + contador de excedentes; a lista completa fica no detalhe. */
export function buildNcProductsSummary(
  products: NcProduct[],
  maxVisible = 2,
): NcProductsSummary {
  return {
    visible: products.slice(0, Math.max(0, maxVisible)),
    overflowCount: Math.max(0, products.length - maxVisible),
    fullLabel: products.map(describeNcProduct).join("; "),
  };
}
