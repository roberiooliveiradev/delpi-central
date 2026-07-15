import { useMemo, useState, type ReactNode } from "react";
import { Factory } from "lucide-react";

import {
  formatParamHintLine,
  humanizeMetaShape,
  resolveRouteAudienceDescription,
  truncateText,
  type DataRouteParamFieldSummary,
} from "./dataRouteCatalogHelpers";

export type DataRouteDisplayKind = "kpi" | "series" | "table";

export type DataRouteCatalogItem = {
  /** Identificador estável — tipicamente operationId. */
  id: string;
  label: string;
  category: string;
  description?: string;
  path?: string;
  httpMethod?: string;
  /** Formas de apresentação sugeridas (kpi / series / table). */
  displayKinds?: DataRouteDisplayKind[];
  metaShape?: string;
  /** Orientação de uso curada (overlay TV) — tem prioridade na prosa «para que serve». */
  whenToUse?: string;
  /** Parâmetros já rotulados para a UI (sem path técnico no card). */
  params?: DataRouteParamFieldSummary[];
};

export type DataRouteCatalogDensity = "compact" | "comfortable";

export type DataRouteCatalogPanelProps = {
  items: DataRouteCatalogItem[];
  onSelect: (item: DataRouteCatalogItem) => void;
  searchPlaceholder?: string;
  emptyMessage?: string;
  loading?: boolean;
  error?: string | null;
  categoryLabels?: Record<string, string>;
  categoryOrder?: readonly string[];
  renderCategoryIcon?: (category: string) => ReactNode;
  className?: string;
  /** Exibe chips de forma (KPI / Série / Tabela). Default true. */
  showDisplayKindFilters?: boolean;
  /**
   * `comfortable` = lista + detalhe lado a lado (popover).
   * `compact` = lista + detalhe empilhado (sidebar).
   */
  density?: DataRouteCatalogDensity;
  /** Rótulo do CTA no detalhe. */
  confirmLabel?: string;
};

const DISPLAY_KIND_LABELS: Record<DataRouteDisplayKind, string> = {
  kpi: "KPI",
  series: "Série",
  table: "Tabela",
};

export function resolveDataRouteDisplayKinds(item: {
  displayKinds?: DataRouteDisplayKind[];
  metaShape?: string;
  allowedDisplayModes?: string[];
}): DataRouteDisplayKind[] {
  if (item.displayKinds?.length) {
    return [...new Set(item.displayKinds)];
  }
  const modes = item.allowedDisplayModes ?? [];
  const kinds = new Set<DataRouteDisplayKind>();
  if (modes.includes("line_chart") || modes.includes("bar_chart")) kinds.add("series");
  if (modes.includes("table") || item.metaShape === "paged_list" || item.metaShape === "hierarchy") {
    kinds.add("table");
  }
  if (modes.includes("kpi") || item.metaShape === "scalar") kinds.add("kpi");
  if (kinds.size === 0) {
    if (item.metaShape === "scalar") kinds.add("kpi");
    else kinds.add("table");
  }
  return [...kinds];
}

export function primaryDataRouteDisplayKind(kinds: DataRouteDisplayKind[]): DataRouteDisplayKind {
  if (kinds.includes("series")) return "series";
  if (kinds.includes("kpi")) return "kpi";
  return "table";
}

function defaultCategoryIcon(_category: string) {
  return <Factory size={16} aria-hidden="true" />;
}

type EnrichedItem = DataRouteCatalogItem & {
  displayKinds: DataRouteDisplayKind[];
  primaryKind: DataRouteDisplayKind;
  params: DataRouteParamFieldSummary[];
  audienceDescription: string;
  paramHint: string;
};

