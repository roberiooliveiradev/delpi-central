import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  ActionButton,
  ConfirmModalPanel,
  ContextMenu,
  ContextMenuDivider,
  ContextMenuItem,
  IconButton,
  type FixedPanelPoint,
} from "@delpi/plugin-ui/index";
import {
  Archive,
  ArchiveRestore,
  ArrowLeft,
  ClipboardCheck,
  Download,
  FileText,
  History,
  Maximize,
  MoreVertical,
  MousePointerSquareDashed,
  PanelRightClose,
  PanelRightOpen,
  Redo2,
  Save,
  SlidersHorizontal,
  Trash2,
  Undo2,
  Wand2,
  ZoomIn,
  ZoomOut,
} from "lucide-react";

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
import { buildDiOps, buildDiXml, hasBpmnDi, injectDiIntoXml, planeElementFor, snapshotFromXml, stripBpmnDi, type DiLayoutOp } from "../layout/diProposal";
import { capabilitiesFromPermissions, editableMode, type Capabilities, type ReadOnlyReason } from "../state/capabilities";
import { SaveMachine, type SaveState } from "../state/saveMachine";
import { ConflictDialog } from "../components/ConflictDialog";
import { DiagramSelector } from "../components/DiagramSelector";
import { useExportActions } from "../components/ExportMenu";
import { ReadOnlyBanner } from "../components/ReadOnlyBanner";
import { SaveStatus } from "../components/SaveStatus";
import { UnsavedChangesDialog } from "../components/UnsavedChangesDialog";
import { ValidationPanel } from "../components/ValidationPanel";
import { RevisionHistoryList } from "../components/RevisionHistoryList";
import { HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  BPMNM_ROOT_CLASS,
  BpmnmModal,
  BpmnmStateBanner,
  BpmnmStatusBadge,
  BpmnmUnderlineNav,
  bpmnmConfirmModalClasses,
} from "../ui/kit";

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
  const [sideCollapsed, setSideCollapsed] = useState(false);
  const [report, setReport] = useState<ValidationReport | null>(null);
  const [revisions, setRevisions] = useState<RevisionSummary[]>([]);
  const [revisionsLoading, setRevisionsLoading] = useState(false);
  const [diagrams, setDiagrams] = useState<DiagramRef[]>([]);
  const [selection, setSelection] = useState<ElementSummary | null>(null);
  const [unsavedOpen, setUnsavedOpen] = useState<(() => void) | null>(null);
  const [layoutBusy, setLayoutBusy] = useState(false);
  const [preview, setPreview] = useState<{ ops: DiLayoutOp[]; xml: string } | null>(null);
  const previewAdapterRef = useRef<BpmnEditorAdapter | null>(null);
  const previewCanvasRef = useRef<HTMLDivElement>(null);
  const [isTablet, setIsTablet] = useState(false);
  const [adapterInstance, setAdapterInstance] = useState<BpmnEditorAdapter | null>(null);
  const [restoreTarget, setRestoreTarget] = useState<number | null>(null);
  const [restoreBusy, setRestoreBusy] = useState(false);
  const [overflowMenu, setOverflowMenu] = useState<FixedPanelPoint | null>(null);
  const [canvasMenu, setCanvasMenu] = useState<{ elementId: string | null; point: FixedPanelPoint } | null>(null);
  const canvasWrapRef = useRef<HTMLDivElement>(null);
  const overflowAnchorRef = useRef<HTMLSpanElement>(null);
  const exportActions = useExportActions(modelId, adapterInstance, getAccessToken);

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

      // lifecycle: destroy do adapter anterior antes de recriar
      // (CANVAS-REG — nunca duas instâncias de editor no mesmo canvas)
      adapterRef.current?.destroy();
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
        onCanvasContextMenu: (event) => {
          setCanvasMenu({
            elementId: event.elementId,
            point: { x: event.x, y: event.y },
          });
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
      previewAdapterRef.current?.destroy();
      previewAdapterRef.current = null;
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

  // canvas resize lifecycle: ResizeObserver no wrap — sidebar, toolbar wrap,
  // janela e mount afetam o viewport do renderer (P4 §7 via adapter).
  useEffect(() => {
    const wrap = canvasWrapRef.current;
    const adapter = adapterInstance;
    if (!wrap || !adapter || typeof ResizeObserver === "undefined") return;
    let frame = 0;
    const observer = new ResizeObserver(() => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => adapter.resized());
    });
    observer.observe(wrap);
    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
    };
  }, [adapterInstance]);

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

  // sidebar collapse/expand: canvas ganha o espaço real — notifica o
  // modeler para re-medir o container preservando zoom/pan/seleção
  useEffect(() => {
    adapterRef.current?.resized();
  }, [sideCollapsed]);

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

  // restore: confirmação via ConfirmModalPanel (sem window.confirm)
  const onConfirmRestore = async (revisionNumber: number) => {
    setRestoreBusy(true);
    try {
      await restoreRevision(modelId, revisionNumber, version, { getAccessToken });
      setRestoreTarget(null);
      // replace model = destroy + mount + importXml (P4 §10)
      await loadModel();
      void loadRevisions();
    } catch (err) {
      setRestoreTarget(null);
      setPageError(err instanceof BpmnModelerApiError ? err.message : "Falha ao restaurar.");
    } finally {
      setRestoreBusy(false);
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

  // ---------- auto-layout (preview → accept/cancel, P5 §18) ----------
  const closePreview = useCallback(() => {
    previewAdapterRef.current?.destroy();
    previewAdapterRef.current = null;
    setPreview(null);
  }, []);

  const onOrganize = async () => {
    const adapter = adapterRef.current;
    if (!adapter || preview) return;
    setLayoutBusy(true);
    try {
      const xml = await adapter.exportXml();
      const snapshot = snapshotFromXml(xml);
      const graph = buildElkGraph(snapshot);
      const job = runLayout(graph);
      layoutJobRef.current = job;
      const outcome = await job.promise;
      if (!outcome.ok) return;

      const planeElement = planeElementFor(xml);
      if (!planeElement) return;
      const ops = buildDiOps(outcome.graph);
      // artefato transient de preview: DI existente removido para que o
      // viewer mostre a proposta (o artefato canônico nunca é reescrito aqui).
      const previewXml = injectDiIntoXml(
        stripBpmnDi(xml),
        buildDiXml(outcome.graph, snapshot, planeElement),
      );
      setPreview({ ops, xml: previewXml });
    } finally {
      layoutJobRef.current = null;
      setLayoutBusy(false);
    }
  };

  // preview viewer transitório (NavigatedViewer) — ciclo de vida isolado
  // do main editor, que permanece intacto até o Accept (P5 §18).
  useEffect(() => {
    if (!preview || !previewCanvasRef.current) return;
    const previewAdapter = new BpmnEditorAdapter();
    previewAdapter.mount(previewCanvasRef.current, "viewer");
    previewAdapterRef.current = previewAdapter;
    void previewAdapter.importXml(preview.xml).then((result) => {
      if (result.ok) previewAdapter.fitViewport();
      else setPageError(result.error.message);
    });
    return () => {
      previewAdapter.destroy();
      if (previewAdapterRef.current === previewAdapter)
        previewAdapterRef.current = null;
    };
  }, [preview]);

  // Accept → UM comando lógico no editor principal → DIRTY (undo reverte).
  const onAcceptPreview = () => {
    if (!preview) return;
    adapterRef.current?.applyDiLayout(preview.ops);
    closePreview();
  };

  // Cancel → preview destruído; main editor bit-a-bit intacto.
  const onCancelPreview = () => {
    closePreview();
  };

  // ---------- navigation guard ----------
  const guardedNavigate = (path: string) => {
    // saída forçada durante preview ⇒ Cancel automático (P5 §18)
    if (preview) closePreview();
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
      <div className={`${BPMNM_ROOT_CLASS} dashboard-page bpmnm-page`}>
        <BpmnmStateBanner variant="error" className="bpmnm-error">
          {pageError}{" "}
          <ActionButton variant="link" onClick={() => void loadModel()}>
            Tentar novamente
          </ActionButton>
        </BpmnmStateBanner>
      </div>
    );
  }

  return (
    <div className={`${BPMNM_ROOT_CLASS} dashboard-page dashboard-page--fill bpmnm-page bpmnm-editor`}>
      <header className="bpmnm-editor__header">
        <div className="bpmnm-editor__group bpmnm-editor__group--nav">
          <ActionButton
            type="button"
            variant="ghost"
            onClick={() => guardedNavigate("/apps/bpmn-modeler")}
          >
            <ArrowLeft size={16} aria-hidden="true" /> Biblioteca
          </ActionButton>
          <h1 className="bpmnm-editor__title">
            {model?.display_name ?? "…"}
            {model?.archived_at ? (
              <BpmnmStatusBadge
                label="Arquivado"
                variant="warning"
                className="bpmnm-badge"
              />
            ) : null}
          </h1>
          <SaveStatus state={machineState} />
        </div>

        {isEditable && !preview && (
          <div className="bpmnm-editor__group bpmnm-editor__group--edit">
            <span
              title={
                machineState !== "DIRTY" && machineState !== "CLEAN"
                  ? HELP_TOOLTIPS.editor.noUndo
                  : HELP_TOOLTIPS.editor.undo
              }
              className="bpmnm-zoom"
            >
              <IconButton
                aria-label="Desfazer"
                disabled={machineState !== "DIRTY" && machineState !== "CLEAN"}
                onClick={() => adapterRef.current?.undo()}
              >
                <Undo2 size={15} aria-hidden="true" />
              </IconButton>
            </span>
            <span
              title={
                machineState !== "DIRTY" && machineState !== "CLEAN"
                  ? HELP_TOOLTIPS.editor.noRedo
                  : HELP_TOOLTIPS.editor.redo
              }
              className="bpmnm-zoom"
            >
              <IconButton
                aria-label="Refazer"
                disabled={machineState !== "DIRTY" && machineState !== "CLEAN"}
                onClick={() => adapterRef.current?.redo()}
              >
                <Redo2 size={15} aria-hidden="true" />
              </IconButton>
            </span>
            <span className="bpmnm-editor__divider" aria-hidden="true" />
            <ActionButton
              type="button"
              title={HELP_TOOLTIPS.editor.organize}
              disabled={layoutBusy || !adapterInstance}
              onClick={() => void onOrganize()}
            >
              <Wand2 size={15} aria-hidden="true" />
              {layoutBusy ? "Calculando layout…" : "Organizar"}
            </ActionButton>
            {layoutBusy && (
              <ActionButton
                type="button"
                onClick={() => layoutJobRef.current?.cancel()}
              >
                Cancelar
              </ActionButton>
            )}
            <ActionButton
              type="button"
              title={HELP_TOOLTIPS.editor.validate}
              disabled={!adapterInstance}
              onClick={() => void onValidate()}
            >
              <ClipboardCheck size={15} aria-hidden="true" />
              Validar
            </ActionButton>
          </div>
        )}

        <div className="bpmnm-editor__group bpmnm-editor__group--right">
          {isEditable && !preview && (
            <ActionButton
              type="button"
              variant="primary"
              title={HELP_TOOLTIPS.editor.save}
              disabled={machineState !== "DIRTY" && machineState !== "SAVE_FAILED"}
              onClick={() => void save()}
            >
              <Save size={15} aria-hidden="true" />
              Salvar
            </ActionButton>
          )}
          {!preview && (
            <>
              <DiagramSelector
                diagrams={diagrams}
                activeId={diagrams[0]?.id ?? null}
                onSelect={(id) => adapterRef.current?.openDiagram(id)}
              />
              <span
                title={HELP_TOOLTIPS.editor.moreActions}
                className="bpmnm-zoom"
                ref={overflowAnchorRef}
              >
                <IconButton
                  aria-label="Mais ações"
                  aria-expanded={overflowMenu !== null}
                  onClick={() => {
                    const rect =
                      overflowAnchorRef.current?.getBoundingClientRect();
                    setOverflowMenu((m) =>
                      m ? null : rect ? { x: rect.right, y: rect.bottom } : null,
                    );
                  }}
                >
                  <MoreVertical size={15} aria-hidden="true" />
                </IconButton>
              </span>
            </>
          )}
        </div>
      </header>

      <ReadOnlyBanner reason={isTablet && isEditable === false && capabilities.edit ? null : readOnlyReason} />
      {isTablet && capabilities.edit && !readOnlyReason ? (
        <BpmnmStateBanner className="bpmnm-banner bpmnm-banner--readonly">
          Em tablets o editor opera em modo somente leitura.
        </BpmnmStateBanner>
      ) : null}
      {pageError ? (
        <BpmnmStateBanner variant="error" className="bpmnm-error">
          {pageError}
        </BpmnmStateBanner>
      ) : null}

      <div className="bpmnm-editor__body">
        <div className="bpmnm-canvas-wrap" ref={canvasWrapRef}>
          <div
            ref={canvasRef}
            className="bpmnm-canvas"
            aria-label="Canvas do diagrama BPMN"
          />
          {!preview && (
            <div
              className="bpmnm-viewport-controls"
              role="group"
              aria-label="Controles de visualização do canvas"
            >
              <span
                title={
                  adapterInstance
                    ? HELP_TOOLTIPS.editor.zoomIn
                    : HELP_TOOLTIPS.editor.editorLoading
                }
                className="bpmnm-zoom"
              >
                <IconButton
                  aria-label="Ampliar"
                  disabled={!adapterInstance}
                  onClick={() => adapterRef.current?.zoomIn()}
                >
                  <ZoomIn size={15} aria-hidden="true" />
                </IconButton>
              </span>
              <span
                title={
                  adapterInstance
                    ? HELP_TOOLTIPS.editor.zoomOut
                    : HELP_TOOLTIPS.editor.editorLoading
                }
                className="bpmnm-zoom"
              >
                <IconButton
                  aria-label="Reduzir"
                  disabled={!adapterInstance}
                  onClick={() => adapterRef.current?.zoomOut()}
                >
                  <ZoomOut size={15} aria-hidden="true" />
                </IconButton>
              </span>
              <span
                title={
                  adapterInstance
                    ? HELP_TOOLTIPS.editor.fitViewport
                    : HELP_TOOLTIPS.editor.editorLoading
                }
                className="bpmnm-zoom"
              >
                <IconButton
                  aria-label="Ajustar à janela"
                  disabled={!adapterInstance}
                  onClick={() => adapterRef.current?.fitViewport()}
                >
                  <Maximize size={15} aria-hidden="true" />
                </IconButton>
              </span>
            </div>
          )}
          {preview && (
            <div className="bpmnm-preview" data-testid="layout-preview">
              <div className="bpmnm-preview__banner" role="status">
                <BpmnmStatusBadge label="Pré-visualização" variant="info" />
                Pré-visualização do layout — nada foi alterado. Aceitar
                aplica o layout ao diagrama; Cancelar descarta.
                <span style={{ marginLeft: "auto", display: "inline-flex", gap: 8 }}>
                  <ActionButton
                    type="button"
                    variant="primary"
                    onClick={onAcceptPreview}
                  >
                    Aceitar
                  </ActionButton>
                  <ActionButton type="button" onClick={onCancelPreview}>
                    Cancelar
                  </ActionButton>
                </span>
              </div>
              <div
                ref={previewCanvasRef}
                className="bpmnm-canvas bpmnm-preview__canvas"
                aria-label="Pré-visualização do layout proposto"
              />
            </div>
          )}
        </div>
        <aside
          className={`bpmnm-side${sideCollapsed ? " bpmnm-side--collapsed" : ""}`}
        >
          {sideCollapsed ? (
            <>
              {/* rail colapsada: expander + atalhos que expandem já na aba */}
              <div className="bpmnm-side__rail" role="toolbar" aria-label="Painéis do editor">
                <span title={HELP_TOOLTIPS.sidebar.expand} className="bpmnm-zoom">
                  <IconButton
                    aria-label="Expandir painel lateral"
                    aria-expanded={false}
                    onClick={() => setSideCollapsed(false)}
                  >
                    <PanelRightOpen size={15} aria-hidden="true" />
                  </IconButton>
                </span>
                <span className="bpmnm-side__rail-sep" aria-hidden="true" />
                {(
                  [
                    ["properties", "Propriedades", HELP_TOOLTIPS.sidebar.propertiesTab, <SlidersHorizontal key="i" size={15} aria-hidden="true" />],
                    ["validation", "Validação", HELP_TOOLTIPS.sidebar.validationTab, <ClipboardCheck key="i" size={15} aria-hidden="true" />],
                    ["history", "Histórico", HELP_TOOLTIPS.sidebar.historyTab, <History key="i" size={15} aria-hidden="true" />],
                  ] as const
                ).map(([tab, label, tip, icon]) => (
                  <span key={tab} title={tip} className="bpmnm-zoom">
                    <IconButton
                      aria-label={label}
                      aria-expanded={false}
                      tone={sideTab === tab ? "primary" : "default"}
                      onClick={() => {
                        setSideTab(tab);
                        setSideCollapsed(false);
                      }}
                    >
                      {icon}
                    </IconButton>
                  </span>
                ))}
              </div>
              {/* host do properties panel permanece montado (attach do vendor) */}
              <div id="bpmnm-side-panel" hidden>
                <div id="bpmn-properties-panel" className="bpmnm-properties" />
              </div>
            </>
          ) : (
            <>
              <div className="bpmnm-side__head">
                <BpmnmUnderlineNav
                  className="bpmnm-side__tabs"
                  aria-label="Painéis do editor"
                  activeId={sideTab}
                  mode="tabs"
                  items={[
                    {
                      id: "properties",
                      label: "Propriedades",
                      iconOnly: true,
                      icon: <SlidersHorizontal size={15} aria-hidden="true" />,
                      title: HELP_TOOLTIPS.sidebar.propertiesTab,
                      controlId: "bpmnm-side-panel",
                      onSelect: () => setSideTab("properties"),
                    },
                    {
                      id: "validation",
                      label: "Validação",
                      iconOnly: true,
                      icon: <ClipboardCheck size={15} aria-hidden="true" />,
                      title: HELP_TOOLTIPS.sidebar.validationTab,
                      controlId: "bpmnm-side-panel",
                      onSelect: () => setSideTab("validation"),
                    },
                    {
                      id: "history",
                      label: "Histórico",
                      iconOnly: true,
                      icon: <History size={15} aria-hidden="true" />,
                      title: HELP_TOOLTIPS.sidebar.historyTab,
                      controlId: "bpmnm-side-panel",
                      onSelect: () => setSideTab("history"),
                    },
                  ]}
                />
                <span
                  title={HELP_TOOLTIPS.sidebar.collapse}
                  className="bpmnm-zoom bpmnm-side__collapse"
                >
                  <IconButton
                    aria-label="Recolher painel lateral"
                    aria-expanded={true}
                    onClick={() => setSideCollapsed(true)}
                  >
                    <PanelRightClose size={15} aria-hidden="true" />
                  </IconButton>
                </span>
              </div>
              <div
                id="bpmnm-side-panel"
                className="bpmnm-side__content"
                role="tabpanel"
                aria-labelledby={`${sideTab}-tab`}
              >
                {/* o Modeler exige o parent no mount — sempre presente no DOM,
                    visível só na aba Propriedades em modo editável */}
                <div
                  id="bpmn-properties-panel"
                  className="bpmnm-properties"
                  hidden={sideTab !== "properties" || !isEditable}
                />
                {sideTab === "properties" && !isEditable ? (
                  <ElementInspector element={selection} />
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
                    onRestore={(n) => setRestoreTarget(n)}
                    onCreateRevision={() => void onCreateRevision()}
                  />
                ) : null}
              </div>
            </>
          )}
        </aside>
      </div>

      {/* overflow ⋮ — ações de baixa frequência (exportar/arquivar) */}
      <ContextMenu
        open={overflowMenu !== null}
        position={overflowMenu}
        onClose={() => setOverflowMenu(null)}
        aria-label="Mais ações do editor"
        portalScopeClassName={BPMNM_ROOT_CLASS}
      >
        <ContextMenuItem
          label="Exportar BPMN"
          icon={Download}
          disabled={exportActions.busy}
          onSelect={() => {
            setOverflowMenu(null);
            void exportActions.exportBpmn();
          }}
        />
        <ContextMenuItem
          label="Exportar SVG"
          icon={FileText}
          disabled={!adapterInstance || exportActions.busy}
          onSelect={() => {
            setOverflowMenu(null);
            void exportActions.exportSvg();
          }}
        />
        <ContextMenuItem
          label="Exportar PNG"
          icon={FileText}
          disabled={!adapterInstance || exportActions.busy}
          onSelect={() => {
            setOverflowMenu(null);
            void exportActions.exportPng();
          }}
        />
        {capabilities.manage && model ? (
          <>
            <ContextMenuDivider />
            <ContextMenuItem
              label={model.archived_at ? "Desarquivar" : "Arquivar"}
              icon={model.archived_at ? ArchiveRestore : Archive}
              onSelect={() => {
                setOverflowMenu(null);
                void onArchiveToggle();
              }}
            />
          </>
        ) : null}
      </ContextMenu>

      {/* contexto do canvas — comandos oficiais do vendor via adapter */}
      <ContextMenu
        open={canvasMenu !== null}
        position={canvasMenu?.point ?? null}
        onClose={() => setCanvasMenu(null)}
        aria-label="Menu do diagrama"
        portalScopeClassName={BPMNM_ROOT_CLASS}
      >
        {canvasMenu?.elementId ? (
          <>
            <ContextMenuItem
              label="Renomear"
              icon={FileText}
              disabled={!isEditable}
              onSelect={() => {
                adapterRef.current?.directEdit(canvasMenu.elementId!);
                setCanvasMenu(null);
              }}
            />
            <ContextMenuItem
              label="Excluir"
              icon={Trash2}
              disabled={!isEditable}
              onSelect={() => {
                adapterRef.current?.removeElement(canvasMenu.elementId!);
                setCanvasMenu(null);
              }}
            />
            <ContextMenuDivider />
          </>
        ) : (
          <ContextMenuItem
            label="Selecionar tudo"
            icon={MousePointerSquareDashed}
            disabled={!adapterInstance}
            onSelect={() => {
              adapterRef.current?.selectAll();
              setCanvasMenu(null);
            }}
          />
        )}
        <ContextMenuItem
          label="Ajustar à janela"
          icon={Maximize}
          disabled={!adapterInstance}
          onSelect={() => {
            adapterRef.current?.fitViewport();
            setCanvasMenu(null);
          }}
        />
      </ContextMenu>

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

      <BpmnmModal
        open={restoreTarget !== null}
        title="Restaurar revisão"
        onClose={() => setRestoreTarget(null)}
      >
        <ConfirmModalPanel
          message={`Restaurar a revisão ${restoreTarget}? O working copy atual será substituído.`}
          confirmLabel="Restaurar"
          confirmBusy={restoreBusy}
          confirmBusyLabel="Restaurando…"
          variant="danger"
          onConfirm={() => {
            if (restoreTarget !== null) void onConfirmRestore(restoreTarget);
          }}
          onCancel={() => setRestoreTarget(null)}
          classNames={bpmnmConfirmModalClasses}
        />
      </BpmnmModal>
    </div>
  );
}
