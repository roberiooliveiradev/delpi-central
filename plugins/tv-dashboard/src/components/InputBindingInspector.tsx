import { useEffect, useMemo, useState } from "react";
import {
  intersectParamSchemaKeys,
  isFetchableDataBlockType,
  listDataSourceBlocks,
  type ComunicadoInputBlock,
} from "@delpi/tv-dashboard-presentation";
import { FormSelectControl, LucideIconField, NativeTextControl } from "@delpi/plugin-ui/index";

import { listDataRoutes, type TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import { TV_DASHBOARD_ROOT_CLASS } from "../constants/pluginRootClass";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DataParamFields, type DataParamSchema } from "./DataParamFields";
import { DeckField } from "./deck/DeckField";
import { DeckPropertySection } from "./deck/DeckPropertySection";
import {
  DATE_RANGE_PRESET_PARAM,
  PERIOD_DAYS_PARAM,
  findDateRangeKeys,
} from "../utils/dateRangePresets";
import {
  buildInputEditorValues,
  buildInputValueEditorSchema,
  intersectInputParamKeysWithPresets,
  parseInputFilterValue,
} from "../utils/inputFilterParamSchema";

type Props = {
  pane?: boolean;
};

const INPUT_DATA_PATCH_KEYS = new Set([
  "defaultValue",
  "paramKey",
  "targetScope",
  "targetSourceIds",
]);

function schemasForTargets(
  routes: TvDataRouteCatalogItem[],
  operationIds: string[],
): DataParamSchema[] {
  return operationIds
    .map((operationId) => {
      const route = routes.find((item) => item.operationId === operationId);
      return (route?.paramSchema ?? {}) as DataParamSchema;
    })
    .filter((schema) => Object.keys(schema).length > 0);
}

