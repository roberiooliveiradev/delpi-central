import { useEffect, useMemo, useState } from "react";
import {
  bindingTargetId,
  buildCanvasTableDataLinkPatch,
  buildTextDataLinkPatch,
  buildViewDataLinkPatch,
  findDataModel,
  isCanvasTableDataBoundBlockType,
  isDataSourceBlockType,
  isDataViewBlockType,
  isTextDataBoundBlock,
  resolveDataBlockErrorText,
  staticLabelFromTextBoundBlock,
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";

import type { BranchScope } from "../api/tvDashboardApi";
import { useTvDataRouteLabelCatalog } from "../hooks/useTvDataRouteLabelCatalog";
import {
  commitHydrateBindingsApplyPlan,
  planHydrateBindingsApply,
} from "../utils/hydrateComunicadoDataBindings";
import { resolveRouteForDataBoundBlock } from "../utils/resolveDataBoundBlockRoute";
import type {
  DataCatalogMode,
  OpenDataCatalogOptions,
} from "./comunicadoEditorContextCore";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DataBindingInspector } from "./DataBindingInspector";
import { DataPreparePanel } from "./DataPreparePanel";
import { DataBuilderChatPanel } from "./DataBuilderChatPanel";
import {
  canLinkBlockToProjectDataSource,
  DataModelsCatalogSection,
  ProjectDataSourcesCatalogSection,
  type DataModelPreviewStatus,
} from "./DataSourceLinkSection";
import { DataModelInspector } from "./DataModelInspector";
import {
  CanvasTableDataBindingInspector,
  canShowCanvasTableDataBindingInspector,
} from "./CanvasTableDataBindingInspector";
import { InputBindingInspector } from "./InputBindingInspector";
import { TextDataBindingInspector, canShowTextDataBindingInspector } from "./TextDataBindingInspector";
import {
  EfficiencyPinInspector,
  canShowEfficiencyPinInspector,
} from "./EfficiencyPinInspector";
import { VisualDataViewInspector } from "./VisualDataViewInspector";
import { NumberFormatSection } from "./selectionSections/NumberFormatSection";
import { DeckPropertySection } from "./deck/DeckPropertySection";
import { MultiSourceDataParamsPanel } from "./MultiSourceDataParamsPanel";
import { resolveSelectedDataContext } from "../utils/selectedDataContext";

export type PanelLayout = "ribbon" | "pane";

type OpenCatalogFn = (mode?: DataCatalogMode, options?: OpenDataCatalogOptions) => void;

type Props = {
  branchScope?: BranchScope | null;
  onInserted?: () => void;
  onOpenCatalog?: OpenCatalogFn;
};

/**
 * Conteúdo da aba Dados do painel lateral:
 * - pane: configuração da fonte / vínculo (texto, visual e data_source no mesmo fluxo)
 * - intent catalog → listagem; com fontes no slide, lista «Fontes neste slide» no topo
 * (a faixa Dados usa grupos próprios em ComunicadoDataRibbon — não este painel)
 */
