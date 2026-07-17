import {
  dataTransformStepLabel,
  isDataTransformV1,
  isDataSourceBlockType,
  normalizeDataTransform,
  type ComunicadoDataSourceBlock,
  type DataTransform,
  type DataTransformStep,
} from "@delpi/tv-dashboard-presentation";
import {
  HintAction,
  SectionHintLabel,
  type FixedPanelPoint,
} from "@delpi/plugin-ui/index";
import {
  Columns3,
  Pencil,
  Plus,
  Settings2,
  Trash2,
  X,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState, type MouseEvent } from "react";

import {
  listDataRoutes,
  type TvDataRouteCatalogItem,
} from "../api/tvDashboardApi";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  canUseAdvancedMEditor,
  canUseMWorkbench,
} from "../features/data-query/domain/dataQueryCapabilities";
import { useDataQueryCapabilities } from "../features/data-query/state/useDataQueryWorkbench";
import { DataQueryWorkbenchModal } from "../features/data-query/ui/DataPrepareModal";
import {
  linkedChartSeriesForSource,
  seriesForColumn,
} from "../utils/dataPrepareCrossHighlight";
import {
  previewTransformTableOnServer,
  type ServerTransformTable,
} from "../utils/previewTransformTableOnServer";
import {
  DataPrepareContextMenu,
  type DataPrepareCtxTarget,
} from "./DataPrepareContextMenu";
import { DataPrepareFormulaBar } from "./DataPrepareFormulaBar";
import {
  DataPrepareRibbon,
  type DataPrepareRibbonOpenRequest,
  type RibbonTab,
} from "./DataPrepareRibbon";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { Modal } from "./ui/Modal";

const H = TV_DASHBOARD_HELP_TOOLTIPS.dataPrepare;

type Props = {
  open: boolean;
  onClose: () => void;
  initialSourceId?: string | null;
};

function queryLabel(block: ComunicadoDataSourceBlock): string {
  const label = block.dataBinding?.label?.trim();
  if (label) return label;
  const op = block.dataBinding?.operationId?.trim();
  if (op) return op;
  return `Fonte ${block.id.slice(0, 6)}`;
}

const EMPTY_STEPS: DataTransformStep[] = [];

/**
 * Ambiente de preparação estilo Power Query — modal.
 * Clique esquerdo: seleciona/desseleciona. Botão direito: menu de ações.
 */
