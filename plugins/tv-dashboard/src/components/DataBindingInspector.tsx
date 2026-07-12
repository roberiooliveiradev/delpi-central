import { useState } from "react";
import { Copy, RefreshCw } from "lucide-react";
import { FormSelectControl, NativeTextControl } from "@delpi/plugin-ui/index";
import {
  blockTypeForDisplayMode,
  DATA_REFRESH_SEC_MAX,
  DATA_REFRESH_SEC_MIN,
  defaultFrame,
  displayModeOptionLabel,
  isDataBlockType,
  isDataSourceBlockType,
  listDataPresentationOptions,
  resolveDataBlockRefreshSec,
  type ComunicadoDataBinding,
  type ComunicadoDataDisplayMode,
} from "@delpi/tv-dashboard-presentation";

import type { TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DataRoutePickerModal } from "./DataRoutePickerModal";
import { DeckField } from "./deck/DeckField";
import { DeckPropertySection } from "./deck/DeckPropertySection";

type ParamSchema = Record<string, { type?: string; label?: string; default?: string | number; optional?: boolean }>;

function routeSuggestedModes(route: TvDataRouteCatalogItem | null): string[] | undefined {
  if (!route) return undefined;
  return route.suggestedDisplayModes ?? route.allowedDisplayModes;
}

function routeValueFieldOptions(route: TvDataRouteCatalogItem | null): string[] {
  const fields = route?.valueFields ?? [];
  return fields.map((field) => String(field).trim()).filter(Boolean);
}

function routeMaxRowsLimit(route: TvDataRouteCatalogItem | null): number {
  const limit = route?.tvConstraints?.maxRows;
  return typeof limit === "number" && Number.isFinite(limit) ? Math.round(limit) : 20;
}

function ParamFields({
  schema,
  values,
  inheritedKeys,
  onChange,
}: {
  schema: ParamSchema;
  values: ComunicadoDataBinding["params"];
  inheritedKeys: Set<string>;
  onChange: (key: string, value: string) => void;
}) {
  const entries = Object.entries(schema);
  if (entries.length === 0) return null;
  return (
    <>
      {entries.map(([key, field]) => {
        const inherited = inheritedKeys.has(key);
        const current = values?.[key];
        return (
          <DeckField
            key={key}
            id={`td-data-param-${key}`}
            label={`${field.label ?? key}${inherited ? " (herdado do slide)" : ""}`}
          >
            <NativeTextControl
              id={`td-data-param-${key}`}
              type={field.type === "integer" ? "number" : "text"}
              placeholder={inherited ? "Herdado do slide" : field.optional ? "Opcional" : ""}
              value={current === undefined || current === null ? "" : String(current)}
              onChange={(value) => onChange(key, value)}
            />
          </DeckField>
        );
      })}
    </>
  );
}