export function SelectedDataSidePanel({
  branchScope = null,
  onInserted,
  onOpenCatalog,
}: Props) {
  const {
    blocks,
    config,
    selected,
    selectedIds,
    dataPanelIntent,
    openDataCatalog,
    setDataPanelIntent,
    updateSelected,
    updateBlocksAtomically,
    setDataFilters,
    getDataPreviewResolved,
    refreshingSourceIds,
  } = useComunicadoEditor();
  const context = useMemo(
    () => resolveSelectedDataContext(blocks, selectedIds, config.dataModels),
    [blocks, selectedIds, config.dataModels],
  );
  const showCatalog = dataPanelIntent === "catalog" || context.kind === "none";
  const openCatalog = onOpenCatalog ?? openDataCatalog;

  const [hydrateHint, setHydrateHint] = useState<string | null>(null);
  const [inspectedModelId, setInspectedModelId] = useState<string | null>(null);
  const bindingTarget = context.bindingTarget;
  const bindingModel = context.bindingModel;
  const inspectedModel =
    inspectedModelId ? findDataModel(config, inspectedModelId) : null;
  const primary = context.primary;
  const isView = primary ? isDataViewBlockType(primary.type) : false;
  const isTextBound = primary ? canShowTextDataBindingInspector(primary) : false;
  const isEfficiencyPin = primary ? canShowEfficiencyPinInspector(primary) : false;
  const isCanvasTableBound = primary
    ? canShowCanvasTableDataBindingInspector(primary)
    : false;
  const isInputFilter = primary?.type === "input";

  const { routes, labelCatalog } = useTvDataRouteLabelCatalog();

  // Hydrate uma vez por fingerprint de bindings (não por tick de config).
  // Ribbon + painel lateral compartilham planHydrateBindingsApply (sessão).
  useEffect(() => {
    if (routes.length === 0) return;
    const plan = planHydrateBindingsApply(config, routes);
    if (!plan) {
      setHydrateHint(null);
      return;
    }
    if (plan.patches.length > 0) {
      updateBlocksAtomically(
        plan.patches.map((item) => ({
          blockId: item.blockId,
          patch: { dataBinding: item.dataBinding } as Partial<ComunicadoBlock>,
        })),
      );
    }
    if (plan.dataFiltersChanged) {
      setDataFilters(plan.dataFilters);
    }
    commitHydrateBindingsApplyPlan(plan);
    setHydrateHint(plan.hint ? "Parâmetros atualizados pelo catálogo" : null);
  }, [routes, config, setDataFilters, updateBlocksAtomically]);

  const selectedRoute = useMemo(
    () => resolveRouteForDataBoundBlock(bindingTarget, blocks, routes, config.dataModels),
    [bindingTarget, blocks, config.dataModels, routes],
  );

  const orphanRoute =
    Boolean(bindingTarget && "dataBinding" in bindingTarget && bindingTarget.dataBinding.operationId) &&
    routes.length > 0 &&
    selectedRoute == null;

  /** Status de preview por modelo — pronto/loading/erro (≠ vazio). */
  const modelStatusById = useMemo(() => {
    const map: Record<string, { status: DataModelPreviewStatus; message?: string }> = {};
    for (const model of config.dataModels ?? []) {
      if (refreshingSourceIds.includes(model.id)) {
        map[model.id] = { status: "loading" };
        continue;
      }
      const resolved = getDataPreviewResolved?.(model.id);
      const errorText = resolveDataBlockErrorText(resolved);
      if (errorText) {
        map[model.id] = { status: "error", message: errorText };
      } else if (resolved) {
        map[model.id] = { status: "ready" };
      } else {
        map[model.id] = { status: "idle" };
      }
    }
    return map;
  }, [config.dataModels, getDataPreviewResolved, refreshingSourceIds]);

  /** Vínculo a DataModel — write exclusivo: modelId + remove dataSourceId. */
  function linkPrimaryToModel(modelId: string) {
    if (!primary) return;
    const model = findDataModel(config, modelId);
    if (!model) return;
    const resolved = getDataPreviewResolved?.(modelId);
    if (isDataViewBlockType(primary.type)) {
      const patch = buildViewDataLinkPatch({
        viewType: primary.type,
        dataSourceId: "",
        modelId,
        resolved,
        currentFrame: primary.frame,
        existing: {
          kpiProjection: "kpiProjection" in primary ? primary.kpiProjection : undefined,
          chartProjection: "chartProjection" in primary ? primary.chartProjection : undefined,
          tableProjection: "tableProjection" in primary ? primary.tableProjection : undefined,
        },
        chartType: primary.type === "chart_view" ? primary.chartType : undefined,
      });
      updateSelected(patch as Partial<ComunicadoBlock>);
      setDataPanelIntent("binding");
      return;
    }
    if (isTextDataBoundBlock(primary)) {
      const patch = buildTextDataLinkPatch({
        dataSourceId: "",
        modelId,
        resolved,
        existing: primary.textProjection,
        staticContent: staticLabelFromTextBoundBlock(primary),
      });
      updateSelected(patch as Partial<ComunicadoBlock>);
      setDataPanelIntent("binding");
      return;
    }
    if (isCanvasTableDataBoundBlockType(primary.type) && primary.type === "canvas_table") {
      const patch = buildCanvasTableDataLinkPatch({
        dataSourceId: "",
        modelId,
        resolved,
        existingCells: primary.cells,
      });
      updateSelected(patch as Partial<ComunicadoBlock>);
      setDataPanelIntent("binding");
    }
  }

  function linkPrimaryToSource(sourceId: string) {
    if (!primary) return;
    const source = blocks.find(
      (block) => block.id === sourceId && isDataSourceBlockType(block.type),
    );
    if (!source) return;
    const resolved = "resolved" in source ? source.resolved : undefined;
    if (isDataViewBlockType(primary.type)) {
      const patch = buildViewDataLinkPatch({
        viewType: primary.type,
        dataSourceId: sourceId,
        resolved,
        fieldTypes: null,
        currentFrame: primary.frame,
        existing: {
          kpiProjection: "kpiProjection" in primary ? primary.kpiProjection : undefined,
          chartProjection: "chartProjection" in primary ? primary.chartProjection : undefined,
          tableProjection: "tableProjection" in primary ? primary.tableProjection : undefined,
        },
        chartType: primary.type === "chart_view" ? primary.chartType : undefined,
      });
      updateSelected(patch as Partial<ComunicadoBlock>);
      setDataPanelIntent("binding");
      return;
    }
    if (isTextDataBoundBlock(primary)) {
      const patch = buildTextDataLinkPatch({
        dataSourceId: sourceId,
        resolved,
        existing: primary.textProjection,
        staticContent: staticLabelFromTextBoundBlock(primary),
      });
      updateSelected(patch as Partial<ComunicadoBlock>);
      setDataPanelIntent("binding");
      return;
    }
    if (isCanvasTableDataBoundBlockType(primary.type) && primary.type === "canvas_table") {
      const patch = buildCanvasTableDataLinkPatch({
        dataSourceId: sourceId,
        resolved,
        existingCells: primary.cells,
      });
      updateSelected(patch as Partial<ComunicadoBlock>);
      setDataPanelIntent("binding");
    }
  }

  if (inspectedModel) {
    return (
      <div>
        <div className="td-data-routes-panel__toolbar">
          <button
            type="button"
            className="td-btn td-btn--sm td-btn--ghost"
            onClick={() => setInspectedModelId(null)}
          >
            Voltar
          </button>
        </div>
        <DataModelInspector pane model={inspectedModel} />
      </div>
    );
  }

  if (showCatalog) {
    const canLink = canLinkBlockToProjectDataSource(selected);
    const activeTargetId = selected ? bindingTargetId(selected) : undefined;
    const activeModelId = activeTargetId
      ? findDataModel(config, activeTargetId)?.id
      : undefined;
    const activeSourceId = activeModelId ? undefined : activeTargetId;
    return (
      <div>
        {context.kind !== "none" ? (
          <div className="td-data-routes-panel__toolbar">
            <button
              type="button"
              className="td-btn td-btn--sm td-btn--ghost"
              onClick={() => setDataPanelIntent("binding")}
            >
              Voltar à fonte atual
            </button>
          </div>
        ) : null}
        {canLink ? (
          <DataModelsCatalogSection
            dataModels={config.dataModels ?? []}
            activeModelId={activeModelId}
            statusById={modelStatusById}
            onPickModel={linkPrimaryToModel}
            onInspectModel={setInspectedModelId}
          />
        ) : null}
        {canLink ? (
          <ProjectDataSourcesCatalogSection
            blocks={blocks}
            activeSourceId={activeSourceId}
            labelCatalog={labelCatalog}
            onPickSource={linkPrimaryToSource}
          />
        ) : null}
        <DataBuilderChatPanel
          branchScope={branchScope}
          onInserted={onInserted}
        />
      </div>
    );
  }

  if (context.kind === "mixed") {
    return (
      <>
        <MultiSourceDataParamsPanel
          targets={context.bindingTargets}
          branchScope={branchScope}
        />
        <div className="td-deck-inspector__actions" style={{ padding: "8px 12px" }}>
          <button
            type="button"
            className="td-btn td-btn--sm td-btn--ghost"
            onClick={(event) => openCatalog("insert", { anchor: event.currentTarget })}
          >
            Inserir nova fonte…
          </button>
        </div>
      </>
    );
  }

  return (
    <>
      {hydrateHint ? <p className="td-deck-inspector__hint">{hydrateHint}</p> : null}
      {orphanRoute ? (
        <div className="td-deck-inspector__onboarding" role="alert">
          <p className="td-deck-inspector__hint">
            Fonte indisponível no catálogo — troque a rota para continuar salvando e exibindo dados.
          </p>
          <button
            type="button"
            className="td-btn td-btn--sm"
            onClick={(event) => openCatalog("replace", { anchor: event.currentTarget })}
          >
            Trocar rota
          </button>
        </div>
      ) : null}

      {context.kind === "homogeneous" && context.dataBlocks.length > 1 ? (
        <p className="td-deck-inspector__hint td-deck-inspector__hint--stage">
          {context.dataBlocks.length} elementos compartilham a mesma fonte — alterações aplicam-se à
          fonte ligada.
        </p>
      ) : null}

      {isInputFilter ? <InputBindingInspector pane /> : null}

      {isView ? (
        <VisualDataViewInspector
          pane
          route={selectedRoute}
          labelCatalog={labelCatalog}
          onOpenDataSources={() => openCatalog("insert")}
          mode="full"
        />
      ) : null}

      {isEfficiencyPin && !isView ? (
        <EfficiencyPinInspector
          pane
          onOpenDataSources={() => openCatalog("insert")}
        />
      ) : null}

      {isTextBound && !isView ? (
        <>
          <TextDataBindingInspector
            pane
            route={selectedRoute}
            labelCatalog={labelCatalog}
            onOpenDataSources={() => openCatalog("insert")}
          />
          <NumberFormatSection layout="pane" />
        </>
      ) : null}

      {isCanvasTableBound && !isView ? (
        <>
          <CanvasTableDataBindingInspector
            pane
            route={selectedRoute}
            labelCatalog={labelCatalog}
            onOpenDataSources={() => openCatalog("insert")}
          />
          <NumberFormatSection layout="pane" />
        </>
      ) : null}

      {bindingModel ? <DataModelInspector pane model={bindingModel} /> : null}

      {bindingTarget && "dataBinding" in bindingTarget ? (
        <DataBindingInspector
          route={selectedRoute}
          pane
          branchScope={branchScope}
          block={selected?.id !== bindingTarget.id ? bindingTarget : null}
        />
      ) : !bindingModel && (isView || isTextBound || isCanvasTableBound || isEfficiencyPin) ? (
        <DeckPropertySection pane title="Parâmetros da fonte" defaultOpen>
          <p className="td-deck-inspector__hint">
            Conecte uma fonte acima para editar parâmetros da rota api-delpi.
          </p>
        </DeckPropertySection>
      ) : null}

      {bindingTarget?.type === "data_source" ? (
        <DataPreparePanel pane block={bindingTarget} />
      ) : null}

      {!isView && !isTextBound && !isCanvasTableBound && !isEfficiencyPin && !isInputFilter && !bindingTarget && !bindingModel ? (
        <DeckPropertySection pane title="Dados" defaultOpen>
          <p className="td-deck-inspector__hint">Nenhuma configuração de dados disponível.</p>
        </DeckPropertySection>
      ) : null}

      <div className="td-deck-inspector__actions" style={{ padding: "8px 12px" }}>
        <button
          type="button"
          className="td-btn td-btn--sm td-btn--ghost"
          onClick={(event) => openCatalog("insert", { anchor: event.currentTarget })}
        >
          Inserir nova fonte…
        </button>
      </div>
    </>
  );
}

export type { ComunicadoBlock };