export function DataRouteCatalogPanel({
  items,
  onSelect,
  searchPlaceholder = "Buscar fonte ou descrição…",
  emptyMessage = "Nenhuma fonte com esses filtros.",
  loading = false,
  error = null,
  categoryLabels = {},
  categoryOrder = [],
  renderCategoryIcon = defaultCategoryIcon,
  className = "",
  showDisplayKindFilters = true,
  density = "comfortable",
  confirmLabel = "Usar esta fonte",
}: DataRouteCatalogPanelProps) {
  const [query, setQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string | "all">("all");
  const [kindFilters, setKindFilters] = useState<DataRouteDisplayKind[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const enriched = useMemo(
    (): EnrichedItem[] =>
      items.map((item) => {
        const kinds = resolveDataRouteDisplayKinds(item);
        const params = item.params ?? [];
        return {
          ...item,
          displayKinds: kinds,
          primaryKind: primaryDataRouteDisplayKind(kinds),
          params,
          audienceDescription: resolveRouteAudienceDescription(item),
          paramHint: formatParamHintLine(params) ?? "Sem filtros",
        };
      }),
    [items],
  );

  const categoryCounts = useMemo(() => {
    const counts = new Map<string, number>();
    for (const item of enriched) {
      const key = item.category || "other";
      counts.set(key, (counts.get(key) ?? 0) + 1);
    }
    return counts;
  }, [enriched]);

  const categoryChipKeys = useMemo(() => {
    const present = [...categoryCounts.keys()];
    const ordered = [
      ...categoryOrder.filter((key) => present.includes(key)),
      ...present.filter((key) => !categoryOrder.includes(key)).sort(),
    ];
    return ordered;
  }, [categoryCounts, categoryOrder]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return enriched.filter((item) => {
      if (categoryFilter !== "all" && (item.category || "other") !== categoryFilter) {
        return false;
      }
      if (kindFilters.length > 0) {
        const kinds = item.displayKinds ?? [];
        if (!kindFilters.some((kind) => kinds.includes(kind))) return false;
      }
      if (!q) return true;
      const haystack = [
        item.label,
        item.id,
        item.category,
        item.path ?? "",
        item.description ?? "",
        item.audienceDescription,
        categoryLabels[item.category] ?? "",
        ...item.params.map((param) => `${param.key} ${param.label}`),
      ]
        .join(" ")
        .toLowerCase();
      return haystack.includes(q);
    });
  }, [categoryFilter, categoryLabels, enriched, kindFilters, query]);

  const grouped = useMemo(() => {
    const buckets = new Map<string, typeof filtered>();
    for (const item of filtered) {
      const key = item.category || "other";
      const list = buckets.get(key) ?? [];
      list.push(item);
      buckets.set(key, list);
    }
    const orderedKeys = [
      ...categoryOrder.filter((key) => buckets.has(key)),
      ...[...buckets.keys()].filter((key) => !categoryOrder.includes(key)).sort(),
    ];
    return orderedKeys.map((key) => ({
      key,
      label: categoryLabels[key] ?? key,
      items: (buckets.get(key) ?? []).sort((a, b) => a.label.localeCompare(b.label, "pt-BR")),
    }));
  }, [categoryLabels, categoryOrder, filtered]);

  const selected = useMemo(() => {
    if (!selectedId) return null;
    return filtered.find((item) => item.id === selectedId) ?? enriched.find((item) => item.id === selectedId) ?? null;
  }, [enriched, filtered, selectedId]);

  function toggleKind(kind: DataRouteDisplayKind) {
    setKindFilters((prev) => (prev.includes(kind) ? prev.filter((k) => k !== kind) : [...prev, kind]));
  }

  const hasActiveFilters = categoryFilter !== "all" || kindFilters.length > 0 || query.trim().length > 0;
  const descClamp = density === "compact" ? 90 : 140;

  const detail = selected ? (
    <aside
      className="delpi-ui-data-route-catalog__detail"
      aria-label={`Detalhe: ${selected.label}`}
    >
      <h3 className="delpi-ui-data-route-catalog__detail-title">{selected.label}</h3>
      <p className="delpi-ui-data-route-catalog__detail-section-label">Para que serve</p>
      <p className="delpi-ui-data-route-catalog__detail-body">{selected.audienceDescription}</p>

      <p className="delpi-ui-data-route-catalog__detail-section-label">O que você vê na TV</p>
      <div className="delpi-ui-data-route-catalog__detail-kinds">
        {selected.displayKinds.map((kind) => (
          <span key={kind} className="delpi-ui-data-route-catalog__mode">
            {DISPLAY_KIND_LABELS[kind]}
          </span>
        ))}
        {humanizeMetaShape(selected.metaShape) ? (
          <span className="delpi-ui-data-route-catalog__detail-shape">
            {humanizeMetaShape(selected.metaShape)}
          </span>
        ) : null}
      </div>

      <p className="delpi-ui-data-route-catalog__detail-section-label">Filtros desta fonte</p>
      {selected.params.length === 0 ? (
        <p className="delpi-ui-data-route-catalog__detail-body">Nenhum filtro configurável.</p>
      ) : (
        <ul className="delpi-ui-data-route-catalog__param-list">
          {selected.params.map((param) => (
            <li key={param.key} className="delpi-ui-data-route-catalog__param-item">
              <span className="delpi-ui-data-route-catalog__param-label">{param.label}</span>
              <span className="delpi-ui-data-route-catalog__param-meta">
                {param.optional === false ? "obrigatório" : "opcional"}
              </span>
              {param.description ? (
                <span className="delpi-ui-data-route-catalog__param-hint">{param.description}</span>
              ) : null}
            </li>
          ))}
        </ul>
      )}

      {selected.httpMethod && selected.path ? (
        <details className="delpi-ui-data-route-catalog__advanced">
          <summary>Avançado (API)</summary>
          <code className="delpi-ui-data-route-catalog__path">
            {selected.httpMethod} {selected.path}
          </code>
          <span className="delpi-ui-data-route-catalog__param-hint">{selected.id}</span>
        </details>
      ) : null}

      <button
        type="button"
        className="delpi-ui-data-route-catalog__confirm"
        onClick={() => onSelect(selected)}
      >
        {confirmLabel}
      </button>
    </aside>
  ) : (
    <aside className="delpi-ui-data-route-catalog__detail delpi-ui-data-route-catalog__detail--empty" aria-hidden={false}>
      <p className="delpi-ui-data-route-catalog__detail-body">
        Selecione uma fonte na lista para ver para que serve e quais filtros ela usa.
      </p>
    </aside>
  );

  return (
    <div
      className={[
        "delpi-ui-data-route-catalog",
        `delpi-ui-data-route-catalog--${density}`,
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <div className="delpi-ui-data-route-catalog__toolbar">
        <input
          type="search"
          className="delpi-ui-data-route-catalog__search"
          placeholder={searchPlaceholder}
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          aria-label={searchPlaceholder}
        />

        <div className="delpi-ui-data-route-catalog__chips" role="group" aria-label="Categorias">
          <button
            type="button"
            className={[
              "delpi-ui-data-route-catalog__chip",
              categoryFilter === "all" ? "delpi-ui-data-route-catalog__chip--active" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            onClick={() => setCategoryFilter("all")}
          >
            Todas
            <span className="delpi-ui-data-route-catalog__chip-count">{enriched.length}</span>
          </button>
          {categoryChipKeys.map((key) => (
            <button
              key={key}
              type="button"
              className={[
                "delpi-ui-data-route-catalog__chip",
                categoryFilter === key ? "delpi-ui-data-route-catalog__chip--active" : "",
              ]
                .filter(Boolean)
                .join(" ")}
              onClick={() => setCategoryFilter(key)}
            >
              {categoryLabels[key] ?? key}
              <span className="delpi-ui-data-route-catalog__chip-count">{categoryCounts.get(key) ?? 0}</span>
            </button>
          ))}
        </div>

        {showDisplayKindFilters ? (
          <div
            className="delpi-ui-data-route-catalog__chips delpi-ui-data-route-catalog__chips--kinds"
            role="group"
            aria-label="Forma dos dados"
          >
            {(Object.keys(DISPLAY_KIND_LABELS) as DataRouteDisplayKind[]).map((kind) => (
              <button
                key={kind}
                type="button"
                className={[
                  "delpi-ui-data-route-catalog__chip",
                  "delpi-ui-data-route-catalog__chip--kind",
                  kindFilters.includes(kind) ? "delpi-ui-data-route-catalog__chip--active" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                onClick={() => toggleKind(kind)}
                aria-pressed={kindFilters.includes(kind)}
              >
                {DISPLAY_KIND_LABELS[kind]}
              </button>
            ))}
          </div>
        ) : null}

        <p className="delpi-ui-data-route-catalog__status" aria-live="polite">
          {loading
            ? "Carregando catálogo…"
            : error
              ? null
              : `${filtered.length} fonte${filtered.length === 1 ? "" : "s"}${
                  categoryFilter !== "all" ? ` · ${categoryLabels[categoryFilter] ?? categoryFilter}` : ""
                }`}
        </p>
        {error ? (
          <p className="delpi-ui-data-route-catalog__status delpi-ui-data-route-catalog__status--error">
            {error}
          </p>
        ) : null}
        {!loading && !error && grouped.length === 0 ? (
          <p className="delpi-ui-data-route-catalog__status">
            {emptyMessage}
            {hasActiveFilters ? (
              <>
                {" "}
                <button
                  type="button"
                  className="delpi-ui-data-route-catalog__clear"
                  onClick={() => {
                    setQuery("");
                    setCategoryFilter("all");
                    setKindFilters([]);
                  }}
                >
                  Limpar filtros
                </button>
              </>
            ) : null}
          </p>
        ) : null}
      </div>

      <div className="delpi-ui-data-route-catalog__main">
        <div className="delpi-ui-data-route-catalog__groups">
          {grouped.map((group) => (
            <section key={group.key} className="delpi-ui-data-route-catalog__group">
              <h3 className="delpi-ui-data-route-catalog__group-title">
                {renderCategoryIcon(group.key)}
                <span>
                  {group.label} · {group.items.length}
                </span>
              </h3>
              <ul className="delpi-ui-data-route-catalog__list">
                {group.items.map((item) => {
                  const active = item.id === selectedId;
                  return (
                    <li key={item.id}>
                      <button
                        type="button"
                        className={[
                          "delpi-ui-data-route-catalog__card",
                          active ? "delpi-ui-data-route-catalog__card--active" : "",
                        ]
                          .filter(Boolean)
                          .join(" ")}
                        aria-pressed={active}
                        onClick={() => setSelectedId(item.id)}
                        onDoubleClick={() => onSelect(item)}
                      >
                        <span className="delpi-ui-data-route-catalog__card-head">
                          <span className="delpi-ui-data-route-catalog__card-title">{item.label}</span>
                          <span className="delpi-ui-data-route-catalog__mode">
                            {DISPLAY_KIND_LABELS[item.primaryKind]}
                          </span>
                        </span>
                        <span className="delpi-ui-data-route-catalog__card-desc">
                          {truncateText(item.audienceDescription, descClamp)}
                        </span>
                        <span className="delpi-ui-data-route-catalog__card-meta">{item.paramHint}</span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            </section>
          ))}
        </div>
        {detail}
      </div>
    </div>
  );
}

export type { DataRouteParamFieldSummary } from "./dataRouteCatalogHelpers";
export {
  countRequiredParams,
  formatParamHintLine,
  humanizeMetaShape,
  isParamFieldOptional,
  isTemplatedRouteDescription,
  resolveRouteAudienceDescription,
  summarizeRouteParams,
  truncateText,
} from "./dataRouteCatalogHelpers";
