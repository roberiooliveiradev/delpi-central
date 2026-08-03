import { useEffect, useMemo, useState } from "react";
import { listDataRoutes, type BranchScope, type Slide, type TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { applyDataParamRawUpdates } from "../utils/applyDataParamUpdates";
import {
  asDataFilterValues,
  collectPlaylistDataParamSchema,
} from "../utils/collectPlaylistDataParamSchema";
import { DataParamFields } from "./DataParamFields";

type Props = {
  slides: Slide[];
  values: Record<string, unknown> | null | undefined;
  branchScope?: BranchScope | null;
  onChange: (next: Record<string, string | number | boolean>) => void;
};

/** Campos de dataDefaults da programação — schema = união das fontes usadas. */
export function PlaylistDataFiltersFields({
  slides,
  values,
  branchScope = null,
  onChange,
}: Props) {
  const [routes, setRoutes] = useState<TvDataRouteCatalogItem[]>([]);

  useEffect(() => {
    void listDataRoutes().then(setRoutes).catch(() => setRoutes([]));
  }, []);

  const schema = useMemo(
    () => collectPlaylistDataParamSchema(slides, routes),
    [slides, routes],
  );

  const filterValues = useMemo(() => asDataFilterValues(values), [values]);

  if (Object.keys(schema).length === 0) {
    return (
      <p className="td-deck-playlist-filters__empty">
        {TV_DASHBOARD_HELP_TOOLTIPS.data.playlistFiltersEmpty}
      </p>
    );
  }

  return (
    <DataParamFields
      schema={schema}
      values={filterValues}
      branchScope={branchScope}
      idPrefix="td-playlist-filter"
      hydrateDefaultPreset={false}
      filterLayer="aggregate"
      onChange={(updates) => {
        onChange(applyDataParamRawUpdates(filterValues, updates, schema));
      }}
    />
  );
}
