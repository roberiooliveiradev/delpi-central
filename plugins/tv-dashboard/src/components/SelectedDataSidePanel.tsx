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

type Props = {
  branchScope?: BranchScope | null;
  onInserted?: () => void;
  onOpenCatalog?: () => void;
};

/**
 * Conteúdo da aba lateral Dados:
 * - com elemento de dados selecionado → configuração da fonte / vínculo
 * - sem seleção de dados ou intent catálogo → listagem para inserir
 */
export function SelectedDataSidePanel({
  branchScope = null,
  onInserted,
  onOpenCatalog,
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
    return <DataRoutesSidePanel branchScope={branchScope} onInserted={onInserted} />;
  }

  if (context.kind === "mixed") {
    return (
      <DeckPropertySection pane title="Dados" defaultOpen>
        <p className="td-deck-inspector__hint">{context.message}</p>
        <button
          type="button"
          className="td-btn td-btn--sm td-btn--ghost"
          onClick={() => (onOpenCatalog ?? openDataCatalog)()}
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
          onOpenDataSources={() => (onOpenCatalog ?? openDataCatalog)()}
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
            onClick={() => (onOpenCatalog ?? openDataCatalog)()}
          >
            Abrir catálogo de fontes
          </button>
        </DeckPropertySection>
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
          onClick={() => (onOpenCatalog ?? openDataCatalog)()}
        >
          Inserir nova fonte…
        </button>
      </div>
    </>
  );
}

export type { ComunicadoBlock };