export function DataBindingInspector({ route, pane = false }: { route: TvDataRouteCatalogItem | null; pane?: boolean }) {
  const {
    selected,
    config,
    updateSelected,
    duplicateSelected,
    replaceSelectedDataRoute,
    globalRefreshSec,
    setLastDataDisplayMode,
  } = useComunicadoEditor();
  const [routePickerOpen, setRoutePickerOpen] = useState(false);

  if (!selected || !("dataBinding" in selected)) return null;
  if (!isDataBlockType(selected.type) && !isDataSourceBlockType(selected.type)) return null;

  const binding = selected.dataBinding;
  const slideFilters = config.dataFilters ?? {};
  const blockParams = binding.params ?? {};
  const inheritedKeys = new Set(
    Object.keys(slideFilters).filter((key) => blockParams[key] === undefined || blockParams[key] === ""),
  );
  const suggestedModes = routeSuggestedModes(route);
  const presentationOptions = listDataPresentationOptions(suggestedModes);
  const currentDisplayMode = (binding.displayMode ?? "kpi") as ComunicadoDataDisplayMode;
  const inheritedRefreshSec = resolveDataBlockRefreshSec(undefined, globalRefreshSec);
  const valueFieldOptions = routeValueFieldOptions(route);
  const maxRowsLimit = routeMaxRowsLimit(route);
  const showPresentationMode = isDataBlockType(selected.type) && !isDataSourceBlockType(selected.type);
  const showTableOptions = showPresentationMode && currentDisplayMode === "table";

  function updateParam(key: string, raw: string) {
    const nextParams = { ...(binding.params ?? {}) };
    if (!raw.trim()) {
      delete nextParams[key];
    } else if ((route?.paramSchema?.[key] as { type?: string } | undefined)?.type === "integer") {
      nextParams[key] = Number(raw);
    } else {
      nextParams[key] = raw.trim();
    }
    updateSelected({
      dataBinding: { ...binding, params: nextParams },
    } as Partial<typeof selected>);
  }

  function updateDisplayMode(displayMode: ComunicadoDataDisplayMode) {
    const blockType = blockTypeForDisplayMode(displayMode, suggestedModes);
    setLastDataDisplayMode(displayMode === "auto" ? "kpi" : displayMode);
    updateSelected({
      type: blockType,
      frame: defaultFrame(blockType),
      dataBinding: { ...binding, displayMode: displayMode === "auto" ? "kpi" : displayMode },
    } as Partial<typeof selected>);
  }

  return (
    <>
      <DeckPropertySection pane={pane} title="Dados" hint="Parâmetros deste bloco sobrescrevem filtros do slide.">
        <p className="td-deck-inspector__meta">{route?.label ?? binding.operationId}</p>
        <div className="td-deck-inspector__actions">
          <button type="button" className="td-btn td-btn--sm" onClick={() => duplicateSelected()}>
            <Copy size={14} aria-hidden="true" />
            Duplicar
          </button>
          <button type="button" className="td-btn td-btn--sm" onClick={() => setRoutePickerOpen(true)}>
            <RefreshCw size={14} aria-hidden="true" />
            Trocar rota
          </button>
        </div>
        {showPresentationMode ? (
          <DeckField id="td-data-display-mode" label="Formato de apresentação">
            <FormSelectControl
              id="td-data-display-mode"
              ariaLabel="Formato de apresentação"
              value={currentDisplayMode === "auto" ? "kpi" : currentDisplayMode}
              onChange={(value) => updateDisplayMode(value as ComunicadoDataDisplayMode)}
              options={presentationOptions.map((option) => ({
                value: option.displayMode,
                label: displayModeOptionLabel(option),
              }))}
            />
          </DeckField>
        ) : null}
        <DeckField id="td-data-label" label="Rótulo (opcional)">
          <NativeTextControl
            id="td-data-label"
            value={binding.label ?? ""}
            onChange={(value) =>
              updateSelected({
                dataBinding: { ...binding, label: value || undefined },
              } as Partial<typeof selected>)
            }
          />
        </DeckField>
        {valueFieldOptions.length > 0 ? (
          <DeckField id="td-data-value-field" label="Campo de valor">
            <FormSelectControl
              id="td-data-value-field"
              ariaLabel="Campo de valor"
              value={binding.valueField ?? ""}
              onChange={(value) => {
                const nextBinding: ComunicadoDataBinding = { ...binding };
                if (!value) {
                  delete nextBinding.valueField;
                } else {
                  nextBinding.valueField = value;
                }
                updateSelected({ dataBinding: nextBinding } as Partial<typeof selected>);
              }}
              options={[
                { value: "", label: "Automático (primeiro disponível)" },
                ...valueFieldOptions.map((field) => ({ value: field, label: field })),
              ]}
            />
          </DeckField>
        ) : null}
        {showTableOptions ? (
          <DeckField id="td-data-max-rows" label="Máximo de linhas">
            <NativeTextControl
              id="td-data-max-rows"
              type="number"
              min={1}
              max={maxRowsLimit}
              placeholder={`Padrão (até ${Math.min(maxRowsLimit, 5)})`}
              value={binding.maxRows ?? ""}
              onChange={(value) => {
                const raw = value.trim();
                const nextBinding: ComunicadoDataBinding = { ...binding };
                if (!raw) {
                  delete nextBinding.maxRows;
                } else {
                  const parsed = Number(raw);
                  if (Number.isFinite(parsed) && parsed >= 1) {
                    nextBinding.maxRows = Math.min(Math.round(parsed), maxRowsLimit);
                  }
                }
                updateSelected({ dataBinding: nextBinding } as Partial<typeof selected>);
              }}
            />
          </DeckField>
        ) : null}
        <DeckField
          id="td-data-refresh"
          label="Atualizar a cada (s)"
          hint={TV_DASHBOARD_HELP_TOOLTIPS.fields.dataBlockRefreshInterval}
        >
          <NativeTextControl
            id="td-data-refresh"
            type="number"
            min={DATA_REFRESH_SEC_MIN}
            max={DATA_REFRESH_SEC_MAX}
            placeholder={`Padrão (${inheritedRefreshSec}s)`}
            value={binding.refreshSec ?? ""}
            onChange={(value) => {
              const raw = value.trim();
              const nextBinding: ComunicadoDataBinding = { ...binding };
              if (!raw) {
                delete nextBinding.refreshSec;
              } else {
                const parsed = Number(raw);
                if (Number.isFinite(parsed)) {
                  nextBinding.refreshSec = parsed;
                }
              }
              updateSelected({ dataBinding: nextBinding } as Partial<typeof selected>);
            }}
          />
        </DeckField>
        <ParamFields
          schema={(route?.paramSchema as ParamSchema) ?? {}}
          values={blockParams}
          inheritedKeys={inheritedKeys}
          onChange={updateParam}
        />
      </DeckPropertySection>
      <DataRoutePickerModal
        open={routePickerOpen}
        onClose={() => setRoutePickerOpen(false)}
        onSelect={(block) => {
          replaceSelectedDataRoute(block);
          setRoutePickerOpen(false);
        }}
      />
    </>
  );
}