function LegacyDataPrepareModal({ open, onClose, initialSourceId = null }: Props) {
  const {
    blocks,
    config,
    playlistId,
    updateBlock,
    refreshDataPreview,
  } = useComunicadoEditor();
  const queries = useMemo(
    () =>
      blocks.filter((block): block is ComunicadoDataSourceBlock =>
        isDataSourceBlockType(block.type),
      ),
    [blocks],
  );

  const [activeId, setActiveId] = useState<string | null>(initialSourceId);
  const [ribbonTab, setRibbonTab] = useState<RibbonTab>("home");
  const [previewStepIndex, setPreviewStepIndex] = useState<number | null>(null);
  const [newColumnDraft, setNewColumnDraft] = useState(false);
  const [formulaFocusToken, setFormulaFocusToken] = useState(0);
  const [activeColumn, setActiveColumn] = useState("");
  const [routes, setRoutes] = useState<TvDataRouteCatalogItem[]>([]);
  const [preview, setPreview] = useState<ServerTransformTable>({ columns: [], rows: [] });
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [previewEpoch, setPreviewEpoch] = useState(0);
  const [ctxMenu, setCtxMenu] = useState<{
    position: FixedPanelPoint;
    target: DataPrepareCtxTarget;
  } | null>(null);
  const [ribbonOpenToken, setRibbonOpenToken] = useState(0);
  const [ribbonOpenRequest, setRibbonOpenRequest] =
    useState<DataPrepareRibbonOpenRequest | null>(null);

  const configRef = useRef(config);
  configRef.current = config;
  const forcePreviewRef = useRef(false);
  const previewRequestIdRef = useRef(0);

  useEffect(() => {
    if (!open) return;
    void listDataRoutes()
      .then(setRoutes)
      .catch(() => setRoutes([]));
  }, [open]);

  useEffect(() => {
    if (!open) {
      setCtxMenu(null);
      return;
    }
    if (initialSourceId && queries.some((q) => q.id === initialSourceId)) {
      setActiveId(initialSourceId);
      return;
    }
    if (activeId && queries.some((q) => q.id === activeId)) return;
    setActiveId(queries[0]?.id ?? null);
  }, [open, initialSourceId, queries, activeId]);

  const active = queries.find((q) => q.id === activeId) ?? null;
  const activeBlockRef = useRef(active);
  activeBlockRef.current = active;
  const steps = isDataTransformV1(active?.dataTransform)
    ? active.dataTransform.steps
    : EMPTY_STEPS;

  useEffect(() => {
    setPreviewStepIndex(steps.length > 0 ? steps.length - 1 : null);
    setNewColumnDraft(false);
    setActiveColumn("");
  }, [activeId, steps.length]);

  useEffect(() => {
    setNewColumnDraft(false);
  }, [previewStepIndex]);

  const stepsThroughKey = useMemo(() => {
    if (previewStepIndex == null) return "[]";
    return JSON.stringify(steps.slice(0, previewStepIndex + 1));
  }, [previewStepIndex, steps]);

  useEffect(() => {
    if (!open || !activeId) {
      setPreview({ columns: [], rows: [] });
      setPreviewError(null);
      setPreviewLoading(false);
      return;
    }

    let cancelled = false;
    const requestId = ++previewRequestIdRef.current;
    const forceRefresh = forcePreviewRef.current;
    forcePreviewRef.current = false;

    const handle = window.setTimeout(() => {
      const block = activeBlockRef.current;
      if (!block || block.id !== activeId) {
        setPreviewLoading(false);
        return;
      }
      const stepsThrough =
        stepsThroughKey === "[]"
          ? ([] as DataTransformStep[])
          : ((JSON.parse(stepsThroughKey) as DataTransformStep[]) ?? []);

      setPreviewLoading(true);
      setPreviewError(null);
      void previewTransformTableOnServer({
        block,
        config: configRef.current,
        playlistId,
        stepsThrough,
        forceRefresh,
      })
        .then((table) => {
          if (cancelled || previewRequestIdRef.current !== requestId) return;
          setPreview(table);
        })
        .catch((err: unknown) => {
          if (cancelled || previewRequestIdRef.current !== requestId) return;
          setPreviewError(
            err instanceof Error ? err.message : "Falha ao calcular prévia no servidor.",
          );
          setPreview({ columns: [], rows: [] });
        })
        .finally(() => {
          if (cancelled || previewRequestIdRef.current !== requestId) return;
          setPreviewLoading(false);
        });
    }, 280);

    return () => {
      cancelled = true;
      window.clearTimeout(handle);
    };
  }, [open, activeId, playlistId, stepsThroughKey, previewEpoch]);

  const linkedSeries = useMemo(
    () => linkedChartSeriesForSource(blocks, activeId),
    [blocks, activeId],
  );

  const routePreset = useMemo(() => {
    const op = active?.dataBinding?.operationId?.trim();
    if (!op) return null;
    return routes.find((route) => route.operationId === op) ?? null;
  }, [active, routes]);

  const persistSteps = (nextSteps: DataTransformStep[]) => {
    if (!active) return;
    const transform = normalizeDataTransform({ steps: nextSteps }) as DataTransform | undefined;
    updateBlock(active.id, { dataTransform: transform } as Partial<ComunicadoDataSourceBlock>);
  };

  const addStep = (step: DataTransformStep) => {
    persistSteps([...steps, step]);
  };

  const replaceStep = (index: number, step: DataTransformStep) => {
    const next = [...steps];
    next[index] = step;
    persistSteps(next);
  };

  const removeStep = (index: number) => {
    persistSteps(steps.filter((_, i) => i !== index));
  };

  const moveStep = (index: number, delta: number) => {
    const target = index + delta;
    if (target < 0 || target >= steps.length) return;
    const next = [...steps];
    const [item] = next.splice(index, 1);
    next.splice(target, 0, item!);
    persistSteps(next);
  };

  const commitFormulaStep = (step: DataTransformStep) => {
    if (newColumnDraft) {
      addStep(step);
      setNewColumnDraft(false);
      return;
    }
    if (previewStepIndex == null) return;
    const current = steps[previewStepIndex];
    if (!current) return;
    if (JSON.stringify(current) === JSON.stringify(step)) return;
    replaceStep(previewStepIndex, step);
  };

  const startNewColumnFromFx = () => {
    setRibbonTab("addColumn");
    setNewColumnDraft(true);
    setFormulaFocusToken((n) => n + 1);
  };

  const applySuggestedPreset = () => {
    const suggested = routePreset?.suggestedTransformSteps;
    if (!Array.isArray(suggested) || !suggested.length || !active) return;
    const normalized = normalizeDataTransform({ steps: suggested });
    if (!isDataTransformV1(normalized) || !normalized.steps.length) return;
    persistSteps(normalized.steps);
  };

  const columnOptions = preview.columns.map((col) => ({ value: col, label: col }));
  const siblingOptions = queries
    .filter((q) => q.id !== activeId)
    .map((q) => ({ value: q.id, label: queryLabel(q) }));

  const handleCloseAndApply = () => {
    void refreshDataPreview({
      force: true,
      blockIds: active ? [active.id] : undefined,
    });
    onClose();
  };

  const requestServerPreview = (force = false) => {
    forcePreviewRef.current = force;
    setPreviewEpoch((n) => n + 1);
  };

  const focusFormulaForStep = (index: number) => {
    setPreviewStepIndex(index);
    setNewColumnDraft(false);
    setFormulaFocusToken((n) => n + 1);
    const step = steps[index];
    if (!step) return;
    if (step.op === "addColumn") setRibbonTab("addColumn");
    else if (step.op === "merge") setRibbonTab("combine");
    else if (step.op === "select" || step.op === "firstRowAsHeader") setRibbonTab("home");
    else setRibbonTab("transform");
  };

  const toggleQuery = (id: string) => {
    setActiveId((prev) => (prev === id ? null : id));
  };

  const toggleStep = (index: number | null) => {
    setPreviewStepIndex((prev) => (prev === index ? null : index));
  };

  const toggleColumn = (col: string) => {
    setActiveColumn((prev) => (prev === col ? "" : col));
  };

  const openContextMenu = useCallback((event: MouseEvent, target: DataPrepareCtxTarget) => {
    event.preventDefault();
    event.stopPropagation();
    if (target.kind === "query") setActiveId(target.id);
    if (target.kind === "step") setPreviewStepIndex(target.index);
    if (target.kind === "fonte") setPreviewStepIndex(null);
    if (target.kind === "column") setActiveColumn(target.name);
    setCtxMenu({
      position: { x: event.clientX, y: event.clientY },
      target,
    });
  }, []);

  const openRibbonAction = (request: DataPrepareRibbonOpenRequest) => {
    setRibbonTab(request.tab);
    setRibbonOpenRequest(request);
    setRibbonOpenToken((n) => n + 1);
  };

  const copyText = (text: string) => {
    if (!text.trim()) return;
    void navigator.clipboard?.writeText(text).catch(() => undefined);
  };

  return (
    <Modal
      open={open}
      title="Preparar dados"
      onClose={onClose}
      className="td-modal--data-prepare"
      footer={
        <div className="td-data-pq__footer">
          <HintAction hint={H.footerCancel} ariaLabel="Ajuda: cancelar" placement="top">
            <button type="button" className="td-btn td-btn--sm td-btn--ghost" onClick={onClose}>
              Cancelar
            </button>
          </HintAction>
          <HintAction hint={H.footerApply} ariaLabel="Ajuda: fechar e aplicar" placement="top">
            <button type="button" className="td-btn td-btn--sm" onClick={handleCloseAndApply}>
              Fechar e aplicar
            </button>
          </HintAction>
        </div>
      }
    >
      {queries.length === 0 ? (
        <p className="td-deck-inspector__hint">{H.modal}</p>
      ) : (
        <div
          className="td-data-pq"
          onClick={() => setCtxMenu(null)}
          onContextMenu={(event) => {
            // Evita menu nativo no workspace; menus específicos usam stopPropagation.
            if ((event.target as HTMLElement).closest("[data-pq-ctx]")) return;
            event.preventDefault();
          }}
        >
          <DataPrepareRibbon
            tab={ribbonTab}
            onTabChange={setRibbonTab}
            columnOptions={columnOptions}
            activeColumn={activeColumn}
            onActiveColumnChange={setActiveColumn}
            siblingOptions={siblingOptions}
            previewLoading={previewLoading}
            hasPreset={Boolean(routePreset?.suggestedTransformSteps?.length)}
            onRefresh={() => requestServerPreview(true)}
            onAddStep={addStep}
            onStartFxColumn={startNewColumnFromFx}
            onApplyPreset={applySuggestedPreset}
            openRequestToken={ribbonOpenToken}
            openRequest={ribbonOpenRequest}
          />

          <div className="td-data-pq__workspace">
            <aside className="td-data-pq__queries" aria-label="Consultas (rotas)">
              <div className="td-data-pq__pane-title">
                <SectionHintLabel label={`Consultas [${queries.length}]`} hint={H.queries} />
              </div>
              <ul className="td-data-pq__query-list">
                {queries.map((query) => {
                  const selectedQuery = query.id === activeId;
                  return (
                    <li key={query.id}>
                      <HintAction
                        hint={H.queryItem}
                        ariaLabel={`Ajuda: consulta ${queryLabel(query)}`}
                        placement="bottom"
                        suppressed={Boolean(ctxMenu)}
                      >
                        <button
                          type="button"
                          data-pq-ctx="query"
                          className={
                            selectedQuery
                              ? "td-data-pq__query td-data-pq__query--selected"
                              : "td-data-pq__query"
                          }
                          aria-pressed={selectedQuery}
                          onClick={(event) => {
                            event.stopPropagation();
                            toggleQuery(query.id);
                          }}
                          onContextMenu={(event) =>
                            openContextMenu(event, { kind: "query", id: query.id })
                          }
                        >
                          <Columns3 size={14} aria-hidden />
                          <span className="td-data-pq__query-label">{queryLabel(query)}</span>
                          <span className="td-data-pq__query-meta">
                            {query.dataBinding?.operationId || "rota"}
                          </span>
                        </button>
                      </HintAction>
                    </li>
                  );
                })}
              </ul>
            </aside>

            <section className="td-data-pq__main" aria-label="Prévia">
              <div className="td-data-pq__banner">
                <HintAction hint={H.previewBanner} ariaLabel="Ajuda: prévia" placement="bottom">
                  <span>
                    Prévia até a etapa selecionada. Clique seleciona/desseleciona; botão direito abre
                    ações.
                    {previewLoading ? " Atualizando…" : null}
                  </span>
                </HintAction>
                <HintAction hint={H.refresh} ariaLabel="Ajuda: atualizar prévia" placement="bottom">
                  <button
                    type="button"
                    className="td-btn td-btn--sm td-btn--ghost"
                    disabled={previewLoading}
                    onClick={() => requestServerPreview(true)}
                  >
                    Atualizar
                  </button>
                </HintAction>
              </div>
              {previewError ? (
                <p className="td-deck-inspector__hint" role="alert">
                  {previewError}
                </p>
              ) : null}
              <DataPrepareFormulaBar
                step={previewStepIndex != null ? (steps[previewStepIndex] ?? null) : null}
                newColumnDraft={newColumnDraft}
                columnHints={preview.columns}
                focusToken={formulaFocusToken}
                onCommit={commitFormulaStep}
                onCancelDraft={() => setNewColumnDraft(false)}
              />
              <div className="td-data-pq__grid-wrap">
                {!active ? (
                  <p className="td-deck-inspector__hint">
                    Nenhuma consulta selecionada. Clique numa consulta à esquerda.
                  </p>
                ) : preview.rows.length === 0 ? (
                  <p className="td-deck-inspector__hint">
                    Sem linhas. Atualize a fonte ou ajuste filtros / parâmetros da rota.
                  </p>
                ) : (
                  <table className="td-data-pq__grid">
                    <thead>
                      <tr>
                        <th className="td-data-pq__row-index">#</th>
                        {preview.columns.map((col) => {
                          const linked = seriesForColumn(linkedSeries, col);
                          const isActiveCol = activeColumn === col;
                          return (
                            <th
                              key={col}
                              data-pq-ctx="column"
                              className={[
                                linked ? "td-data-pq__col--series" : "",
                                isActiveCol ? "td-data-pq__col--active" : "",
                              ]
                                .filter(Boolean)
                                .join(" ") || undefined}
                              style={
                                linked?.color
                                  ? { boxShadow: `inset 0 -3px 0 ${linked.color}` }
                                  : undefined
                              }
                              aria-selected={isActiveCol}
                              onClick={(event) => {
                                event.stopPropagation();
                                toggleColumn(col);
                              }}
                              onContextMenu={(event) =>
                                openContextMenu(event, { kind: "column", name: col })
                              }
                            >
                              <HintAction
                                hint={H.columnHeader}
                                ariaLabel={`Ajuda: coluna ${col}`}
                                placement="bottom"
                                suppressed={Boolean(ctxMenu)}
                              >
                                <span className="td-data-pq__col-label">
                                  <span className="td-data-pq__col-type" aria-hidden>
                                    {linked ? "∑" : "ABC"}
                                  </span>
                                  {col}
                                </span>
                              </HintAction>
                            </th>
                          );
                        })}
                      </tr>
                    </thead>
                    <tbody>
                      {preview.rows.slice(0, 40).map((row, rowIndex) => (
                        <tr key={rowIndex}>
                          <td className="td-data-pq__row-index">{rowIndex + 1}</td>
                          {preview.columns.map((col) => (
                            <td
                              key={col}
                              className={
                                activeColumn === col
                                  ? "td-data-pq__cell--active"
                                  : undefined
                              }
                              onClick={(event) => {
                                event.stopPropagation();
                                toggleColumn(col);
                              }}
                              onContextMenu={(event) =>
                                openContextMenu(event, { kind: "column", name: col })
                              }
                            >
                              {row[col] == null ? "" : String(row[col])}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
              {preview.rows.length > 40 ? (
                <p className="td-deck-inspector__meta">
                  Mostrando 40 de {preview.rows.length} linhas
                </p>
              ) : null}
            </section>

            <aside className="td-data-pq__settings" aria-label="Configuração da consulta">
              <div className="td-data-pq__pane-title">
                <Settings2 size={14} aria-hidden />
                <SectionHintLabel label="Config. consulta" hint={H.settings} />
              </div>
              <div className="td-data-pq__props">
                <label className="td-data-pq__prop-label" htmlFor="td-pq-query-name">
                  Nome
                </label>
                <input
                  id="td-pq-query-name"
                  className="td-data-pq__prop-input"
                  readOnly
                  value={active ? queryLabel(active) : ""}
                />
                <p className="td-deck-inspector__meta">
                  {active?.dataBinding?.operationId
                    ? `Rota: ${active.dataBinding.operationId}`
                    : "Sem operationId"}
                </p>
                {activeColumn ? (
                  <p className="td-deck-inspector__meta">Coluna ativa: {activeColumn}</p>
                ) : null}
              </div>
              <div className="td-data-pq__steps-title">
                <SectionHintLabel label="Etapas aplicadas" hint={H.steps} />
              </div>
              <ol className="td-data-pq__steps">
                <li>
                  <HintAction hint={H.stepFonte} ariaLabel="Ajuda: etapa Fonte" placement="top">
                    <button
                      type="button"
                      data-pq-ctx="fonte"
                      className={
                        previewStepIndex == null
                          ? "td-data-pq__step td-data-pq__step--selected"
                          : "td-data-pq__step"
                      }
                      aria-pressed={previewStepIndex == null}
                      onClick={(event) => {
                        event.stopPropagation();
                        toggleStep(null);
                      }}
                      onContextMenu={(event) => openContextMenu(event, { kind: "fonte" })}
                    >
                      Fonte
                    </button>
                  </HintAction>
                </li>
                {steps.map((step, index) => {
                  const selectedStep = previewStepIndex === index;
                  return (
                    <li key={`${step.op}-${index}`}>
                      <div
                        data-pq-ctx="step"
                        className={
                          selectedStep
                            ? "td-data-pq__step td-data-pq__step--selected"
                            : "td-data-pq__step"
                        }
                        onContextMenu={(event) =>
                          openContextMenu(event, { kind: "step", index })
                        }
                      >
                        {selectedStep ? (
                          <HintAction
                            hint={H.stepDelete}
                            ariaLabel="Ajuda: remover etapa"
                            placement="top"
                          >
                            <button
                              type="button"
                              className="td-data-pq__step-x"
                              aria-label="Remover etapa"
                              onClick={(event) => {
                                event.stopPropagation();
                                removeStep(index);
                              }}
                            >
                              <X size={12} aria-hidden />
                            </button>
                          </HintAction>
                        ) : null}
                        <HintAction
                          hint={H.stepItem}
                          ariaLabel={`Ajuda: ${dataTransformStepLabel(step)}`}
                          placement="top"
                          suppressed={Boolean(ctxMenu)}
                        >
                          <button
                            type="button"
                            className="td-data-pq__step-main"
                            aria-pressed={selectedStep}
                            onClick={(event) => {
                              event.stopPropagation();
                              toggleStep(index);
                            }}
                          >
                            {dataTransformStepLabel(step)}
                          </button>
                        </HintAction>
                        <div className="td-data-pq__step-tools">
                          <HintAction
                            hint={H.stepEdit}
                            ariaLabel="Ajuda: editar etapa"
                            placement="top"
                          >
                            <button
                              type="button"
                              className="td-btn td-btn--sm td-btn--ghost"
                              aria-label="Editar etapa na barra fx"
                              onClick={(event) => {
                                event.stopPropagation();
                                focusFormulaForStep(index);
                              }}
                            >
                              <Pencil size={12} aria-hidden />
                            </button>
                          </HintAction>
                          <HintAction
                            hint={H.stepMoveUp}
                            ariaLabel="Ajuda: mover etapa para cima"
                            placement="top"
                          >
                            <button
                              type="button"
                              className="td-btn td-btn--sm td-btn--ghost"
                              aria-label="Mover para cima"
                              disabled={index === 0}
                              onClick={(event) => {
                                event.stopPropagation();
                                moveStep(index, -1);
                              }}
                            >
                              ↑
                            </button>
                          </HintAction>
                          <HintAction
                            hint={H.stepMoveDown}
                            ariaLabel="Ajuda: mover etapa para baixo"
                            placement="top"
                          >
                            <button
                              type="button"
                              className="td-btn td-btn--sm td-btn--ghost"
                              aria-label="Mover para baixo"
                              disabled={index === steps.length - 1}
                              onClick={(event) => {
                                event.stopPropagation();
                                moveStep(index, 1);
                              }}
                            >
                              ↓
                            </button>
                          </HintAction>
                          <HintAction
                            hint={H.stepDelete}
                            ariaLabel="Ajuda: excluir etapa"
                            placement="top"
                          >
                            <button
                              type="button"
                              className="td-btn td-btn--sm td-btn--ghost"
                              aria-label="Excluir etapa"
                              onClick={(event) => {
                                event.stopPropagation();
                                removeStep(index);
                              }}
                            >
                              <Trash2 size={12} aria-hidden />
                            </button>
                          </HintAction>
                        </div>
                      </div>
                    </li>
                  );
                })}
              </ol>
              {steps.length === 0 ? (
                <p className="td-deck-inspector__meta">
                  Nenhuma etapa — dados da API como vieram. Use a faixa acima para transformar.
                </p>
              ) : (
                <p className="td-deck-inspector__meta">
                  Clique na etapa para prévia; clique de novo desseleciona (Fonte). Botão direito:
                  menu.
                </p>
              )}
              <HintAction hint={H.newFxStep} ariaLabel="Ajuda: nova etapa fx" placement="top">
                <button
                  type="button"
                  className="td-btn td-btn--sm"
                  style={{ marginTop: 8 }}
                  disabled={!active}
                  onClick={startNewColumnFromFx}
                >
                  <Plus size={14} aria-hidden />
                  Nova etapa (fx)…
                </button>
              </HintAction>
            </aside>
          </div>

          <DataPrepareContextMenu
            open={Boolean(ctxMenu)}
            position={ctxMenu?.position ?? null}
            target={ctxMenu?.target ?? null}
            hasSteps={steps.length > 0}
            canMoveStepUp={
              ctxMenu?.target?.kind === "step" ? ctxMenu.target.index > 0 : false
            }
            canMoveStepDown={
              ctxMenu?.target?.kind === "step"
                ? ctxMenu.target.index < steps.length - 1
                : false
            }
            queryOperationId={active?.dataBinding?.operationId ?? null}
            onClose={() => setCtxMenu(null)}
            onRefresh={() => requestServerPreview(true)}
            onClearSteps={() => persistSteps([])}
            onCopyText={copyText}
            onEditStepFx={focusFormulaForStep}
            onMoveStep={moveStep}
            onDeleteStep={removeStep}
            onRenameColumn={(column) => {
              setActiveColumn(column);
              openRibbonAction({ tab: "transform", action: "rename" });
            }}
            onFilterColumn={(column) => {
              setActiveColumn(column);
              openRibbonAction({ tab: "transform", action: "filter" });
            }}
            onSortColumn={(column, direction) => {
              addStep({ op: "sort", column, direction });
            }}
            onRemoveColumn={(column) => {
              const next = preview.columns.filter((name) => name !== column);
              if (!next.length) return;
              addStep({ op: "select", columns: next });
              setActiveColumn("");
            }}
            onKeepOnlyColumn={(column) => {
              addStep({ op: "select", columns: [column] });
              setActiveColumn(column);
            }}
          />
        </div>
      )}
    </Modal>
  );
}

/** Compositor fino: rollout seguro legado ou workbench M conforme capability server-side. */
export function DataPrepareModal(props: Props) {
  const { capabilities } = useDataQueryCapabilities();
  return canUseMWorkbench(capabilities) ? (
    <DataQueryWorkbenchModal
      {...props}
      advancedEditorEnabled={canUseAdvancedMEditor(capabilities)}
      profilingEnabled={capabilities.profilingEnabled}
    />
  ) : (
    <LegacyDataPrepareModal {...props} />
  );
}
