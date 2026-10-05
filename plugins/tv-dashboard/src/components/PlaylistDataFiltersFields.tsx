import { useEffect, useMemo, useState } from "react";
import type { ParamExpressionSpec } from "@delpi/tv-dashboard-presentation";
import { listDataRoutes, type BranchScope, type Slide, type TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useParamExpressionCapability } from "../hooks/useParamExpressionCapability";
import { applyDataParamRawUpdates } from "../utils/applyDataParamUpdates";
import {
  asDataFilterValues,
  collectPlaylistDataParamSchema,
} from "../utils/collectPlaylistDataParamSchema";
import { periodParamFieldKeys } from "../utils/dateRangePresets";
import { DataParamFields } from "./DataParamFields";
import { useComunicadoEditor } from "./comunicadoEditorContext";

type Props = {
  slides: Slide[];
  values: Record<string, unknown> | null | undefined;
  branchScope?: BranchScope | null;
  onChange: (next: Record<string, string | number | boolean | ParamExpressionSpec>) => void;
};

/**
 * Campos de dataDefaults da programação — schema = união das fontes usadas
 * (blocos data_* + inputs de DataModel de todos os slides). Mesmo presenter
 * e mesma capability de Tela: período + expressões + filtros literais.
 */
export function PlaylistDataFiltersFields({
  slides,
  values,
  branchScope = null,
  onChange,
}: Props) {
  const { openExpressionEditor } = useComunicadoEditor();
  const expressionSupport = useParamExpressionCapability();
  const [routes, setRoutes] = useState<TvDataRouteCatalogItem[]>([]);

  useEffect(() => {
    void listDataRoutes().then(setRoutes).catch(() => setRoutes([]));
  }, []);

  const schema = useMemo(
    () => collectPlaylistDataParamSchema(slides, routes),
    [slides, routes],
  );

  const filterValues = useMemo(() => asDataFilterValues(values), [values]);
  const periodKeys = useMemo(
    () => periodParamFieldKeys(Object.keys(schema)),
    [schema],
  );

  if (Object.keys(schema).length === 0) {
    return (
      <p className="td-deck-playlist-filters__empty">
        {TV_DASHBOARD_HELP_TOOLTIPS.data.playlistFiltersEmpty}
      </p>
    );
  }

  const applyUpdates = (updates: Record<string, import("../utils/applyDataParamUpdates").DataParamUpdateValue>) =>
    onChange(applyDataParamRawUpdates(filterValues, updates, schema));

  const sharedProps = {
    schema,
    values: filterValues,
    branchScope,
    filterLayer: "aggregate" as const,
    expressionSupport,
    onEditExpression: openExpressionEditor,
  };
  const periodEntries = periodKeys.size > 0;
  const otherEntries = Object.keys(schema).some((key) => !periodKeys.has(key));

  return (
    <>
      {periodEntries ? (
        <>
          <p className="td-deck-inspector__hint td-data-param-group">Período</p>
          <DataParamFields
            {...sharedProps}
            idPrefix="td-playlist-filter-period"
            onlyParams={periodKeys}
            onChange={applyUpdates}
          />
        </>
      ) : null}
      {otherEntries ? (
        <>
          {periodEntries ? (
            <p className="td-deck-inspector__hint td-data-param-group">Filtros</p>
          ) : null}
          <DataParamFields
            {...sharedProps}
            idPrefix="td-playlist-filter"
            excludeParams={periodKeys}
            onChange={applyUpdates}
          />
        </>
      ) : null}
    </>
  );
}
