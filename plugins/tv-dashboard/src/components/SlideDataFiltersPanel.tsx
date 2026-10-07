import { useEffect, useMemo, useState } from "react";
import { Filter } from "lucide-react";
import { listDataRoutes, type BranchScope, type TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useParamExpressionCapability } from "../hooks/useParamExpressionCapability";
import { applyDataParamRawUpdates, type DataParamUpdateValue } from "../utils/applyDataParamUpdates";
import {
  collectDataOperationIds,
  mergeRouteParamSchemas,
} from "../utils/collectPlaylistDataParamSchema";
import { periodParamFieldKeys } from "../utils/dateRangePresets";
import { listSlideInputVariableRefs } from "../utils/inputVariableEditor";
import { DataParamFields, type DataParamExpressionEditRequest } from "./DataParamFields";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DeckPropertySection } from "./deck/DeckPropertySection";
import { DeckSettingsAccordion } from "./deck/DeckSettingsAccordion";

type Props = {
  branchScope?: BranchScope | null;
  compact?: boolean;
};

/**
 * Filtros da tela (dataFilters).
 * Mesmo conjunto de campos que Programação pode exibir — a diferença é só a
 * precedência no merge: input > dados (fonte) > tela > programação.
 */
export function SlideDataFiltersPanel({
  branchScope = null,
  compact = false,
}: Props) {
  const { config, setDataFilters, openExpressionEditor } = useComunicadoEditor();
  const expressionSupport = useParamExpressionCapability();
  const [routes, setRoutes] = useState<TvDataRouteCatalogItem[]>([]);
  const filters = config.dataFilters ?? {};

  useEffect(() => {
    void listDataRoutes().then(setRoutes).catch(() => setRoutes([]));
  }, []);

  const operationIds = useMemo(
    () => collectDataOperationIds(config),
    [config],
  );

  const schema = useMemo(
    () => mergeRouteParamSchemas(routes, operationIds),
    [routes, operationIds],
  );

  const periodKeys = useMemo(
    () => periodParamFieldKeys(Object.keys(schema)),
    [schema],
  );

  function updateFilters(updates: Record<string, DataParamUpdateValue>) {
    const next = applyDataParamRawUpdates(filters, updates, schema);
    setDataFilters(Object.keys(next).length > 0 ? next : undefined);
  }

  if (operationIds.length === 0 || Object.keys(schema).length === 0) return null;

  const sharedProps = {
    schema,
    values: filters,
    branchScope,
    filterLayer: "aggregate" as const,
    expressionSupport,
    onEditExpression: (request: DataParamExpressionEditRequest) =>
      openExpressionEditor({ ...request, refInputKeys: listSlideInputVariableRefs(config.blocks) }),
  };
  const periodEntries = periodKeys.size > 0;
  const otherEntries = Object.keys(schema).some((key) => !periodKeys.has(key));

  const body = (
    <DeckPropertySection
      title="Filtros do slide"
      hint={TV_DASHBOARD_HELP_TOOLTIPS.fields.slideDataFilters}
      compact={compact}
    >
      {periodEntries ? (
        <>
          <p className="td-deck-inspector__hint td-data-param-group">Período</p>
          <DataParamFields
            {...sharedProps}
            idPrefix="td-slide-filter-period"
            onlyParams={periodKeys}
            onChange={updateFilters}
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
            idPrefix="td-slide-filter"
            excludeParams={periodKeys}
            onChange={updateFilters}
          />
        </>
      ) : null}
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
