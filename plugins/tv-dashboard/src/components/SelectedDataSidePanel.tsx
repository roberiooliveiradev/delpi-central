import { useEffect, useMemo, useRef, useState } from "react";
import {
  buildCanvasTableDataLinkPatch,
  buildTextDataLinkPatch,
  buildViewDataLinkPatch,
  isCanvasTableDataBoundBlockType,
  isDataSourceBlockType,
  isDataViewBlockType,
  isTextDataBoundBlockType,
  type ComunicadoBlock,
  type DataSourceLabelCatalog,
} from "@delpi/tv-dashboard-presentation";

import { listDataRoutes, type BranchScope, type TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import {
  buildLabelCatalogFromRoutes,
  hydrateComunicadoDataBindings,
} from "../utils/hydrateComunicadoDataBindings";
import type {
  DataCatalogMode,
  OpenDataCatalogOptions,
} from "./comunicadoEditorContextCore";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DataBindingInspector } from "./DataBindingInspector";
import { DataPreparePanel } from "./DataPreparePanel";
import { DataRoutesSidePanel } from "./DataRoutesSidePanel";
import {
  canLinkBlockToProjectDataSource,
  ProjectDataSourcesCatalogSection,
} from "./DataSourceLinkSection";
import {
  CanvasTableDataBindingInspector,
  canShowCanvasTableDataBindingInspector,
} from "./CanvasTableDataBindingInspector";
import { TextDataBindingInspector, canShowTextDataBindingInspector } from "./TextDataBindingInspector";
import { VisualDataViewInspector } from "./VisualDataViewInspector";
import { DeckPropertySection } from "./deck/DeckPropertySection";
import { resolveSelectedDataContext } from "../utils/selectedDataContext";

export type PanelLayout = "ribbon" | "pane";

type OpenCatalogFn = (mode?: DataCatalogMode, options?: OpenDataCatalogOptions) => void;

type Props = {
  branchScope?: BranchScope | null;
  onInserted?: () => void;
  onOpenCatalog?: OpenCatalogFn;
  /** ribbon = top bar compacta; pane = painel lateral com inspector completo. */
  layout?: PanelLayout;
};

/**
 * Conteúdo da aba Dados (side bar e ribbon):
 * - ribbon: só ações curtas (nunca inspector/onboarding — vazava sobre o filmstrip)
 * - pane: configuração da fonte / vínculo (texto, visual e data_source no mesmo fluxo)
 * - intent catalog → listagem; com fontes no slide, lista «Fontes neste slide» no topo
 */
