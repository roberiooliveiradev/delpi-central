import { useEffect, useMemo, useState } from "react";
import {
  isDataViewBlockType,
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";

import { listDataRoutes, type BranchScope, type TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import type {
  DataCatalogMode,
  OpenDataCatalogOptions,
} from "./comunicadoEditorContextCore";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DataBindingInspector } from "./DataBindingInspector";
import { DataPreparePanel } from "./DataPreparePanel";
import { DataRoutesSidePanel } from "./DataRoutesSidePanel";
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
 * - pane: configuração da fonte / vínculo
 * - sem seleção de dados ou intent catálogo → listagem para inserir
 */
export function SelectedDataSidePanel({
  branchScope = null,
  onInserted,
  onOpenCatalog,
  layout = "pane",
}: Props) {
  const {
    blocks,
    selected,
    selectedIds,
    dataPanelIntent,
    openDataCatalog,
    openDataPanel,
    setDataPanelIntent,
  } = useComunicadoEditor();
  const context = useMemo(
    () => resolveSelectedDataContext(blocks, selectedIds),
    [blocks, selectedIds],
  );
  const showCatalog =
    dataPanelIntent === "catalog" || context.kind === "none";
  const isRibbon = layout === "ribbon";
  const openCatalog = onOpenCatalog ?? openDataCatalog;

  const [routes, setRoutes] = useState<TvDataRouteCatalogItem[]>([]);
  const bindingTarget = context.bindingTarget;

  useEffect(() => {
    if (isRibbon || showCatalog || !bindingTarget || !("dataBinding" in bindingTarget)) return;
    void listDataRoutes()
      .then(setRoutes)
      .catch(() => setRoutes([]));
  }, [isRibbon, showCatalog, bindingTarget]);

  const selectedRoute = useMemo(() => {
    if (!bindingTarget || !("dataBinding" in bindingTarget)) return null;
    return routes.find((route) => route.operationId === bindingTarget.dataBinding.operationId) ?? null;
  }, [bindingTarget, routes]);

  /** Faixa superior: toolbar horizontal — inspector completo só no painel lateral. */
  if (isRibbon) {
    const primary = context.primary;
    const isView = primary ? isDataViewBlockType(primary.type) : false;
    const unboundView = isView && !bindingTarget;
    const hint = showCatalog
      ? "Escolha uma fonte no catálogo para inserir no palco."
      : context.kind === "mixed"
        ? context.message
        : unboundView
          ? "KPI/gráfico sem fonte — conecte no painel ao lado ou abra o catálogo."
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
              {unboundView ? "Conectar no painel" : "Abrir painel Dados"}
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

  const primary = context.primary;
  const isView = primary ? isDataViewBlockType(primary.type) : false;

  return (
    <>
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
      ) : isView ? (
        <DeckPropertySection pane title="Parâmetros da fonte" defaultOpen>
          <p className="td-deck-inspector__hint">
            Conecte uma fonte acima para editar parâmetros da rota api-delpi.
          </p>
          <button
            type="button"
            className="td-btn td-btn--sm td-btn--ghost"
            onClick={(event) => openCatalog("insert", { anchor: event.currentTarget })}
          >
            Abrir catálogo de fontes
          </button>
        </DeckPropertySection>
      ) : null}

      {bindingTarget?.type === "data_source" ? (
        <DataPreparePanel pane block={bindingTarget} />
      ) : null}

      {!isView && !bindingTarget ? (
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
