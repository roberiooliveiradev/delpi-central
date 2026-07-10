import { useMemo, useState, type ReactNode } from "react";
import { Factory } from "lucide-react";

export type DataRouteCatalogItem = {
  /** Identificador estável — tipicamente operationId. */
  id: string;
  label: string;
  category: string;
  description?: string;
  path?: string;
  httpMethod?: string;
};

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
};

function defaultCategoryIcon(category: string) {
  return <Factory size={16} aria-hidden="true" />;
}

function truncate(text: string, maxLength: number): string {
  const trimmed = text.trim();
  if (trimmed.length <= maxLength) return trimmed;
  return `${trimmed.slice(0, maxLength - 1).trim()}…`;
}

export function DataRouteCatalogPanel({
  items,
  onSelect,
  searchPlaceholder = "Buscar por nome, path ou categoria…",
  emptyMessage = "Nenhuma rota encontrada.",
  loading = false,
  error = null,
  categoryLabels = {},
  categoryOrder = [],
  renderCategoryIcon = defaultCategoryIcon,
  className = "",
}: DataRouteCatalogPanelProps) {
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return items;
    return items.filter((item) => {
      const haystack = [
        item.label,
        item.id,
        item.category,
        item.path ?? "",
        item.description ?? "",
      ]
        .join(" ")
        .toLowerCase();
      return haystack.includes(q);
    });
  }, [items, query]);

  const grouped = useMemo(() => {
    const buckets = new Map<string, DataRouteCatalogItem[]>();
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

  return (
    <div className={["delpi-ui-data-route-catalog", className].filter(Boolean).join(" ")}>
      <input
        type="search"
        className="delpi-ui-data-route-catalog__search"
        placeholder={searchPlaceholder}
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        aria-label={searchPlaceholder}
      />
      {loading ? <p className="delpi-ui-data-route-catalog__status">Carregando catálogo…</p> : null}
      {error ? <p className="delpi-ui-data-route-catalog__status delpi-ui-data-route-catalog__status--error">{error}</p> : null}
      {!loading && !error && grouped.length === 0 ? (
        <p className="delpi-ui-data-route-catalog__status">{emptyMessage}</p>
      ) : null}
      <div className="delpi-ui-data-route-catalog__groups">
        {grouped.map((group) => (
          <section key={group.key} className="delpi-ui-data-route-catalog__group">
            <h3 className="delpi-ui-data-route-catalog__group-title">
              {renderCategoryIcon(group.key)}
              <span>{group.label}</span>
            </h3>
            <ul className="delpi-ui-data-route-catalog__list">
              {group.items.map((item) => (
                <li key={item.id}>
                  <button
                    type="button"
                    className="delpi-ui-data-route-catalog__card"
                    onClick={() => onSelect(item)}
                  >
                    <span className="delpi-ui-data-route-catalog__card-head">
                      <span className="delpi-ui-data-route-catalog__card-title">{item.label}</span>
                      {item.httpMethod && item.path ? (
                        <span className="delpi-ui-data-route-catalog__badge">
                          {item.httpMethod} {item.path}
                        </span>
                      ) : null}
                    </span>
                    {item.description ? (
                      <span className="delpi-ui-data-route-catalog__card-desc">
                        {truncate(item.description, 120)}
                      </span>
                    ) : null}
                  </button>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </div>
  );
}
