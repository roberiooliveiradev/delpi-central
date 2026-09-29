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

import { useParamExpressionCapability } from "../hooks/useParamExpressionCapability";
import {
  applyDataParamRawUpdates,
  type DataParamUpdateValue,
} from "../utils/applyDataParamUpdates";
import { previewTvDataRoute } from "../utils/previewTvDataRoute";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import {
  RIBBON_INLINE_PARAM_LIMIT,
  visibleParamSchema,
  type DataParamSchema,
} from "../utils/dataParamSchema";
import {
  DataParamFields,
  type DataParamExpressionEditRequest,
} from "./DataParamFields";
import { DataRefreshIntervalField } from "./DataRefreshIntervalField";
import { FieldLabelsEditor } from "./FieldLabelsEditor";
import type { PanelLayout } from "./SelectedDataSidePanel";
import { DeckField } from "./deck/DeckField";
import { DeckPropertySection } from "./deck/DeckPropertySection";
import { HostContainedDialog } from "./ui/Modal";
import type { ValueFieldOption } from "./ValueFieldsMultiSelect";

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

function RibbonZone({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="td-deck-ribbon__panel-zone">
      <h4 className="td-deck-ribbon__panel-zone-title">{title}</h4>
      {children}
    </div>
  );
}

/**
 * Diagnostics do backend — `resolved.paramExpressions` / `effectiveParams` do
 * preview-block. Mostra parâmetro → valor resolvido/erro. O AST editável
 * permanece nos params; aqui é só leitura do resultado do backend.
 */
