import {
  ContextMenu,
  ContextMenuDivider,
  ContextMenuItem,
  type FixedPanelPoint,
} from "@delpi/plugin-ui/index";
import {
  isDataSourceBlockType,
  type ComunicadoDataSourceBlock,
} from "@delpi/tv-dashboard-presentation";
import { ArrowDownAZ, ArrowDownZA, Columns3, Trash2 } from "lucide-react";
import { useMemo, useState, type MouseEvent } from "react";

import { useComunicadoEditor } from "../../../components/comunicadoEditorContext";
import { Modal } from "../../../components/ui/Modal";
import { useDataQueryWorkbench } from "../state/useDataQueryWorkbench";
import { DataPrepareAppliedSteps } from "./DataPrepareAppliedSteps";
import { DataPrepareDiagnostics } from "./DataPrepareDiagnostics";
import { DataPrepareFormulaBar } from "./DataPrepareFormulaBar";
import { DataPreparePreviewGrid } from "./DataPreparePreviewGrid";
import { DataPrepareQueryList } from "./DataPrepareQueryList";
import { DataPrepareRibbon } from "./DataPrepareRibbon";

export function DataQueryWorkbenchModal({
  open,
  onClose,
  initialSourceId = null,
}: {
  open: boolean;
  onClose: () => void;
  initialSourceId?: string | null;
}) {
  const {
    blocks,
    config,
    playlistId,
    updateBlocksAtomically,
    refreshDataPreview,
  } = useComunicadoEditor();
  const queries = useMemo(
    () =>
      blocks.filter((block): block is ComunicadoDataSourceBlock =>
        isDataSourceBlockType(block.type),
      ),
    [blocks],
  );
  const workbench = useDataQueryWorkbench({
    open,
    queries,
    config,
    playlistId,
    initialSourceId,
  });
  const [applyError, setApplyError] = useState<string | null>(null);
  const [columnMenu, setColumnMenu] = useState<{
    position: FixedPanelPoint;
    column: string;
  } | null>(null);
  const draft = workbench.activeDraft;
  const compiled = draft?.compiled;
  const selectedStep = compiled?.steps.find(
    (step) => step.name === draft?.selectedStepName,
  );
  const preview = workbench.state.preview.value;
  const diagnostics = [
    ...(compiled?.diagnostics ?? []),
    ...(preview?.diagnostics ?? []),
  ];
  const dirtyCount = Object.values(workbench.state.draftByQueryId).filter(
    (item) => item.dirty,
  ).length;

  const apply = async () => {
    setApplyError(null);
    try {
      const changedIds = await workbench.apply(updateBlocksAtomically);
      if (changedIds.length > 0) {
        await refreshDataPreview({ force: true, blockIds: changedIds });
      }
      onClose();
    } catch (error) {
      setApplyError(error instanceof Error ? error.message : "Não foi possível aplicar.");
    }
  };

  const openColumnMenu = (event: MouseEvent<HTMLElement>, column: string) => {
    event.preventDefault();
    setColumnMenu({ position: { x: event.clientX, y: event.clientY }, column });
    workbench.dispatch({ type: "select_column", columnKey: column });
  };

  const insertForColumn = (
    stepName: string,
    operation: string,
    arguments_: Record<string, unknown>,
  ) => {
    void workbench.mutate({
      type: "insert_step",
      afterStepName: draft?.selectedStepName,
      stepName,
      operation,
      arguments: arguments_,
    });
    setColumnMenu(null);
  };

  return (
    <Modal
      open={open}
      title="Preparar dados — M DELPI"
      onClose={onClose}
      className="td-modal--data-prepare"
      footer={
        <div className="td-data-pq__footer">
          <span role="status">
            {dirtyCount > 0 ? `${dirtyCount} consulta(s) alterada(s)` : "Sem alterações"}
          </span>
          <button type="button" className="td-btn td-btn--sm td-btn--ghost" onClick={onClose}>
            Cancelar
          </button>
          <button
            type="button"
            className="td-btn td-btn--sm"
            disabled={
              workbench.state.compile.status === "loading" ||
              diagnostics.some((item) => item.severity === "error")
            }
            onClick={() => void apply()}
          >
            Fechar e aplicar
          </button>
        </div>
      }
    >
      <div className="td-data-pq">
        <DataPrepareRibbon
          selectedColumnKey={workbench.state.selectedColumnKey}
          selectedStepName={draft?.selectedStepName ?? null}
          preview={preview}
          loading={workbench.state.preview.status === "loading"}
          onRefresh={() => void workbench.preview(true)}
          onMutate={(action) => void workbench.mutate(action)}
        />
        <div className="td-data-pq__workspace">
          <DataPrepareQueryList
            drafts={Object.values(workbench.state.draftByQueryId)}
            activeQueryId={workbench.state.activeQueryId}
            onSelect={(queryId) =>
              workbench.dispatch({ type: "select_query", queryId })
            }
          />
          <main className="td-data-pq__main" aria-label="Prévia da consulta">
            <DataPrepareFormulaBar
              stepName={draft?.selectedStepName ?? null}
              formula={selectedStep?.formula ?? ""}
              diagnostics={diagnostics}
              onApply={(expression) =>
                draft?.selectedStepName
                  ? workbench.mutate({
                      type: "replace_step_expression",
                      stepName: draft.selectedStepName,
                      expression,
                    })
                  : undefined
              }
            />
            <DataPrepareDiagnostics diagnostics={diagnostics} />
            {applyError || workbench.state.preview.error || workbench.state.compile.error ? (
              <p className="td-deck-inspector__hint" role="alert">
                {applyError || workbench.state.preview.error || workbench.state.compile.error}
              </p>
            ) : null}
            <DataPreparePreviewGrid
              preview={preview}
              loading={workbench.state.preview.status === "loading"}
              selectedColumnKey={workbench.state.selectedColumnKey}
              onSelectColumn={(columnKey) =>
                workbench.dispatch({ type: "select_column", columnKey })
              }
              onColumnContextMenu={openColumnMenu}
            />
          </main>
          <DataPrepareAppliedSteps
            steps={compiled?.steps ?? []}
            selectedStepName={draft?.selectedStepName ?? null}
            onSelect={workbench.selectStep}
            onMove={(stepName, targetIndex) =>
              void workbench.mutate({ type: "move_step", stepName, targetIndex })
            }
            onRemove={(stepName) =>
              void workbench.mutate({ type: "remove_step", stepName })
            }
          />
        </div>
        <ContextMenu
          open={Boolean(columnMenu)}
          position={columnMenu?.position ?? null}
          onClose={() => setColumnMenu(null)}
          aria-label="Ações da coluna"
        >
          <ContextMenuItem
            label="Ordenar crescente"
            icon={ArrowDownAZ}
            onSelect={() =>
              columnMenu &&
              insertForColumn("Linhas ordenadas", "sort", {
                column: columnMenu.column,
                direction: "asc",
              })
            }
          />
          <ContextMenuItem
            label="Ordenar decrescente"
            icon={ArrowDownZA}
            onSelect={() =>
              columnMenu &&
              insertForColumn("Linhas ordenadas", "sort", {
                column: columnMenu.column,
                direction: "desc",
              })
            }
          />
          <ContextMenuItem
            label="Manter somente esta coluna"
            icon={Columns3}
            onSelect={() =>
              columnMenu &&
              insertForColumn("Colunas selecionadas", "select", {
                columns: [columnMenu.column],
              })
            }
          />
          <ContextMenuDivider />
          <ContextMenuItem
            label="Remover coluna"
            icon={Trash2}
            destructive
            onSelect={() =>
              columnMenu &&
              insertForColumn("Colunas removidas", "remove_columns", {
                remainingColumns: (preview?.columns ?? [])
                  .map((item) => item.key)
                  .filter((key) => key !== columnMenu.column),
              })
            }
          />
        </ContextMenu>
      </div>
    </Modal>
  );
}
