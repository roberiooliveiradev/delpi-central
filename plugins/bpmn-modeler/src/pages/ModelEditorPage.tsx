import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  archiveModel,
  BpmnModelerApiError,
  createRevision,
  getModel,
  getWorkingCopy,
  listRevisions,
  restoreRevision,
  saveWorkingCopy,
  unarchiveModel,
  validateWorkingCopy,
  type ModelSummary,
  type RevisionSummary,
  type ValidationReport,
} from "../data/api/bpmnModelerApi";
import { BpmnEditorAdapter, type DiagramRef, type ElementSummary } from "../editor/BpmnEditorAdapter";
import { ElementInspector } from "../editor/inspector/ElementInspector";
import { buildElkGraph } from "../layout/elkGraph";
import { runLayout, type LayoutJob } from "../layout/layoutEngine";
import { buildDiXml, hasBpmnDi, injectDiIntoXml, planeElementFor, snapshotFromXml } from "../layout/diProposal";
import { capabilitiesFromPermissions, editableMode, type Capabilities, type ReadOnlyReason } from "../state/capabilities";
import { SaveMachine, type SaveState } from "../state/saveMachine";
import { ConflictDialog } from "../components/ConflictDialog";
import { DiagramSelector } from "../components/DiagramSelector";
import { ExportMenu } from "../components/ExportMenu";
import { ReadOnlyBanner } from "../components/ReadOnlyBanner";
import { SaveStatus } from "../components/SaveStatus";
import { UnsavedChangesDialog } from "../components/UnsavedChangesDialog";
import { ValidationPanel } from "../components/ValidationPanel";
import { RevisionHistoryList } from "../components/RevisionHistoryList";

type Props = {
  modelId: string;
  getAccessToken?: () => string | undefined;
  permissions?: string[];
  navigate: (path: string) => void;
};

type SideTab = "properties" | "validation" | "history";

function detectMustUnderstand(xml: string): boolean {
  try {
    const doc = new DOMParser().parseFromString(xml, "application/xml");
    for (const el of Array.from(doc.querySelectorAll("*"))) {
      for (const attr of Array.from(el.attributes)) {
        if (attr.localName === "mustUnderstand" && attr.value === "true") {
          return true;
        }
      }
    }
  } catch {
    return false;
  }
  return false;
}

