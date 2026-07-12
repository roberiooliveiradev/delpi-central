import { useEffect, useMemo, useState } from "react";
import {
  isDataViewBlockType,
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";

import { listDataRoutes, type BranchScope, type TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DataBindingInspector } from "./DataBindingInspector";
import { DataRoutesSidePanel } from "./DataRoutesSidePanel";
import { VisualDataViewInspector } from "./VisualDataViewInspector";
import { DeckPropertySection } from "./deck/DeckPropertySection";
import { resolveSelectedDataContext } from "../utils/selectedDataContext";

export type PanelLayout = "ribbon" | "pane";

type Props = {
  branchScope?: BranchScope | null;
  onInserted?: () => void;
  onOpenCatalog?: () => void;
  /** ribbon = top bar full-width; pane = painel lateral. */
  layout?: PanelLayout;
};

/**
 * Conteúdo da aba Dados (side bar e ribbon):
 * - com elemento de dados selecionado → configuração da fonte / vínculo
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
  } = useComunicadoEditor();
  const context = useMemo(
    () => resolveSelectedDataContext(blocks, selectedIds),
    [blocks, selectedIds],
  );
  const showCatalog =
    dataPanelIntent === "catalog" || context.kind === "none";
  const isRibbon = layout === "ribbon";

  const [routes, setRoutes] = useState<TvDataRouteCatalogItem[]>([]);
  const bindingTarget = context.bindingTarget;

  useEffect(() => {
    if (showCatalog || !bindingTarget || !("dataBinding" in bindingTarget)) return;
    void listDataRoutes()
      .then(setRoutes)
      .catch(() => setRoutes([]));
  }, [showCatalog, bindingTarget]);

  const selectedRoute = useMemo(() => {
    if (!bindingTarget || !("dataBinding" in bindingTarget)) return null;
    return routes.find((route) => route.operationId === bindingTarget.dataBinding.operationId) ?? null;
  }, [bindingTarget, routes]);

  if (showCatalog) {
    return (
      <div className={isRibbon ? "td-deck-ribbon__panel td-deck-ribbon__panel--ribbon" : undefined}>
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
      <div className={isRibbon ? "td-deck-ribbon__panel td-deck-ribbon__panel--ribbon" : undefined}>
        <DeckPropertySection pane={!isRibbon} title="Dados" defaultOpen>
          <p className="td-deck-inspector__hint">{context.message}</p>
          <button
            type="button"
            className="td-btn td-btn--sm td-btn--ghost"
            onClick={() => (onOpenCatalog ?? openDataCatalog)()}
          >
            Inserir nova fonte
          </button>
        </DeckPropertySection>
      </div>
    );
  }

  const primary = context.primary;
  const isView = primary ? isDataViewBlockType(primary.type) : false;

  const body = (
    <>
      {context.kind === "homogeneous" && context.dataBlocks.length > 1 ? (
        <p className="td-deck-inspector__hint td-deck-inspector__hint--stage">
          {context.dataBlocks.length} elementos compartilham a mesma fonte — alterações aplicam-se à
          fonte ligada.
        </p>
      ) : null}

      {isView ? (
        <VisualDataViewInspector
          pane={!isRibbon}
          layout={layout}
          onOpenDataSources={() => (onOpenCatalog ?? openDataCatalog)()}
        />
      ) : null}

      {bindingTarget && "dataBinding" in bindingTarget ? (
        <DataBindingInspector
          route={selectedRoute}
          pane={!isRibbon}
          layout={layout}
          branchScope={branchScope}
          block={selected?.id !== bindingTarget.id ? bindingTarget : null}
        />
      ) : isView ? (
        <DeckPropertySection pane={!isRibbon} title="Parâmetros da fonte" defaultOpen>
          <p className="td-deck-inspector__hint">
            Conecte uma fonte acima para editar parâmetros da rota api-delpi.
          </p>
          <button
            type="button"
            className="td-btn td-btn--sm td-btn--ghost"
            onClick={() => (onOpenCatalog ?? openDataCatalog)()}
          >
            Abrir catálogo de fontes
          </button>
        </DeckPropertySection>
      ) : null}

      {!isView && !bindingTarget ? (
        <DeckPropertySection pane={!isRibbon} title="Dados" defaultOpen>
          <p className="td-deck-inspector__hint">Nenhuma configuração de dados disponível.</p>
        </DeckPropertySection>
      ) : null}

      <div className="td-deck-inspector__actions" style={isRibbon ? undefined : { padding: "8px 12px" }}>
        <button
          type="button"
          className="td-btn td-btn--sm td-btn--ghost"
          onClick={() => (onOpenCatalog ?? openDataCatalog)()}
        >
          Inserir nova fonte…
        </button>
      </div>
    </>
  );

  if (!isRibbon) return body;

  return <div className="td-deck-ribbon__panel td-deck-ribbon__panel--ribbon">{body}</div>;
}

export type { ComunicadoBlock };
