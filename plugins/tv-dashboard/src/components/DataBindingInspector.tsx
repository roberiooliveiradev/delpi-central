import { useState } from "react";
import { Copy, RefreshCw } from "lucide-react";
import { NativeSelectControl } from "@delpi/plugin-ui/index";
import {
  blockTypeForDisplayMode,
  defaultFrame,
  displayModeLabel,
  isDataBlockType,
  listDataPresentationOptions,
  type ComunicadoDataBinding,
  type ComunicadoDataDisplayMode,
} from "@delpi/tv-dashboard-presentation";

import type { TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DataRoutePickerModal } from "./DataRoutePickerModal";
import { DeckField } from "./deck/DeckField";
import { DeckPropertySection } from "./deck/DeckPropertySection";

type ParamSchema = Record<string, { type?: string; label?: string; default?: string | number; optional?: boolean }>;

function routeDisplayModes(route: TvDataRouteCatalogItem | null): string[] | undefined {
  if (!route) return undefined;
  return route.suggestedDisplayModes ?? route.allowedDisplayModes;
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
            <input
              id={`td-data-param-${key}`}
              type={field.type === "integer" ? "number" : "text"}
              placeholder={inherited ? "Herdado do slide" : field.optional ? "Opcional" : ""}
              value={current === undefined || current === null ? "" : String(current)}
              onChange={(event) => onChange(key, event.target.value)}
            />
          </DeckField>
        );
      })}
    </>
  );
}

export function DataBindingInspector({ route }: { route: TvDataRouteCatalogItem | null }) {
  const { selected, config, updateSelected, duplicateSelected, replaceSelectedDataRoute } =
    useComunicadoEditor();
  const [routePickerOpen, setRoutePickerOpen] = useState(false);

  if (!selected || !isDataBlockType(selected.type) || !("dataBinding" in selected)) return null;

  const binding = selected.dataBinding;
  const slideFilters = config.dataFilters ?? {};
  const blockParams = binding.params ?? {};
  const inheritedKeys = new Set(
    Object.keys(slideFilters).filter((key) => blockParams[key] === undefined || blockParams[key] === ""),
  );
  const displayModes = routeDisplayModes(route);
  const presentationOptions = listDataPresentationOptions(displayModes);
  const currentDisplayMode = (binding.displayMode ?? "auto") as ComunicadoDataDisplayMode;

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
    const blockType = blockTypeForDisplayMode(displayMode, displayModes);
    updateSelected({
      type: blockType,
      frame: defaultFrame(blockType),
      dataBinding: { ...binding, displayMode },
    } as Partial<typeof selected>);
  }

  return (
    <>
      <DeckPropertySection title="Dados" hint="Parâmetros deste bloco sobrescrevem filtros do slide.">
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
        {presentationOptions.length > 1 ? (
          <DeckField id="td-data-display-mode" label="Formato de apresentação">
            <NativeSelectControl
              id="td-data-display-mode"
              value={currentDisplayMode}
              onChange={(value) => updateDisplayMode(value as ComunicadoDataDisplayMode)}
              options={presentationOptions.map((option) => ({
                value: option.displayMode,
                label: displayModeLabel(option.displayMode),
              }))}
            />
          </DeckField>
        ) : (
          <p className="td-deck-inspector__meta">{displayModeLabel(currentDisplayMode)}</p>
        )}
        <DeckField id="td-data-label" label="Rótulo (opcional)">
          <input
            id="td-data-label"
            value={binding.label ?? ""}
            onChange={(event) =>
              updateSelected({
                dataBinding: { ...binding, label: event.target.value || undefined },
              } as Partial<typeof selected>)
            }
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