export function ModelEditorPage({ modelId, getAccessToken, permissions, navigate }: Props) {
  const capabilities: Capabilities = useMemo(
    () => capabilitiesFromPermissions(permissions),
    [permissions],
  );

  const canvasRef = useRef<HTMLDivElement>(null);
  const adapterRef = useRef<BpmnEditorAdapter | null>(null);
  const machineRef = useRef(new SaveMachine());
  const layoutJobRef = useRef<LayoutJob | null>(null);

  const [machineState, setMachineState] = useState<SaveState>("LOADING");
  const [model, setModel] = useState<ModelSummary | null>(null);
  const [version, setVersion] = useState(1);
  const [readOnlyReason, setReadOnlyReason] = useState<ReadOnlyReason>(null);
  const [pageError, setPageError] = useState<string | null>(null);
  const [sideTab, setSideTab] = useState<SideTab>("properties");
  const [report, setReport] = useState<ValidationReport | null>(null);
  const [revisions, setRevisions] = useState<RevisionSummary[]>([]);
  const [revisionsLoading, setRevisionsLoading] = useState(false);
  const [diagrams, setDiagrams] = useState<DiagramRef[]>([]);
  const [selection, setSelection] = useState<ElementSummary | null>(null);
  const [unsavedOpen, setUnsavedOpen] = useState<(() => void) | null>(null);
  const [layoutBusy, setLayoutBusy] = useState(false);
  const [isTablet, setIsTablet] = useState(false);
  const [adapterInstance, setAdapterInstance] = useState<BpmnEditorAdapter | null>(null);

  const setState = useCallback((s: SaveState) => setMachineState(s), []);

  const isEditable =
    editableMode(capabilities, !!model?.archived_at, readOnlyReason) && !isTablet;

  // ---------- load ----------
  const loadModel = useCallback(async () => {
    setState("LOADING");
    setPageError(null);
    try {
      const [{ model: meta, version: v }, wc] = await Promise.all([
        getModel(modelId, { getAccessToken }),
        getWorkingCopy(modelId, { getAccessToken }),
      ]);
      setModel(meta);
      setVersion(v);

      let reason: ReadOnlyReason = null;
      if (meta.archived_at) reason = "ARCHIVED";
      else if (detectMustUnderstand(wc.xml)) reason = "UNSUPPORTED_MUST_UNDERSTAND";
      else if (!capabilities.edit) reason = "NO_EDIT_PERMISSION";
      setReadOnlyReason(reason);

      const adapter = new BpmnEditorAdapter();
      adapterRef.current = adapter;
      setAdapterInstance(adapter);
      adapter.subscribe({
        onChanged: (trigger) => {
          const m = machineRef.current;
          m.dispatch({ type: "COMMAND", trigger });
          setState(m.state);
        },
        onSelectionChanged: (ids) => {
          setSelection(ids[0] ? adapter.getElementSummary(ids[0]) : null);
        },
        onImportDone: (result) => {
          if (!result.ok) {
            setReadOnlyReason("EDITOR_CAPABILITY_FAILURE");
          }
        },
      });

      const editable = capabilities.edit && !meta.archived_at && reason === null && !isTablet;
      adapter.mount(canvasRef.current!, editable ? "edit" : "viewer");

      let xml = wc.xml;
      // Sem DI → layout transitório calculado e injetado antes do import (P5 §15).
      if (!hasBpmnDi(xml)) {
        try {
          const snapshot = snapshotFromXml(xml);
          const graph = buildElkGraph(snapshot);
          const job = runLayout(graph);
          const outcome = await job.promise;
          if (outcome.ok) {
            const planeElement = planeElementFor(xml);
            if (planeElement) {
              xml = injectDiIntoXml(xml, buildDiXml(outcome.graph, snapshot, planeElement));
            }
          }
        } catch {
          // sem DI e sem layout → import direto; vendor mostra o que conseguir
        }
      }

      const imported = await adapter.importXml(xml);
      setDiagrams(adapter.listDiagrams());
      const m = machineRef.current;
      if (imported.ok) {
        m.dispatch({ type: "LOAD_OK", editable });
      } else {
        m.dispatch({ type: "LOAD_OK", editable: false });
        setReadOnlyReason("EDITOR_CAPABILITY_FAILURE");
      }
      setState(m.state);
    } catch (err) {
      setPageError(
        err instanceof BpmnModelerApiError ? err.message : "Falha ao carregar o modelo.",
      );
    }
  }, [modelId, getAccessToken, capabilities.edit, isTablet, setState]);

  useEffect(() => {
    void Promise.resolve().then(loadModel);
    return () => {
      layoutJobRef.current?.cancel();
      adapterRef.current?.destroy();
      adapterRef.current = null;
    };
  }, [loadModel]);

  // tablet read-only (P4 §59 — tablet somente leitura)
  useEffect(() => {
    const coarse = window.matchMedia("(pointer: coarse)");
    const apply = () => setIsTablet(coarse.matches && window.innerWidth < 1280);
    apply();
    coarse.addEventListener("change", apply);
    return () => coarse.removeEventListener("change", apply);
  }, []);

  // beforeunload enquanto DIRTY (P4 §16)
  useEffect(() => {
    if (machineState !== "DIRTY" && machineState !== "SAVE_FAILED") return;
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault();
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [machineState]);

  // ---------- save ----------
  const save = async (): Promise<boolean> => {
    const adapter = adapterRef.current;
    const m = machineRef.current;
    if (!adapter || !m.canSave()) return false;
    m.dispatch({ type: "SAVE_REQUEST" });
    setState(m.state);
    try {
      const candidate = await adapter.exportXml();
      const outcome = await saveWorkingCopy(modelId, candidate, version, {
        getAccessToken,
      });
      // authoritative read-back (P4 §9): nunca confiar no eco do request
      const readBack = await getWorkingCopy(modelId, { getAccessToken });
      if (readBack.xml !== candidate) {
        setPageError("Não foi possível confirmar a gravação. Recarregue o estado autoritativo.");
        m.dispatch({ type: "SAVE_FAILED" });
        setState(m.state);
        return false;
      }
      setVersion(outcome.version);
      m.dispatch({ type: "SAVE_VERIFIED" });
      setState(m.state);
      return true;
    } catch (err) {
      if (err instanceof BpmnModelerApiError) {
        if (err.code === "VALIDATION_BLOCKED") {
          const details = err.details as { validation_report?: ValidationReport };
          if (details.validation_report) setReport(details.validation_report);
          setSideTab("validation");
          m.dispatch({ type: "VALIDATION_BLOCKED" });
        } else if (err.code === "CONFLICT") {
          m.dispatch({ type: "VERSION_CONFLICT" });
        } else {
          m.dispatch({ type: "SAVE_FAILED" });
        }
      } else {
        m.dispatch({ type: "SAVE_FAILED" });
      }
      setState(m.state);
      return false;
    }
  };

  // Ctrl/Cmd+S
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") {
        e.preventDefault();
        void save();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [machineState, version]);

  // ---------- revisions ----------
  const loadRevisions = useCallback(async () => {
    setRevisionsLoading(true);
    try {
      const page = await listRevisions(modelId, { getAccessToken });
      setRevisions(page.items);
    } catch {
      setRevisions([]);
    } finally {
      setRevisionsLoading(false);
    }
  }, [modelId, getAccessToken]);

  useEffect(() => {
    if (sideTab === "history") void Promise.resolve().then(loadRevisions);
  }, [sideTab, loadRevisions]);

  const onCreateRevision = async () => {
    try {
      await createRevision(modelId, version, { getAccessToken });
      const { version: v } = await getModel(modelId, { getAccessToken });
      setVersion(v);
      void loadRevisions();
    } catch (err) {
      setPageError(err instanceof BpmnModelerApiError ? err.message : "Falha ao criar revisão.");
    }
  };

  const onRestore = async (revisionNumber: number) => {
    if (!window.confirm(`Restaurar a revisão ${revisionNumber}? O working copy atual será substituído.`)) return;
    try {
      await restoreRevision(modelId, revisionNumber, version, { getAccessToken });
      // replace model = destroy + mount + importXml (P4 §10)
      await loadModel();
    } catch (err) {
      setPageError(err instanceof BpmnModelerApiError ? err.message : "Falha ao restaurar.");
    }
  };

  // ---------- archive toggle ----------
  const onArchiveToggle = async () => {
    if (!model) return;
    try {
      const outcome = model.archived_at
        ? await unarchiveModel(modelId, version, { getAccessToken })
        : await archiveModel(modelId, version, { getAccessToken });
      setVersion(outcome.version);
      await loadModel();
    } catch (err) {
      setPageError(err instanceof BpmnModelerApiError ? err.message : "Falha ao alterar arquivamento.");
    }
  };

  // ---------- validate on demand ----------
  const onValidate = async () => {
    const adapter = adapterRef.current;
    if (!adapter) return;
    try {
      const candidate = await adapter.exportXml();
      const result = await validateWorkingCopy(modelId, candidate, { getAccessToken });
      setReport(result);
      setSideTab("validation");
    } catch (err) {
      setPageError(err instanceof Error ? err.message : "Falha ao validar.");
    }
  };

  // ---------- auto-layout (preview → accept/cancel) ----------
  const onOrganize = async () => {
    const adapter = adapterRef.current;
    if (!adapter) return;
    setLayoutBusy(true);
    try {
      const xml = await adapter.exportXml();
      const snapshot = snapshotFromXml(xml);
      const graph = buildElkGraph(snapshot);
      const job = runLayout(graph);
      layoutJobRef.current = job;
      const outcome = await job.promise;
      if (outcome.ok) {
        const planeElement = planeElementFor(xml);
        if (planeElement) {
          const withDi = injectDiIntoXml(xml, buildDiXml(outcome.graph, snapshot, planeElement));
          // accept: reimport do artefato layoutado (commands → dirty via reload)
          await adapter.destroy();
          adapter.mount(canvasRef.current!, "edit");
          adapter.subscribe({
            onChanged: (trigger) => {
              const m = machineRef.current;
              m.dispatch({ type: "COMMAND", trigger });
              setState(m.state);
            },
            onSelectionChanged: (ids) => {
              setSelection(ids[0] ? adapter.getElementSummary(ids[0]) : null);
            },
          });
          const res = await adapter.importXml(withDi);
          if (res.ok) {
            const m = machineRef.current;
            m.dispatch({ type: "COMMAND", trigger: "execute" });
            setState(m.state);
          }
        }
      }
    } finally {
      layoutJobRef.current = null;
      setLayoutBusy(false);
    }
  };

  // ---------- navigation guard ----------
  const guardedNavigate = (path: string) => {
    const m = machineRef.current;
    if (m.dirty() || m.state === "SAVE_FAILED") {
      setUnsavedOpen(() => () => {
        setUnsavedOpen(null);
        navigate(path);
      });
    } else {
      navigate(path);
    }
  };

  if (pageError && machineState === "LOADING") {
    return (
      <div className="bpmnm-page">
        <div className="bpmnm-error" role="alert">
          {pageError}{" "}
          <button type="button" className="bpmnm-btn" onClick={() => void loadModel()}>
            Tentar novamente
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bpmnm-page bpmnm-editor">
      <header className="bpmnm-editor__header">
        <button
          type="button"
          className="bpmnm-btn bpmnm-btn--ghost"
          onClick={() => guardedNavigate("/apps/bpmn-modeler")}
        >
          ← Biblioteca
        </button>
        <h1 className="bpmnm-editor__title">
          {model?.display_name ?? "…"}
          {model?.archived_at ? <span className="bpmnm-badge">Arquivado</span> : null}
        </h1>
        <SaveStatus state={machineState} />
        <div className="bpmnm-editor__actions">
          <DiagramSelector
            diagrams={diagrams}
            activeId={diagrams[0]?.id ?? null}
            onSelect={(id) => adapterRef.current?.openDiagram(id)}
          />
          {isEditable && (
            <>
              <button type="button" className="bpmnm-btn" disabled={machineState !== "DIRTY" && machineState !== "CLEAN"} onClick={() => adapterRef.current?.undo()}>
                Desfazer
              </button>
              <button type="button" className="bpmnm-btn" disabled={machineState !== "DIRTY" && machineState !== "CLEAN"} onClick={() => adapterRef.current?.redo()}>
                Refazer
              </button>
              <button
                type="button"
                className="bpmnm-btn"
                disabled={layoutBusy}
                onClick={() => void onOrganize()}
              >
                {layoutBusy ? "Calculando layout…" : "Organizar layout"}
              </button>
              {layoutBusy && (
                <button type="button" className="bpmnm-btn" onClick={() => layoutJobRef.current?.cancel()}>
                  Cancelar
                </button>
              )}
              <button
                type="button"
                className="bpmnm-btn"
                onClick={() => void onValidate()}
              >
                Validar
              </button>
              <button
                type="button"
                className="bpmnm-btn bpmnm-btn--primary"
                disabled={machineState !== "DIRTY" && machineState !== "SAVE_FAILED"}
                onClick={() => void save()}
              >
                Salvar
              </button>
            </>
          )}
          <button type="button" className="bpmnm-btn" onClick={() => adapterRef.current?.zoomIn()} aria-label="Ampliar">+</button>
          <button type="button" className="bpmnm-btn" onClick={() => adapterRef.current?.zoomOut()} aria-label="Reduzir">−</button>
          <button type="button" className="bpmnm-btn" onClick={() => adapterRef.current?.fitViewport()}>
            Ajustar
          </button>
          {capabilities.manage && model && (
            <button type="button" className="bpmnm-btn" onClick={() => void onArchiveToggle()}>
              {model.archived_at ? "Desarquivar" : "Arquivar"}
            </button>
          )}
          <ExportMenu modelId={modelId} adapter={adapterInstance} getAccessToken={getAccessToken} />
        </div>
      </header>

      <ReadOnlyBanner reason={isTablet && isEditable === false && capabilities.edit ? null : readOnlyReason} />
      {isTablet && capabilities.edit && !readOnlyReason ? (
        <div className="bpmnm-banner bpmnm-banner--readonly" role="note">
          Em tablets o editor opera em modo somente leitura.
        </div>
      ) : null}
      {pageError ? <div className="bpmnm-error" role="alert">{pageError}</div> : null}

      <div className="bpmnm-editor__body">
        <div
          ref={canvasRef}
          className="bpmnm-canvas"
          aria-label="Canvas do diagrama BPMN"
        />
        <aside className="bpmnm-side">
          <div className="bpmnm-side__tabs" role="tablist">
            <button role="tab" aria-selected={sideTab === "properties"} className={sideTab === "properties" ? "active" : ""} onClick={() => setSideTab("properties")}>
              Propriedades
            </button>
            <button role="tab" aria-selected={sideTab === "validation"} className={sideTab === "validation" ? "active" : ""} onClick={() => setSideTab("validation")}>
              Validação
            </button>
            <button role="tab" aria-selected={sideTab === "history"} className={sideTab === "history" ? "active" : ""} onClick={() => setSideTab("history")}>
              Histórico
            </button>
          </div>
          <div className="bpmnm-side__content">
            {sideTab === "properties" ? (
              isEditable ? (
                <div id="bpmn-properties-panel" className="bpmnm-properties" />
              ) : (
                <ElementInspector element={selection} />
              )
            ) : null}
            {sideTab === "validation" ? (
              <ValidationPanel
                report={report}
                onSelectIssue={(ref) => adapterRef.current?.selectElement(ref)}
              />
            ) : null}
            {sideTab === "history" ? (
              <RevisionHistoryList
                revisions={revisions}
                loading={revisionsLoading}
                canManage={capabilities.manage && !model?.archived_at}
                onView={(n) => guardedNavigate(`/apps/bpmn-modeler/models/${modelId}/revisions/${n}`)}
                onRestore={(n) => void onRestore(n)}
                onCreateRevision={() => void onCreateRevision()}
              />
            ) : null}
          </div>
        </aside>
      </div>

      <ConflictDialog
        open={machineState === "CONFLICT"}
        onReloadLatest={() => void loadModel()}
        onExportLocal={() => {
          void adapterRef.current?.exportXml().then((xml) => {
            const blob = new Blob([xml], { type: "application/xml" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "modelo-local.bpmn";
            a.click();
            URL.revokeObjectURL(url);
          });
        }}
        onStay={() => undefined}
      />

      {unsavedOpen ? (
        <UnsavedChangesDialog
          open
          canEdit={isEditable && machineState !== "CONFLICT"}
          onContinue={() => setUnsavedOpen(null)}
          onDiscard={() => unsavedOpen()}
          onSaveAndExit={() => {
            void save().then((ok) => {
              if (ok) unsavedOpen();
            });
          }}
        />
      ) : null}
    </div>
  );
}
