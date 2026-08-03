import { useEffect, useMemo, useState } from "react";
import { Filter } from "lucide-react";
import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";
import { listDataRoutes, type BranchScope, type TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { applyDataParamRawUpdates } from "../utils/applyDataParamUpdates";
import {
  collectFetchableOperationIds,
  mergeRouteParamSchemas,
  omitSchemaKeysCoveredByDefaults,
} from "../utils/collectPlaylistDataParamSchema";
import { DataParamFields } from "./DataParamFields";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DeckPropertySection } from "./deck/DeckPropertySection";
import { DeckSettingsAccordion } from "./deck/DeckSettingsAccordion";

type Props = {
  branchScope?: BranchScope | null;
  compact?: boolean;
  /** dataDefaults da programação — chaves já definidas não repetem neste painel. */
  playlistDefaults?: Record<string, unknown> | null;
};

export function SlideDataFiltersPanel({
  branchScope = null,
  compact = false,
  playlistDefaults = null,
}: Props) {
  const { config, setDataFilters } = useComunicadoEditor();
  const [routes, setRoutes] = useState<TvDataRouteCatalogItem[]>([]);
  const filters = config.dataFilters ?? {};

  useEffect(() => {
    void listDataRoutes().then(setRoutes).catch(() => setRoutes([]));
  }, []);

  const operationIds = useMemo(
    () => collectFetchableOperationIds((config.blocks ?? []) as ComunicadoBlock[]),
    [config.blocks],
  );

  const schema = useMemo(() => {
    const merged = mergeRouteParamSchemas(routes, operationIds);
    return omitSchemaKeysCoveredByDefaults(merged, playlistDefaults);
  }, [routes, operationIds, playlistDefaults]);

  function updateFilters(updates: Record<string, string>) {
    const next = applyDataParamRawUpdates(filters, updates, schema);
    setDataFilters(Object.keys(next).length > 0 ? next : undefined);
  }

  if (operationIds.length === 0) return null;

  const emptyCoveredByDefaults =
    Object.keys(schema).length === 0 &&
    Boolean(playlistDefaults && Object.keys(playlistDefaults).length > 0);

  if (Object.keys(schema).length === 0 && !emptyCoveredByDefaults) return null;

  const body = (
    <DeckPropertySection
      title="Filtros do slide"
      hint={TV_DASHBOARD_HELP_TOOLTIPS.fields.slideDataFilters}
      compact={compact}
    >
      {Object.keys(schema).length === 0 ? (
        <p className="td-deck-playlist-filters__empty">
          {TV_DASHBOARD_HELP_TOOLTIPS.data.slideFiltersCoveredByDefaults}
        </p>
      ) : (
        <DataParamFields
          schema={schema}
          values={filters}
          branchScope={branchScope}
          idPrefix="td-slide-filter"
          hydrateDefaultPreset={false}
          onChange={updateFilters}
        />
      )}
    </DeckPropertySection>
  );

  if (compact) {
    return (
      <DeckSettingsAccordion
        summary="Filtros"
        ariaLabel="Filtros de dados do slide"
        icon={Filter}
      >
        {body}
      </DeckSettingsAccordion>
    );
  }

  return body;
}
