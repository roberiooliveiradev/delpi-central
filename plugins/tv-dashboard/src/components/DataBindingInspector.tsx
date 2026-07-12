import { useState, type ReactNode } from "react";
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
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";

import type { BranchScope, TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DataParamFields, visibleParamSchema, type DataParamSchema } from "./DataParamFields";
import { DataRoutePickerModal } from "./DataRoutePickerModal";
import type { PanelLayout } from "./SelectedDataSidePanel";
import { DeckField } from "./deck/DeckField";
import { DeckPropertySection } from "./deck/DeckPropertySection";

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
  return typeof limit === "number" && Number.isFinite(limit) ? Math.round(limit) : 90;
}

function RibbonZone({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="td-deck-ribbon__panel-zone">
      <h4 className="td-deck-ribbon__panel-zone-title">{title}</h4>
      {children}
    </div>
  );
}

export function DataBindingInspector({
  route,
  pane = false,
  layout = "pane",
  branchScope = null,
  /** Quando definido, edita este bloco (ex.: fonte ligada a um visual) em vez do selecionado. */
  block: blockOverride = null,
}: {
  route: TvDataRouteCatalogItem | null;
  pane?: boolean;
  layout?: PanelLayout;
  branchScope?: BranchScope | null;
  block?: ComunicadoBlock | null;
}) {
  const {
    selected,
    config,
    updateSelected,
    updateBlock,
    duplicateSelected,
    replaceSelectedDataRoute,
    globalRefreshSec,
    setLastDataDisplayMode,
  } = useComunicadoEditor();
  const [routePickerOpen, setRoutePickerOpen] = useState(false);
  const isRibbon = layout === "ribbon";

  const target = blockOverride ?? selected;
  if (!target || !("dataBinding" in target)) return null;
  if (!isDataBlockType(target.type) && !isDataSourceBlockType(target.type)) return null;

  const editingLinkedSource = Boolean(blockOverride && selected && blockOverride.id !== selected.id);
  const binding = target.dataBinding;
  const applyPatch = (patch: Partial<ComunicadoBlock>) => {
    if (blockOverride) {
      updateBlock(blockOverride.id, patch);
    } else {
      updateSelected(patch);
    }
  };
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
  const showPresentationMode = isDataBlockType(target.type) && !isDataSourceBlockType(target.type);
  const showTableOptions = showPresentationMode && currentDisplayMode === "table";
  const paramSchema = visibleParamSchema(
    (route?.paramSchema ?? undefined) as DataParamSchema | undefined,
    route?.fixedQueryParams,
  );

  function updateParam(key: string, raw: string) {
    const nextParams = { ...(binding.params ?? {}) };
    const fieldType = (paramSchema[key] as { type?: string } | undefined)?.type;
    if (!raw.trim()) {
      delete nextParams[key];
    } else if (fieldType === "integer" || fieldType === "number") {
      nextParams[key] = Number(raw);
    } else if (fieldType === "boolean") {
      nextParams[key] = raw === "true";
    } else {
      nextParams[key] = raw.trim();
    }
    applyPatch({
      dataBinding: { ...binding, params: nextParams },
    } as Partial<ComunicadoBlock>);
  }

  function updateDisplayMode(displayMode: ComunicadoDataDisplayMode) {
    const blockType = blockTypeForDisplayMode(displayMode, suggestedModes);
    setLastDataDisplayMode(displayMode === "auto" ? "kpi" : displayMode);
    applyPatch({
      type: blockType,
      frame: defaultFrame(blockType),
      dataBinding: { ...binding, displayMode: displayMode === "auto" ? "kpi" : displayMode },
    } as Partial<ComunicadoBlock>);
  }

  const connectionFields = (
    <>
      <p className="td-deck-inspector__meta">{route?.label ?? binding.operationId}</p>
      <div className="td-deck-inspector__actions">
        {!editingLinkedSource ? (
          <button type="button" className="td-btn td-btn--sm" onClick={() => duplicateSelected()}>
            <Copy size={14} aria-hidden="true" />
            Duplicar
          </button>
        ) : null}
        {!editingLinkedSource ? (
          <button type="button" className="td-btn td-btn--sm" onClick={() => setRoutePickerOpen(true)}>
            <RefreshCw size={14} aria-hidden="true" />
            Trocar rota
          </button>
        ) : null}
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
            applyPatch({
              dataBinding: { ...binding, label: value || undefined },
            } as Partial<ComunicadoBlock>)
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
              applyPatch({ dataBinding: nextBinding } as Partial<ComunicadoBlock>);
            }}
            options={[
              { value: "", label: "Automático (primeiro disponível)" },
              ...valueFieldOptions.map((field) => ({ value: field, label: field })),
            ]}
          />
        </DeckField>
      ) : null}
    </>
  );

  const paramFields = (
    <DataParamFields
      schema={paramSchema}
      values={blockParams}
      inheritedKeys={inheritedKeys}
      branchScope={branchScope}
      layout={layout}
      onChange={updateParam}
    />
  );

  const refreshFields = (
    <>
      {showTableOptions ? (
        <DeckField id="td-data-max-rows" label="Máximo de linhas (consulta)">
          <NativeTextControl
            id="td-data-max-rows"
            type="number"
            min={1}
            max={maxRowsLimit}
            placeholder={`Padrão da rota (até ${maxRowsLimit})`}
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
              applyPatch({ dataBinding: nextBinding } as Partial<ComunicadoBlock>);
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
            applyPatch({ dataBinding: nextBinding } as Partial<ComunicadoBlock>);
          }}
        />
      </DeckField>
    </>
  );

  const picker = !editingLinkedSource ? (
    <DataRoutePickerModal
      open={routePickerOpen}
      onClose={() => setRoutePickerOpen(false)}
      onSelect={(block) => {
        replaceSelectedDataRoute(block);
        setRoutePickerOpen(false);
      }}
    />
  ) : null;

  if (isRibbon) {
    return (
      <>
        <RibbonZone title={editingLinkedSource ? "Fonte ligada" : "Conexão"}>
          <div className="td-deck-ribbon__field-grid">{connectionFields}</div>
        </RibbonZone>
        <RibbonZone title="Parâmetros da fonte">
          {Object.keys(paramSchema).length > 0 ? (
            paramFields
          ) : (
            <p className="td-deck-inspector__hint">Nenhum parâmetro editável nesta rota.</p>
          )}
        </RibbonZone>
        <RibbonZone title="Atualização">
          <div className="td-deck-ribbon__field-grid">{refreshFields}</div>
        </RibbonZone>
        {picker}
      </>
    );
  }

  return (
    <>
      <DeckPropertySection
        pane={pane}
        title={editingLinkedSource ? "Parâmetros da fonte" : "Dados"}
        hint="Parâmetros deste bloco sobrescrevem filtros do slide."
      >
        {connectionFields}
        {refreshFields}
        {paramFields}
      </DeckPropertySection>
      {picker}
    </>
  );
}
