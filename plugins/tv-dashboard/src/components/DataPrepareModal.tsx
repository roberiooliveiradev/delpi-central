import {
  dataTransformStepLabel,
  isDataSourceBlockType,
  normalizeDataTransform,
  type ComunicadoChartViewBlock,
  type ComunicadoDataSourceBlock,
  type DataTransform,
  type DataTransformStep,
} from "@delpi/tv-dashboard-presentation";
import {
  Columns3,
  Pencil,
  Plus,
  Settings2,
  Trash2,
  X,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import {
  listDataRoutes,
  type TvDataRouteCatalogItem,
} from "../api/tvDashboardApi";
import {
  columnForSelectedSeries,
  linkedChartSeriesForSource,
  seriesForColumn,
} from "../utils/dataPrepareCrossHighlight";
import {
  previewTransformTableOnServer,
  type ServerTransformTable,
} from "../utils/previewTransformTableOnServer";
import { DataPrepareFormulaBar } from "./DataPrepareFormulaBar";
import {
  DataPrepareRibbon,
  type RibbonTab,
} from "./DataPrepareRibbon";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { Modal } from "./ui/Modal";

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
 * «Consultas» = fontes `data_source` (rotas api-delpi) do slide.
 * Cálculo dos steps: sempre no backend (`preview-block` / enrichment).
 */
export function DataPrepareModal({ open, onClose, initialSourceId = null }: Props) {
  const {
    blocks,
    config,
    playlistId,
    updateBlock,
    refreshDataPreview,
    selected,
    selectedChartPart,
    selectChartPart,
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
    if (!open) return;
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
  const steps = active?.dataTransform?.steps ?? EMPTY_STEPS;

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

  const highlightedColumn = useMemo(() => {
    if (!selected || selected.type !== "chart_view" || !selectedChartPart) return null;
    if (selectedChartPart.kind !== "series") return null;
    const chart = selected as ComunicadoChartViewBlock;
    if (String(chart.dataSourceId || "").trim() !== String(activeId || "").trim()) return null;
    return columnForSelectedSeries(linkedSeries, chart.id, selectedChartPart.seriesIndex);
  }, [selected, selectedChartPart, linkedSeries, activeId]);

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
    if (!normalized?.steps.length) return;
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

  return (
    <Modal
      open={open}
      title="Preparar dados"
      onClose={onClose}
      className="td-modal--data-prepare"
      footer={
        <div className="td-data-pq__footer">
          <button type="button" className="td-btn td-btn--sm td-btn--ghost" onClick={onClose}>
            Cancelar
          </button>
          <button type="button" className="td-btn td-btn--sm" onClick={handleCloseAndApply}>
            Fechar e aplicar
          </button>
        </div>
      }
    >
      {queries.length === 0 ? (
        <p className="td-deck-inspector__hint">
          Nenhuma fonte no slide. Insira uma rota api-delpi (fonte de dados) para preparar a tabela.
        </p>
      ) : (
        <div className="td-data-pq">
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
          />

          <div className="td-data-pq__workspace">
            <aside className="td-data-pq__queries" aria-label="Consultas (rotas)">
              <div className="td-data-pq__pane-title">Consultas [{queries.length}]</div>
              <ul className="td-data-pq__query-list">
                {queries.map((query) => {
                  const selectedQuery = query.id === activeId;
                  return (
                    <li key={query.id}>
                      <button
                        type="button"
                        className={
                          selectedQuery
                            ? "td-data-pq__query td-data-pq__query--selected"
                            : "td-data-pq__query"
                        }
                        onClick={() => setActiveId(query.id)}
                      >
                        <Columns3 size={14} aria-hidden />
                        <span className="td-data-pq__query-label">{queryLabel(query)}</span>
                        <span className="td-data-pq__query-meta">
                          {query.dataBinding?.operationId || "rota"}
                        </span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            </aside>

            <section className="td-data-pq__main" aria-label="Prévia">
              <div className="td-data-pq__banner">
                <span>
                  Prévia até a etapa selecionada (servidor). Clique no cabeçalho para coluna ativa;
                  coluna ligada ao gráfico também seleciona a série.
                  {previewLoading ? " Atualizando…" : null}
                </span>
                <button
                  type="button"
                  className="td-btn td-btn--sm td-btn--ghost"
                  disabled={previewLoading}
                  onClick={() => requestServerPreview(true)}
                >
                  Atualizar
                </button>
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
                  <p className="td-deck-inspector__hint">Selecione uma consulta à esquerda.</p>
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
                          const isSeriesHl = highlightedColumn === col;
                          const isActiveCol = activeColumn === col;
                          return (
                            <th
                              key={col}
                              className={[
                                linked ? "td-data-pq__col--series" : "",
                                isSeriesHl || isActiveCol ? "td-data-pq__col--active" : "",
                              ]
                                .filter(Boolean)
                                .join(" ") || undefined}
                              style={
                                linked?.color
                                  ? { boxShadow: `inset 0 -3px 0 ${linked.color}` }
                                  : undefined
                              }
                              title={
                                linked
                                  ? `Coluna ativa · série «${linked.label}»`
                                  : `Coluna ativa: ${col}`
                              }
                              onClick={() => {
                                setActiveColumn(col);
                                if (!linked) return;
                                selectChartPart(linked.chartId, {
                                  kind: "series",
                                  seriesIndex: linked.seriesIndex,
                                });
                              }}
                            >
                              <span className="td-data-pq__col-type" aria-hidden>
                                {linked ? "∑" : "ABC"}
                              </span>
                              {col}
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
                                highlightedColumn === col || activeColumn === col
                                  ? "td-data-pq__cell--active"
                                  : undefined
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
                Config. consulta
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
              <div className="td-data-pq__steps-title">Etapas aplicadas</div>
              <ol className="td-data-pq__steps">
                <li>
                  <button
                    type="button"
                    className={
                      previewStepIndex == null
                        ? "td-data-pq__step td-data-pq__step--selected"
                        : "td-data-pq__step"
                    }
                    onClick={() => setPreviewStepIndex(null)}
                  >
                    Fonte
                  </button>
                </li>
                {steps.map((step, index) => {
                  const selectedStep = previewStepIndex === index;
                  return (
                    <li key={`${step.op}-${index}`}>
                      <div
                        className={
                          selectedStep
                            ? "td-data-pq__step td-data-pq__step--selected"
                            : "td-data-pq__step"
                        }
                      >
                        {selectedStep ? (
                          <button
                            type="button"
                            className="td-data-pq__step-x"
                            aria-label="Remover etapa"
                            onClick={() => removeStep(index)}
                          >
                            <X size={12} aria-hidden />
                          </button>
                        ) : null}
                        <button
                          type="button"
                          className="td-data-pq__step-main"
                          onClick={() => setPreviewStepIndex(index)}
                        >
                          {dataTransformStepLabel(step)}
                        </button>
                        <div className="td-data-pq__step-tools">
                          <button
                            type="button"
                            className="td-btn td-btn--sm td-btn--ghost"
                            aria-label="Editar etapa na barra fx"
                            onClick={() => focusFormulaForStep(index)}
                          >
                            <Pencil size={12} aria-hidden />
                          </button>
                          <button
                            type="button"
                            className="td-btn td-btn--sm td-btn--ghost"
                            aria-label="Mover para cima"
                            disabled={index === 0}
                            onClick={() => moveStep(index, -1)}
                          >
                            ↑
                          </button>
                          <button
                            type="button"
                            className="td-btn td-btn--sm td-btn--ghost"
                            aria-label="Mover para baixo"
                            disabled={index === steps.length - 1}
                            onClick={() => moveStep(index, 1)}
                          >
                            ↓
                          </button>
                          <button
                            type="button"
                            className="td-btn td-btn--sm td-btn--ghost"
                            aria-label="Excluir etapa"
                            onClick={() => removeStep(index)}
                          >
                            <Trash2 size={12} aria-hidden />
                          </button>
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
                  Selecione a etapa para ver a prévia até ali. Lápis foca a barra fx (✓ aplica).
                </p>
              )}
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
            </aside>
          </div>
        </div>
      )}
    </Modal>
  );
}
