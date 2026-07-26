import { useEffect, useMemo, useState } from "react";
import type { BranchScope } from "../api/tvDashboardApi";
import { listDataRoutes, type TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import { applyDataParamRawUpdates } from "../utils/applyDataParamUpdates";
import { DataParamFields, type DataParamSchema } from "./DataParamFields";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DeckPropertySection } from "./deck/DeckPropertySection";
import { DeckSettingsAccordion } from "./deck/DeckSettingsAccordion";

type Props = {
  branchScope?: BranchScope | null;
  compact?: boolean;
};

export function SlideDataFiltersPanel({ branchScope = null, compact = false }: Props) {
  const { config, setDataFilters } = useComunicadoEditor();
  const [routes, setRoutes] = useState<TvDataRouteCatalogItem[]>([]);
  const filters = config.dataFilters ?? {};

  useEffect(() => {
    void listDataRoutes().then(setRoutes).catch(() => setRoutes([]));
  }, []);

  const schema = useMemo(() => mergeParamSchemas(routes), [routes]);

  function updateFilters(updates: Record<string, string>) {
    const next = applyDataParamRawUpdates(filters, updates, schema);
    setDataFilters(Object.keys(next).length > 0 ? next : undefined);
  }

  if (Object.keys(schema).length === 0) return null;

  const body = (
    <DeckPropertySection
      title="Filtros do slide"
      hint="Aplicam-se a todos os blocos de dados deste slide."
      compact={compact}
    >
      <DataParamFields
        schema={schema}
        values={filters}
        branchScope={branchScope}
        idPrefix="td-slide-filter"
        onChange={updateFilters}
      />
    </DeckPropertySection>
  );

  if (compact) {
    return (
      <DeckSettingsAccordion summary="Filtros" ariaLabel="Filtros de dados do slide">
        {body}
      </DeckSettingsAccordion>
    );
  }

  return body;
}

function mergeParamSchemas(routes: TvDataRouteCatalogItem[]): DataParamSchema {
  const merged: DataParamSchema = {};
  for (const route of routes) {
    for (const [key, field] of Object.entries(route.paramSchema ?? {})) {
      if (!merged[key]) merged[key] = field as DataParamSchema[string];
    }
  }
  return merged;
}
