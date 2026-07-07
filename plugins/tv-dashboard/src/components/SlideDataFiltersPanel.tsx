import { useEffect, useState } from "react";

import { listDataRoutes, type TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DeckField } from "./deck/DeckField";
import { DeckPropertySection } from "./deck/DeckPropertySection";

type ParamSchema = Record<string, { type?: string; label?: string; default?: string | number; optional?: boolean }>;

export function SlideDataFiltersPanel() {
  const { config, setDataFilters } = useComunicadoEditor();
  const [routes, setRoutes] = useState<TvDataRouteCatalogItem[]>([]);
  const filters = config.dataFilters ?? {};

  useEffect(() => {
    void listDataRoutes().then(setRoutes).catch(() => setRoutes([]));
  }, []);

  const schema = mergeParamSchemas(routes);

  function updateFilter(key: string, raw: string) {
    const next = { ...filters };
    if (!raw.trim()) delete next[key];
    else if (schema[key]?.type === "integer") next[key] = Number(raw);
    else next[key] = raw.trim();
    setDataFilters(Object.keys(next).length > 0 ? next : undefined);
  }

  if (Object.keys(schema).length === 0) return null;

  return (
    <DeckPropertySection title="Filtros do slide" hint="Aplicam-se a todos os indicadores deste slide.">
      {Object.entries(schema).map(([key, field]) => (
        <DeckField key={key} id={`td-slide-filter-${key}`} label={field.label ?? key}>
          <input
            id={`td-slide-filter-${key}`}
            type={field.type === "integer" ? "number" : "text"}
            placeholder={field.optional ? "Opcional" : ""}
            value={filters[key] === undefined ? "" : String(filters[key])}
            onChange={(event) => updateFilter(key, event.target.value)}
          />
        </DeckField>
      ))}
    </DeckPropertySection>
  );
}

function mergeParamSchemas(routes: TvDataRouteCatalogItem[]): ParamSchema {
  const merged: ParamSchema = {};
  for (const route of routes) {
    for (const [key, field] of Object.entries(route.paramSchema ?? {})) {
      if (!merged[key]) merged[key] = field as ParamSchema[string];
    }
  }
  return merged;
}
