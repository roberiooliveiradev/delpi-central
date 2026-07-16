import { useEffect, useState, type ReactNode } from "react";
import { Copy, Play, RefreshCw, SlidersHorizontal } from "lucide-react";
import {
  DataRouteSamplePreview,
  FormSelectControl,
  NativeTextControl,
  type DataRoutePreviewPayload,
} from "@delpi/plugin-ui/index";
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
import { previewTvDataRoute } from "../utils/previewTvDataRoute";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import {
  DataParamFields,
  RIBBON_INLINE_PARAM_LIMIT,
  visibleParamSchema,
  type DataParamSchema,
} from "./DataParamFields";
import type { PanelLayout } from "./SelectedDataSidePanel";
import { DeckField } from "./deck/DeckField";
import { DeckPropertySection } from "./deck/DeckPropertySection";
import { Modal } from "./ui/Modal";
import type { ValueFieldOption } from "./ValueFieldsMultiSelect";

const REFRESH_PRESET_VALUES = new Set(["60", "120", "300", "600"]);

function routeSuggestedModes(route: TvDataRouteCatalogItem | null): string[] | undefined {
  if (!route) return undefined;
  return route.suggestedDisplayModes ?? route.allowedDisplayModes;
}

function routeValueFieldOptions(route: TvDataRouteCatalogItem | null): ValueFieldOption[] {
  const fields = route?.valueFields ?? [];
  const labels = route?.valueFieldLabels ?? {};
  return fields
    .map((field) => String(field).trim())
    .filter(Boolean)
    .map((field) => ({
      field,
      label: labels[field]?.trim() || field,
    }));
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
  /** Em ribbon com visual: ocultar conexão (já no VisualDataViewInspector). */
  sections,
  onOpenCatalog,
}: {
  route: TvDataRouteCatalogItem | null;
  pane?: boolean;
  layout?: PanelLayout;
  branchScope?: BranchScope | null;
  block?: ComunicadoBlock | null;
  sections?: Array<"connection" | "params" | "refresh">;
  onOpenCatalog?: () => void;
}) {
  const {
    selected,
    config,
    updateSelected,
    updateBlock,
    duplicateSelected,
    openDataCatalog,
    globalRefreshSec,
    setLastDataDisplayMode,
    playlistId,
  } = useComunicadoEditor();
  const [paramsModalOpen, setParamsModalOpen] = useState(false);
  const [refreshCustom, setRefreshCustom] = useState(false);
  const [testing, setTesting] = useState(false);
  const [livePreview, setLivePreview] = useState<DataRoutePreviewPayload | null>(null);
  const [testError, setTestError] = useState<string | null>(null);
  const isRibbon = layout === "ribbon";
  const compactSelect = isRibbon ? "delpi-ui-select--compact" : undefined;
  const compactNative = isRibbon ? "delpi-ui-native-control--compact" : undefined;
  const activeSections = sections ?? (["connection", "params", "refresh"] as const);

  const target = blockOverride ?? selected;
  const canEdit =
    Boolean(target) &&
    "dataBinding" in (target ?? {}) &&
    (isDataBlockType((target as ComunicadoBlock).type) ||
      isDataSourceBlockType((target as ComunicadoBlock).type));
  const targetId = target && "id" in target ? String(target.id) : "";
  const operationId =
    target && "dataBinding" in target && target.dataBinding
      ? String(target.dataBinding.operationId || "").trim()
      : "";

  useEffect(() => {
    setLivePreview(null);
    setTestError(null);
    setTesting(false);
  }, [targetId, operationId]);

  if (!canEdit || !target || !("dataBinding" in target)) return null;

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
  const paramCount = Object.keys(paramSchema).length;
  const paramsNeedModal = isRibbon && paramCount > RIBBON_INLINE_PARAM_LIMIT;

  const refreshAsStr = binding.refreshSec == null ? "" : String(binding.refreshSec);
  const refreshSelectValue =
    binding.refreshSec == null ? "" : REFRESH_PRESET_VALUES.has(refreshAsStr) ? refreshAsStr : "__custom__";
  const showCustomRefresh = refreshCustom || refreshSelectValue === "__custom__";

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

  function applyRefreshSec(raw: string) {
    const nextBinding: ComunicadoDataBinding = { ...binding };
    if (!raw.trim()) {
      delete nextBinding.refreshSec;
    } else {
      const parsed = Number(raw);
      if (Number.isFinite(parsed)) {
        nextBinding.refreshSec = Math.min(
          DATA_REFRESH_SEC_MAX,
          Math.max(DATA_REFRESH_SEC_MIN, Math.round(parsed)),
        );
      }
    }
    applyPatch({ dataBinding: nextBinding } as Partial<ComunicadoBlock>);
  }

  async function handleTestRoute() {
    if (!route || !("dataBinding" in target)) return;
    setTesting(true);
    setTestError(null);
    try {
      const payload = await previewTvDataRoute({
        route,
        block: target as ComunicadoBlock & { dataBinding: ComunicadoDataBinding },
        config,
        playlistId,
        slideFilters,
      });
      if (payload.error) {
        setLivePreview(null);
        setTestError(payload.error);
      } else {
        setLivePreview(payload);
      }
    } catch (err) {
      setLivePreview(null);
      setTestError(err instanceof Error ? err.message : "Falha ao testar a rota.");
    } finally {
      setTesting(false);
    }
  }

  const testRouteControls = route ? (
    <div className="td-data-binding-test">
      <button
        type="button"
        className="td-btn td-btn--sm"
        disabled={testing}
        onClick={() => void handleTestRoute()}
      >
        <Play size={14} aria-hidden="true" />
        {testing ? "Testando…" : "Testar rota"}
      </button>
      {testError ? (
        <p className="delpi-ui-data-route-preview__error" role="alert">
          {testError}
        </p>
      ) : null}
      {livePreview && !livePreview.error ? <DataRouteSamplePreview payload={livePreview} /> : null}
    </div>
  ) : null;

  const connectionFields = (
    <>
      <p className="td-deck-inspector__meta" title={route?.label ?? binding.operationId}>
        {route?.label ?? binding.operationId}
      </p>
      {!isRibbon ? (
        <div className="td-deck-inspector__actions">
          {!editingLinkedSource ? (
            <button type="button" className="td-btn td-btn--sm" onClick={() => duplicateSelected()}>
              <Copy size={14} aria-hidden="true" />
              Duplicar
            </button>
          ) : null}
          {!editingLinkedSource ? (
            <button
              type="button"
              className="td-btn td-btn--sm"
              onClick={(event) => openDataCatalog("replace", { anchor: event.currentTarget })}
            >
              <RefreshCw size={14} aria-hidden="true" />
              Trocar rota
            </button>
          ) : null}
        </div>
      ) : !editingLinkedSource ? (
        <button
          type="button"
          className="td-btn td-btn--sm"
          onClick={(event) => openDataCatalog("replace", { anchor: event.currentTarget })}
        >
          <RefreshCw size={14} aria-hidden="true" />
          Trocar rota
        </button>
      ) : null}
      {testRouteControls}
      {showPresentationMode ? (
        <DeckField id="td-data-display-mode" label="Formato de apresentação">
          <FormSelectControl
            id="td-data-display-mode"
            className={compactSelect}
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
          className={compactNative}
          value={binding.label ?? ""}
          onChange={(value) =>
            applyPatch({
              dataBinding: { ...binding, label: value || undefined },
            } as Partial<ComunicadoBlock>)
          }
        />
      </DeckField>
      {valueFieldOptions.length > 0 ? (
        <p className="td-deck-inspector__hint">
          Campos disponíveis ({valueFieldOptions.length}): configure métricas, eixos e colunas no
          visual (KPI / gráfico / tabela), não na fonte.
        </p>
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
            className={compactNative}
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
        label="Atualizar na TV a cada (s)"
        hint={TV_DASHBOARD_HELP_TOOLTIPS.fields.dataBlockRefreshInterval}
      >
        {isRibbon ? (
          <>
            <FormSelectControl
              id="td-data-refresh"
              className={compactSelect}
              ariaLabel="Atualizar a cada (s)"
              value={showCustomRefresh ? "__custom__" : refreshSelectValue}
              onChange={(value) => {
                if (value === "__custom__") {
                  setRefreshCustom(true);
                  return;
                }
                setRefreshCustom(false);
                applyRefreshSec(value);
              }}
              options={[
                { value: "", label: `Padrão (${inheritedRefreshSec}s)` },
                { value: "60", label: "60s" },
                { value: "120", label: "120s" },
                { value: "300", label: "300s" },
                { value: "600", label: "600s" },
                { value: "__custom__", label: "Personalizado…" },
              ]}
            />
            {showCustomRefresh ? (
              <NativeTextControl
                id="td-data-refresh-custom"
                type="number"
                className={compactNative}
                min={DATA_REFRESH_SEC_MIN}
                max={DATA_REFRESH_SEC_MAX}
                placeholder={`${DATA_REFRESH_SEC_MIN}–${DATA_REFRESH_SEC_MAX}`}
                value={binding.refreshSec ?? ""}
                onChange={applyRefreshSec}
              />
            ) : null}
          </>
        ) : (
          <NativeTextControl
            id="td-data-refresh"
            type="number"
            min={DATA_REFRESH_SEC_MIN}
            max={DATA_REFRESH_SEC_MAX}
            placeholder={`Padrão (${inheritedRefreshSec}s)`}
            value={binding.refreshSec ?? ""}
            onChange={applyRefreshSec}
          />
        )}
      </DeckField>
      {isRibbon && onOpenCatalog ? (
        <button type="button" className="td-btn td-btn--sm td-btn--ghost" onClick={onOpenCatalog}>
          Inserir nova fonte…
        </button>
      ) : null}
    </>
  );

  const paramsModal = (
    <Modal
      open={paramsModalOpen}
      title="Parâmetros da fonte"
      onClose={() => setParamsModalOpen(false)}
    >
      <p className="td-deck-inspector__meta">{route?.label ?? binding.operationId}</p>
      <DataParamFields
        schema={paramSchema}
        values={blockParams}
        inheritedKeys={inheritedKeys}
        branchScope={branchScope}
        layout="pane"
        idPrefix="td-data-param-modal"
        onChange={updateParam}
      />
    </Modal>
  );

  if (isRibbon) {
    return (
      <>
        {activeSections.includes("connection") ? (
          <RibbonZone title="Conexão">
            <div className="td-deck-ribbon__field-grid">{connectionFields}</div>
          </RibbonZone>
        ) : null}
        {activeSections.includes("params") ? (
          <RibbonZone title="Parâmetros">
            {paramCount === 0 ? (
              <p className="td-deck-inspector__hint">Nenhum parâmetro editável nesta rota.</p>
            ) : paramsNeedModal ? (
              <button
                type="button"
                className="td-btn td-btn--sm"
                onClick={() => setParamsModalOpen(true)}
              >
                <SlidersHorizontal size={14} aria-hidden="true" />
                Parâmetros… ({paramCount})
              </button>
            ) : (
              paramFields
            )}
          </RibbonZone>
        ) : null}
        {activeSections.includes("refresh") ? (
          <RibbonZone title="Atualização">
            <p className="td-deck-inspector__hint">
              No editor o preview não atualiza sozinho — use «Atualizar visual». O intervalo abaixo vale só na TV.
            </p>
            <div className="td-deck-ribbon__field-grid">{refreshFields}</div>
          </RibbonZone>
        ) : null}
        {paramsNeedModal ? paramsModal : null}
      </>
    );
  }

  return (
    <>
      <DeckPropertySection
        pane={pane}
        title={editingLinkedSource ? "Parâmetros da fonte" : "Dados"}
        hint="Parâmetros deste bloco sobrescrevem filtros do slide. No editor o preview não autoatualiza — use «Atualizar visual»; o intervalo de refresh vale só na TV."
      >
        {connectionFields}
        {refreshFields}
        {paramFields}
      </DeckPropertySection>
    </>
  );
}