function ParamExpressionTrace({ payload }: { payload: DataRoutePreviewPayload | null }) {
  const expr = payload?.paramExpressions ?? [];
  const effective = payload?.effectiveParams;
  const effectiveEntries = effective ? Object.entries(effective) : [];
  if (expr.length === 0 && effectiveEntries.length === 0) return null;

  const formatValue = (value: unknown): string => {
    if (value === null || value === undefined) return "—";
    if (typeof value === "object") {
      try {
        return JSON.stringify(value);
      } catch {
        return "—";
      }
    }
    return String(value);
  };

  return (
    <details className="td-param-expression-trace">
      <summary>Detalhes técnicos — expressões resolvidas</summary>
      {expr.length > 0 ? (
        <dl className="td-param-expression-trace__list">
          {expr.map((entry, index) => {
            const key = String(entry.param ?? `expressão ${index + 1}`);
            const errorRaw = entry.error;
            const error =
              errorRaw && typeof errorRaw === "object"
                ? String(
                    (errorRaw as { message?: unknown }).message ??
                      (errorRaw as { code?: unknown }).code ??
                      "erro",
                  )
                : null;
            const expected =
              typeof entry.expectedType === "string" ? entry.expectedType : null;
            return (
              <div key={`${key}-${index}`} className="td-param-expression-trace__row">
                <dt>
                  {key}
                  {expected ? <small> ({expected})</small> : null}
                </dt>
                <dd>
                  {error ? (
                    <span className="td-param-expression-trace__error" role="alert">
                      {error}
                    </span>
                  ) : (
                    <span className="td-param-expression-trace__value">
                      {formatValue(entry.resolved)}
                    </span>
                  )}
                </dd>
              </div>
            );
          })}
        </dl>
      ) : null}
      {effectiveEntries.length > 0 ? (
        <dl className="td-param-expression-trace__list">
          <div className="td-param-expression-trace__row td-param-expression-trace__row--head">
            <dt>Parâmetros efetivos</dt>
          </div>
          {effectiveEntries.map(([key, value]) => (
            <div key={key} className="td-param-expression-trace__row">
              <dt>{key}</dt>
              <dd>
                <span className="td-param-expression-trace__value">
                  {formatValue(value)}
                </span>
              </dd>
            </div>
          ))}
        </dl>
      ) : null}
    </details>
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
    playlistDefaults,
    openExpressionEditor,
  } = useComunicadoEditor();
  const [paramsModalOpen, setParamsModalOpen] = useState(false);
  const [testing, setTesting] = useState(false);
  const [livePreview, setLivePreview] = useState<DataRoutePreviewPayload | null>(null);
  const [testError, setTestError] = useState<string | null>(null);
  // Capability do catálogo vivo (`/data/m/functions`) — habilita o modo Expressão.
  const expressionSupport = useParamExpressionCapability();
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
  const targetResolved =
    "resolved" in target && target.resolved ? target.resolved : null;

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
  const showPresentationMode = isDataBlockType(target.type) && !isDataSourceBlockType(target.type);
  const paramSchema = visibleParamSchema(
    (route?.paramSchema ?? undefined) as DataParamSchema | undefined,
    route?.fixedQueryParams,
  );
  const paramCount = Object.keys(paramSchema).length;
  const paramsNeedModal = isRibbon && paramCount > RIBBON_INLINE_PARAM_LIMIT;

  function updateParams(updates: Record<string, DataParamUpdateValue>) {
    const nextParams = applyDataParamRawUpdates(binding.params, updates, paramSchema);
    applyPatch({
      dataBinding: { ...binding, params: nextParams },
    } as Partial<ComunicadoBlock>);
  }

  /** «Editar expressão» → drawer do editor (mesmo canal da ribbon/sidebar). */
  function handleEditExpression(request: DataParamExpressionEditRequest) {
    openExpressionEditor({ ...request, previewBlockId: targetId || null });
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

  async function handleTestRoute() {
    if (!route || !target || !("dataBinding" in target)) return;
    setTesting(true);
    setTestError(null);
    try {
      const payload = await previewTvDataRoute({
        route,
        block: target as ComunicadoBlock & { dataBinding: ComunicadoDataBinding },
        config,
        playlistId,
        playlistDefaults,
        slideFilters,
      });
      // Mantém o payload mesmo com erro — o trace (paramExpressions/effectiveParams)
      // do backend explica falhas de resolução de expressão.
      setLivePreview(payload);
      setTestError(payload.error ?? null);
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
      <ParamExpressionTrace payload={livePreview} />
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
          placeholder={route?.label ? String(route.label) : undefined}
          onChange={(value) =>
            applyPatch({
              dataBinding: { ...binding, label: value.trim() || undefined },
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
      openEndedDateRange={Boolean(route?.openEndedDateRange)}
      expressionSupport={expressionSupport}
      fixedQueryParams={route?.fixedQueryParams}
      resolved={targetResolved}
      onEditExpression={handleEditExpression}
      onChange={updateParams}
    />
  );

  const refreshFields = (
    <>
      <DataRefreshIntervalField
        refreshSec={binding.refreshSec}
        inheritedRefreshSec={inheritedRefreshSec}
        compact={isRibbon}
        onChange={(sec) => {
          const nextBinding: ComunicadoDataBinding = { ...binding };
          if (sec == null) delete nextBinding.refreshSec;
          else nextBinding.refreshSec = sec;
          applyPatch({ dataBinding: nextBinding } as Partial<ComunicadoBlock>);
        }}
      />
      {isRibbon && onOpenCatalog ? (
        <button type="button" className="td-btn td-btn--sm td-btn--ghost" onClick={onOpenCatalog}>
          Inserir nova fonte…
        </button>
      ) : null}
    </>
  );

  const paramsModal = (
    <HostContainedDialog
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
        openEndedDateRange={Boolean(route?.openEndedDateRange)}
        expressionSupport={expressionSupport}
        fixedQueryParams={route?.fixedQueryParams}
        resolved={targetResolved}
        onEditExpression={handleEditExpression}
        onChange={updateParams}
      />
    </HostContainedDialog>
  );

  const showFieldLabels = isDataSourceBlockType(target.type);
  const sourceResolved =
    "resolved" in target && target.resolved ? target.resolved : undefined;
  const catalogLabelFields = valueFieldOptions.map((item) => ({
    field: item.field,
    label: item.label,
  }));

  const fieldLabelsEditor = showFieldLabels ? (
    <FieldLabelsEditor
      resolved={sourceResolved}
      catalogFields={catalogLabelFields}
      fieldLabels={(target as import("@delpi/tv-dashboard-presentation").ComunicadoDataSourceBlock).fieldLabels}
      pane={pane}
      compact={isRibbon}
      onChange={(next) => applyPatch({ fieldLabels: next } as Partial<ComunicadoBlock>)}
    />
  ) : null;

  if (isRibbon) {
    return (
      <>
        {activeSections.includes("connection") ? (
          <RibbonZone title="Conexão">
            <div className="td-deck-ribbon__field-grid">{connectionFields}</div>
          </RibbonZone>
        ) : null}
        {fieldLabelsEditor}
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
              No editor o preview atualiza ao mudar parâmetros ou filtros. O intervalo abaixo vale só na TV.
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
        hint="Parâmetros deste bloco sobrescrevem filtros do slide. Alterações atualizam o palco automaticamente; o intervalo de refresh vale só na TV."
      >
        {connectionFields}
        {refreshFields}
        {paramFields}
      </DeckPropertySection>
      {fieldLabelsEditor}
    </>
  );
}
