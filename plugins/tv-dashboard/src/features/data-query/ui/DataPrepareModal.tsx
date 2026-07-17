import {
  isDataSourceBlockType,
  type ComunicadoDataSourceBlock,
} from "@delpi/tv-dashboard-presentation";
import { Code2 } from "lucide-react";
import { useMemo, useRef, useState, type MouseEvent } from "react";

import { useComunicadoEditor } from "../../../components/comunicadoEditorContext";
import { HostContainedModal } from "../../../components/ui/Modal";
import { dataQueryDependencyEdges } from "../domain/dataQueryDependencies";
import type { DataQueryInsertOperation } from "../domain/dataQueryTypes";
import {
  useDataQueryFunctions,
  useDataQueryWorkbench,
} from "../state/useDataQueryWorkbench";
import { DataPrepareAdvancedEditor } from "./DataPrepareAdvancedEditor";
import { DataPrepareAppliedSteps } from "./DataPrepareAppliedSteps";
import {
  DataPrepareColumnMenu,
  type ColumnMenuTarget,
} from "./DataPrepareColumnMenu";
import { DataPrepareDiagnostics } from "./DataPrepareDiagnostics";
import { DataPrepareFormulaBar } from "./DataPrepareFormulaBar";
import { DataPreparePreviewGrid } from "./DataPreparePreviewGrid";
import { DataPrepareQualityPanel } from "./DataPrepareQualityPanel";
import { DataPrepareQueryList } from "./DataPrepareQueryList";
import { DataPrepareRibbon } from "./DataPrepareRibbon";

export function DataQueryWorkbenchModal({
  open,
  onClose,
  initialSourceId = null,
  advancedEditorEnabled,
  profilingEnabled,
}: {
  open: boolean;
  onClose: () => void;
  initialSourceId?: string | null;
  advancedEditorEnabled: boolean;
  profilingEnabled: boolean;
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
  const [advancedEditorOpen, setAdvancedEditorOpen] = useState(false);
  const advancedEditorButtonRef = useRef<HTMLButtonElement>(null);
  const functionCatalog = useDataQueryFunctions(advancedEditorOpen && advancedEditorEnabled);
  const [columnMenu, setColumnMenu] = useState<ColumnMenuTarget | null>(null);
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
  const dependencyEdges = dataQueryDependencyEdges(
    Object.values(workbench.state.draftByQueryId),
  );

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
  const closeAdvancedEditor = () => {
    setAdvancedEditorOpen(false);
    requestAnimationFrame(() => advancedEditorButtonRef.current?.focus());
  };

  const openColumnMenu = (
    event: MouseEvent<HTMLElement>,
    column: string,
    cellValue?: unknown,
  ) => {
    event.preventDefault();
    const meta = preview?.columns.find((item) => item.key === column);
    const cellText =
      typeof cellValue === "string" ||
      typeof cellValue === "number" ||
      typeof cellValue === "boolean"
        ? String(cellValue)
        : null;
    setColumnMenu({
      position: { x: event.clientX, y: event.clientY },
      columnKey: column,
      columnLabel: meta?.label ?? column,
      columnType: meta?.type ?? "any",
      cellValue: cellText,
    });
    workbench.dispatch({ type: "select_column", columnKey: column });
  };

  const insertForColumn = (
    stepName: string,
    operation: DataQueryInsertOperation,
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
    <HostContainedModal
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
      <div
        className="td-data-pq"
        onContextMenu={(event) => {
          // Menu nativo só em campos de texto (colar); no resto, menus próprios.
          const target = event.target as HTMLElement;
          if (target.closest("input, textarea, [contenteditable='true']")) return;
          event.preventDefault();
        }}
      >
        <DataPrepareRibbon
          selectedColumnKey={workbench.state.selectedColumnKey}
          selectedStepName={draft?.selectedStepName ?? null}
          preview={preview}
          loading={workbench.state.preview.status === "loading"}
          availableQueries={Object.values(workbench.state.draftByQueryId)
            .filter((item) => item.sourceId !== draft?.sourceId)
            .map((item) => item.queryName)}
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
            onRename={async (name) => {
              setApplyError(null);
              try {
                await workbench.renameQuery(name);
              } catch (error) {
                setApplyError(
                  error instanceof Error ? error.message : "Não foi possível renomear.",
                );
              }
            }}
          />
          <main className="td-data-pq__main" aria-label="Prévia da consulta">
            <div className="td-data-pq__editor-launch">
              <button
                ref={advancedEditorButtonRef}
                type="button"
                className="td-btn td-btn--sm td-btn--ghost"
                disabled={!advancedEditorEnabled || !draft}
                onClick={() => setAdvancedEditorOpen(true)}
              >
                <Code2 size={16} aria-hidden />
                Editor avançado
              </button>
              {!advancedEditorEnabled ? (
                <span>Editor avançado indisponível pelas capabilities.</span>
              ) : null}
            </div>
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
            {advancedEditorOpen && draft ? (
              <DataPrepareAdvancedEditor
                open
                script={draft.script}
                compiled={compiled ?? workbench.state.compile.value}
                functions={functionCatalog.items}
                loadingFunctions={functionCatalog.loading}
                canUndo={draft.undoStack.length > 0}
                canRedo={draft.redoStack.length > 0}
                onChange={(script) =>
                  workbench.dispatch({ type: "edit_script", queryId: draft.sourceId, script })
                }
                onCompile={workbench.compileScript}
                onFormat={() => workbench.mutate({ type: "format_script" })}
                onUndo={() =>
                  workbench.dispatch({ type: "undo_script", queryId: draft.sourceId })
                }
                onRedo={() =>
                  workbench.dispatch({ type: "redo_script", queryId: draft.sourceId })
                }
                onClose={closeAdvancedEditor}
              />
            ) : (
              <>
                <DataPreparePreviewGrid
                  preview={preview}
                  loading={workbench.state.preview.status === "loading"}
                  selectedColumnKey={workbench.state.selectedColumnKey}
                  onSelectColumn={(columnKey) =>
                    workbench.dispatch({ type: "select_column", columnKey })
                  }
                  onColumnContextMenu={openColumnMenu}
                />
                {profilingEnabled || preview?.columnProfile || preview?.explainPlan ? (
                  <DataPrepareQualityPanel
                    preview={preview}
                    profilingEnabled={profilingEnabled}
                    profilingRequested={workbench.profilingRequested}
                    loading={workbench.state.preview.status === "loading"}
                    onToggleProfiling={workbench.setProfilingRequested}
                  />
                ) : null}
                <section className="td-data-pq__dependencies" aria-label="Dependências de consultas">
                  <strong>Dependências</strong>
                  {dependencyEdges.length === 0 ? (
                    <span>Nenhuma dependência entre consultas.</span>
                  ) : (
                    <ul>
                      {dependencyEdges.map((edge) => (
                        <li key={`${edge.sourceId}-${edge.targetName}`}>
                          {edge.sourceName} → {edge.targetName}
                        </li>
                      ))}
                    </ul>
                  )}
                </section>
              </>
            )}
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
            onRename={(stepName, newName) =>
              void workbench.mutate({ type: "rename_step", stepName, newName })
            }
          />
        </div>
        <DataPrepareColumnMenu
          target={columnMenu}
          onClose={() => setColumnMenu(null)}
          onInsert={insertForColumn}
        />
      </div>
    </HostContainedModal>
  );
}