export function SelectedDataSidePanel({
  branchScope = null,
  onInserted,
  onOpenCatalog,
  layout = "pane",
}: Props) {
  const {
    blocks,
    config,
    selected,
    selectedIds,
    dataPanelIntent,
    openDataCatalog,
    openDataPanel,
    setDataPanelIntent,
    updateSelected,
    updateBlocksAtomically,
    setDataFilters,
  } = useComunicadoEditor();
  const context = useMemo(
    () => resolveSelectedDataContext(blocks, selectedIds),
    [blocks, selectedIds],
  );
  const showCatalog = dataPanelIntent === "catalog" || context.kind === "none";
  const isRibbon = layout === "ribbon";
  const openCatalog = onOpenCatalog ?? openDataCatalog;

  const [routes, setRoutes] = useState<TvDataRouteCatalogItem[]>([]);
  const [hydrateHint, setHydrateHint] = useState<string | null>(null);
  const hydratedFpRef = useRef<string>("");
  const bindingTarget = context.bindingTarget;
  const primary = context.primary;
  const isView = primary ? isDataViewBlockType(primary.type) : false;
  const isTextBound = primary ? canShowTextDataBindingInspector(primary) : false;
  const isCanvasTableBound = primary
    ? canShowCanvasTableDataBindingInspector(primary)
    : false;

  useEffect(() => {
    void listDataRoutes()
      .then(setRoutes)
      .catch(() => setRoutes([]));
  }, []);

  const labelCatalog: DataSourceLabelCatalog = useMemo(
    () => buildLabelCatalogFromRoutes(routes),
    [routes],
  );

  useEffect(() => {
    if (routes.length === 0) return;
    const result = hydrateComunicadoDataBindings(config, routes);
    const fp = JSON.stringify({
      orphans: result.orphanOperationIds,
      stripped: result.strippedParamKeys,
      remapped: result.remappedParamKeys,
      cleared: result.clearedLabels,
      changed: result.changed,
    });
    if (fp === hydratedFpRef.current) return;
    hydratedFpRef.current = fp;
    if (!result.changed) {
      setHydrateHint(null);
      return;
    }
    updateBlocksAtomically(result.config.blocks ?? []);
    if (result.config.dataFilters !== config.dataFilters) {
      setDataFilters(result.config.dataFilters);
    }
    if (
      result.clearedLabels > 0 ||
      result.remappedParamKeys.length > 0 ||
      result.strippedParamKeys.length > 0
    ) {
      setHydrateHint("Parâmetros atualizados pelo catálogo");
    } else {
      setHydrateHint(null);
    }
  }, [routes, config, setDataFilters, updateBlocksAtomically]);

  const selectedRoute = useMemo(() => {
    if (!bindingTarget || !("dataBinding" in bindingTarget)) return null;
    return routes.find((route) => route.operationId === bindingTarget.dataBinding.operationId) ?? null;
  }, [bindingTarget, routes]);

  const orphanRoute =
    Boolean(bindingTarget && "dataBinding" in bindingTarget && bindingTarget.dataBinding.operationId) &&
    routes.length > 0 &&
    selectedRoute == null;

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
      });
      updateSelected(patch as Partial<ComunicadoBlock>);
      setDataPanelIntent("binding");
      return;
    }
    if (isTextDataBoundBlockType(primary.type)) {
      const patch = buildTextDataLinkPatch({
        dataSourceId: sourceId,
        resolved,
        existing: "textProjection" in primary ? primary.textProjection : undefined,
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

  /** Faixa superior: toolbar horizontal — inspector completo só no painel lateral. */
  if (isRibbon) {
    const unboundView = isView && !bindingTarget;
    const unboundText = (isTextBound || isCanvasTableBound) && !bindingTarget;
    const hint = showCatalog
      ? "Escolha uma fonte do slide ou uma rota nova no catálogo."
      : context.kind === "mixed"
        ? context.message
        : unboundView || unboundText
          ? "Sem fonte — conecte no painel ao lado (fontes do slide ou catálogo)."
          : bindingTarget
            ? "Fonte ligada — edite parâmetros e conexão no painel Dados."
            : "Configure os dados no painel ao lado.";

    return (
      <div className="td-deck-ribbon__panel td-deck-ribbon__panel--dados td-deck-ribbon__panel--dados-compact">
        <p className="td-deck-inspector__hint">{hint}</p>
        <div className="td-deck-ribbon__field-grid">
          <button
            type="button"
            className="td-btn td-btn--sm"
            onClick={(event) => openCatalog("insert", { anchor: event.currentTarget })}
          >
            Abrir catálogo de fontes
          </button>
          {!showCatalog && context.kind !== "none" ? (
            <button
              type="button"
              className="td-btn td-btn--sm td-btn--ghost"
              onClick={() => openDataPanel()}
            >
              {unboundView || unboundText ? "Conectar no painel" : "Abrir painel Dados"}
            </button>
          ) : null}
          {showCatalog && context.kind !== "none" ? (
            <button
              type="button"
              className="td-btn td-btn--sm td-btn--ghost"
              onClick={() => setDataPanelIntent("binding")}
            >
              Voltar à fonte atual
            </button>
          ) : null}
        </div>
      </div>
    );
  }

  if (showCatalog) {
    const canLink = canLinkBlockToProjectDataSource(selected);
    const activeSourceId =
      selected && "dataSourceId" in selected ? selected.dataSourceId?.trim() : undefined;
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
          <ProjectDataSourcesCatalogSection
            blocks={blocks}
            activeSourceId={activeSourceId}
            labelCatalog={labelCatalog}
            onPickSource={linkPrimaryToSource}
          />
        ) : null}
        <DataRoutesSidePanel
          layout={layout}
          branchScope={branchScope}
          onInserted={onInserted}
        />
      </div>
    );
  }

  if (context.kind === "mixed") {
    return (
      <DeckPropertySection pane title="Dados" defaultOpen>
        <p className="td-deck-inspector__hint">{context.message}</p>
        <button
          type="button"
          className="td-btn td-btn--sm td-btn--ghost"
          onClick={(event) => openCatalog("insert", { anchor: event.currentTarget })}
        >
          Inserir nova fonte
        </button>
      </DeckPropertySection>
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

      {isView ? (
        <VisualDataViewInspector
          pane
          route={selectedRoute}
          labelCatalog={labelCatalog}
          onOpenDataSources={() => openCatalog("insert")}
        />
      ) : null}

      {isTextBound && !isView ? (
        <TextDataBindingInspector
          pane
          route={selectedRoute}
          labelCatalog={labelCatalog}
          onOpenDataSources={() => openCatalog("insert")}
        />
      ) : null}

      {isCanvasTableBound && !isView ? (
        <CanvasTableDataBindingInspector
          pane
          route={selectedRoute}
          labelCatalog={labelCatalog}
          onOpenDataSources={() => openCatalog("insert")}
        />
      ) : null}

      {bindingTarget && "dataBinding" in bindingTarget ? (
        <DataBindingInspector
          route={selectedRoute}
          pane
          branchScope={branchScope}
          block={selected?.id !== bindingTarget.id ? bindingTarget : null}
        />
      ) : isView || isTextBound || isCanvasTableBound ? (
        <DeckPropertySection pane title="Parâmetros da fonte" defaultOpen>
          <p className="td-deck-inspector__hint">
            Conecte uma fonte acima para editar parâmetros da rota api-delpi.
          </p>
        </DeckPropertySection>
      ) : null}

      {bindingTarget?.type === "data_source" ? (
        <DataPreparePanel pane block={bindingTarget} />
      ) : null}

      {!isView && !isTextBound && !isCanvasTableBound && !bindingTarget ? (
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