export function InputBindingInspector({ pane = false }: Props) {
  const { selected, config, patchInputBlock, scheduleInputFilterRefresh } = useComunicadoEditor();
  const [routes, setRoutes] = useState<TvDataRouteCatalogItem[]>([]);

  useEffect(() => {
    void listDataRoutes().then(setRoutes).catch(() => setRoutes([]));
  }, []);

  const block = selected?.type === "input" ? (selected as ComunicadoInputBlock) : null;

  const fetchable = useMemo(
    () => (config.blocks ?? []).filter((item) => isFetchableDataBlockType(item.type)),
    [config.blocks],
  );

  const targetScope = block?.input?.targetScope === "sources" ? "sources" : "slide";
  const targetSourceIds = block?.input?.targetSourceIds ?? [];

  const targetBlocks = useMemo(() => {
    if (!block) return [];
    if (targetScope === "slide") return fetchable;
    const idSet = new Set(targetSourceIds);
    return fetchable.filter((item) => idSet.has(item.id));
  }, [block, fetchable, targetScope, targetSourceIds]);

  const operationIds = useMemo(
    () =>
      targetBlocks
        .map((item) =>
          "dataBinding" in item && item.dataBinding?.operationId
            ? item.dataBinding.operationId
            : "",
        )
        .filter(Boolean),
    [targetBlocks],
  );

  const schemas = useMemo(() => schemasForTargets(routes, operationIds), [routes, operationIds]);
  const paramKeys = useMemo(() => intersectInputParamKeysWithPresets(schemas), [schemas]);
  const valueSchema = useMemo(
    () => (block?.input?.paramKey ? buildInputValueEditorSchema(schemas, block.input.paramKey) : {}),
    [block?.input?.paramKey, schemas],
  );
  const editorValues = useMemo(
    () =>
      block
        ? buildInputEditorValues(block, config.dataFilters ?? {}, valueSchema)
        : {},
    [block, config.dataFilters, valueSchema],
  );
  const datePair = useMemo(
    () => findDateRangeKeys(schemas.flatMap((schema) => Object.keys(schema))),
    [schemas],
  );

  if (!block) return null;

  const sources = listDataSourceBlocks(config.blocks ?? []);

  const applyInputPatch = (patch: Partial<ComunicadoInputBlock["input"]>) => {
    const nextBlock: ComunicadoInputBlock = {
      ...block,
      input: { ...block.input, ...patch },
    };
    patchInputBlock(block.id, patch);
    if (Object.keys(patch).some((key) => INPUT_DATA_PATCH_KEYS.has(key))) {
      scheduleInputFilterRefresh(nextBlock);
    }
  };

  const applyFilterFieldChange = (key: string, raw: string) => {
    const fieldType = valueSchema[key]?.type;
    const parsed = parseInputFilterValue(key, raw, fieldType);
    const paramKey = String(block.input.paramKey || "").trim();
    const filterBundle: Record<string, string | number | boolean | null | undefined> = {
      [key]: parsed,
    };

    if (datePair && (key === datePair.startKey || key === datePair.endKey)) {
      filterBundle[DATE_RANGE_PRESET_PARAM] = "custom";
    }

    if (key === DATE_RANGE_PRESET_PARAM) {
      applyInputPatch({ defaultValue: parsed });
      if (targetScope === "slide") {
        patchInputBlock(
          block.id,
          { defaultValue: parsed },
          {
            [DATE_RANGE_PRESET_PARAM]: parsed,
            ...(parsed !== "last_n_days" ? { [PERIOD_DAYS_PARAM]: null } : {}),
            ...(parsed !== "custom" && datePair
              ? { [datePair.startKey]: null, [datePair.endKey]: null }
              : {}),
          },
        );
      }
      scheduleInputFilterRefresh({ ...block, input: { ...block.input, defaultValue: parsed } });
      return;
    }

    if (key === PERIOD_DAYS_PARAM) {
      if (targetScope === "slide") {
        patchInputBlock(block.id, {}, filterBundle);
      }
      scheduleInputFilterRefresh(block);
      return;
    }

    if (key === paramKey) {
      applyInputPatch({ defaultValue: parsed });
      if (targetScope === "slide") {
        patchInputBlock(block.id, { defaultValue: parsed }, filterBundle);
      }
      return;
    }

    if (targetScope === "slide") {
      patchInputBlock(block.id, {}, filterBundle);
      scheduleInputFilterRefresh(block);
    }
  };

  const applyFilterUpdates = (updates: Record<string, string>) => {
    // Preset relativo: um patch atômico (datas/periodDays limpos no mesmo bundle).
    if (DATE_RANGE_PRESET_PARAM in updates) {
      applyFilterFieldChange(DATE_RANGE_PRESET_PARAM, updates[DATE_RANGE_PRESET_PARAM] ?? "");
      return;
    }
    const entries = Object.entries(updates);
    if (entries.length === 0) return;
    if (entries.length === 1) {
      applyFilterFieldChange(entries[0][0], entries[0][1]);
      return;
    }
    // Lote (ex.: data + dateRangePreset=custom): um único filterBundle.
    const filterBundle: Record<string, string | number | boolean | null | undefined> = {};
    let primaryKey = "";
    let primaryRaw = "";
    for (const [key, raw] of entries) {
      if (!primaryKey) {
        primaryKey = key;
        primaryRaw = raw;
      }
      filterBundle[key] = parseInputFilterValue(key, raw, valueSchema[key]?.type);
    }
    const paramKey = String(block.input.paramKey || "").trim();
    if (primaryKey === paramKey) {
      applyInputPatch({ defaultValue: filterBundle[primaryKey] });
      if (targetScope === "slide") {
        patchInputBlock(block.id, { defaultValue: filterBundle[primaryKey] }, filterBundle);
      }
      return;
    }
    if (targetScope === "slide") {
      patchInputBlock(block.id, {}, filterBundle);
      scheduleInputFilterRefresh(block);
    } else {
      applyFilterFieldChange(primaryKey, primaryRaw);
    }
  };

  const labelByKey = (key: string): string => {
    if (key === DATE_RANGE_PRESET_PARAM) return "Período relativo";
    for (const schema of schemas) {
      const label = schema[key]?.label;
      if (typeof label === "string" && label.trim()) return label;
    }
    return key;
  };

  return (
    <div id="td-input-binding">
      <DeckPropertySection
        pane={pane}
        title="Campo / Filtro"
        hint={TV_DASHBOARD_HELP_TOOLTIPS.data.inputFilterPresets}
      >
        {fetchable.length === 0 ? (
          <p className="td-deck-inspector__hint">
            Inclua uma fonte de dados no slide antes de configurar o filtro.
          </p>
        ) : null}

        <DeckField id="td-input-scope" label="Alvo">
          <FormSelectControl
            id="td-input-scope"
            ariaLabel="Alvo do filtro"
            portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
            value={targetScope}
            onChange={(value) =>
              applyInputPatch({
                targetScope: value === "sources" ? "sources" : "slide",
                targetSourceIds: value === "sources" ? targetSourceIds : undefined,
              })
            }
            options={[
              { value: "slide", label: "Todo o slide" },
              { value: "sources", label: "Fontes selecionadas" },
            ]}
          />
        </DeckField>

        {targetScope === "sources" ? (
          <fieldset className="td-deck-inspector__fieldset">
            <legend className="td-deck-inspector__legend">Fontes</legend>
            {sources.length === 0 ? (
              <p className="td-deck-inspector__hint">Nenhuma fonte no slide.</p>
            ) : (
              sources.map((source) => {
                const checked = targetSourceIds.includes(source.id);
                const label = source.dataBinding?.label || source.dataBinding?.operationId || source.id;
                return (
                  <label key={source.id} className="td-deck-inspector__checkbox">
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={(event) => {
                        const next = event.target.checked
                          ? [...targetSourceIds, source.id]
                          : targetSourceIds.filter((id) => id !== source.id);
                        applyInputPatch({ targetSourceIds: next, targetScope: "sources" });
                      }}
                    />
                    {label}
                  </label>
                );
              })
            )}
          </fieldset>
        ) : null}

        <DeckField
          id="td-input-param"
          label="Parâmetro"
          hint={
            paramKeys.length === 0
              ? "Nenhum parâmetro em comum nas fontes alvo (interseção vazia)."
              : "Somente chaves do paramSchema das rotas alvo. Use «Período relativo» para presets como «Este mês (até hoje)»."
          }
        >
          <FormSelectControl
            id="td-input-param"
            ariaLabel="Parâmetro da rota"
            portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
            value={block.input.paramKey || ""}
            onChange={(value) => applyInputPatch({ paramKey: value, defaultValue: null })}
            options={[
              { value: "", label: "Selecione…" },
              ...paramKeys.map((key) => ({
                value: key,
                label: labelByKey(key),
              })),
            ]}
          />
        </DeckField>

        <DeckField id="td-input-label" label="Rótulo (opcional)">
          <NativeTextControl
            id="td-input-label"
            value={block.input.label ?? ""}
            onChange={(value) => applyInputPatch({ label: value.trim() || undefined })}
          />
        </DeckField>

        <DeckField id="td-input-icon" label="Ícone (opcional)">
          <LucideIconField
            value={block.input.iconName ?? ""}
            defaultIcon="Filter"
            nameFormat="pascal"
            curatedOnly={false}
            labels={{ clear: "Sem ícone", close: "Fechar" }}
            onChange={(name) =>
              applyInputPatch({ iconName: name?.trim() ? name.trim() : undefined })
            }
            ariaLabel="Selecionar ícone do filtro"
          />
        </DeckField>

        {block.input.paramKey && Object.keys(valueSchema).length > 0 ? (
          <DataParamFields
            schema={valueSchema}
            values={editorValues}
            idPrefix="td-input-value"
            onChange={applyFilterUpdates}
          />
        ) : null}
      </DeckPropertySection>
    </div>
  );
}
