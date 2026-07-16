import { FormSelectControl, NativeTextControl } from "@delpi/plugin-ui/index";
import {
  applyDataTransformSteps,
  coercePayloadToTable,
  dataTransformStepFormula,
  dataTransformStepLabel,
  isDataSourceBlockType,
  normalizeDataTransform,
  type ComunicadoChartViewBlock,
  type ComunicadoDataSourceBlock,
  type DataTransform,
  type DataTransformAgg,
  type DataTransformCmp,
  type DataTransformStep,
} from "@delpi/tv-dashboard-presentation";
import {
  ArrowDownAZ,
  Columns3,
  Filter,
  FunctionSquare,
  GitMerge,
  Layers2,
  Pencil,
  Plus,
  RefreshCw,
  Replace,
  Settings2,
  Sparkles,
  Trash2,
  X,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import {
  listDataRoutes,
  type TvDataRouteCatalogItem,
} from "../api/tvDashboardApi";
import {
  columnForSelectedSeries,
  linkedChartSeriesForSource,
  seriesForColumn,
} from "../utils/dataPrepareCrossHighlight";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { Modal } from "./ui/Modal";

type Props = {
  open: boolean;
  onClose: () => void;
  initialSourceId?: string | null;
};

const CMP_OPTIONS: Array<{ value: DataTransformCmp; label: string }> = [
  { value: "eq", label: "igual a" },
  { value: "neq", label: "diferente de" },
  { value: "gt", label: "maior que" },
  { value: "lt", label: "menor que" },
  { value: "contains", label: "contém" },
  { value: "startsWith", label: "começa com" },
  { value: "notNull", label: "não nulo" },
];

const AGG_OPTIONS: Array<{ value: DataTransformAgg; label: string }> = [
  { value: "sum", label: "Soma" },
  { value: "avg", label: "Média" },
  { value: "min", label: "Mín" },
  { value: "max", label: "Máx" },
  { value: "count", label: "Contagem" },
  { value: "first", label: "Primeiro" },
];

function queryLabel(block: ComunicadoDataSourceBlock): string {
  const label = block.dataBinding?.label?.trim();
  if (label) return label;
  const op = block.dataBinding?.operationId?.trim();
  if (op) return op;
  return `Fonte ${block.id.slice(0, 6)}`;
}

type RibbonTab = "home" | "transform" | "addColumn" | "combine";

/**
 * Ambiente de preparação estilo Power Query — modal.
 * «Consultas» = fontes `data_source` (rotas api-delpi) do slide.
 */
export function DataPrepareModal({ open, onClose, initialSourceId = null }: Props) {
  const {
    blocks,
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
  const [editingStepIndex, setEditingStepIndex] = useState<number | null>(null);
  const [formulaDraft, setFormulaDraft] = useState("");
  const [routes, setRoutes] = useState<TvDataRouteCatalogItem[]>([]);

  const [draftRenameFrom, setDraftRenameFrom] = useState("");
  const [draftRenameTo, setDraftRenameTo] = useState("");
  const [draftFilterCol, setDraftFilterCol] = useState("");
  const [draftFilterCmp, setDraftFilterCmp] = useState<DataTransformCmp>("eq");
  const [draftFilterValue, setDraftFilterValue] = useState("");
  const [draftAddName, setDraftAddName] = useState("");
  const [draftAddExpr, setDraftAddExpr] = useState("");
  const [draftSelect, setDraftSelect] = useState("");
  const [draftReplaceCol, setDraftReplaceCol] = useState("");
  const [draftReplaceFind, setDraftReplaceFind] = useState("");
  const [draftReplaceWith, setDraftReplaceWith] = useState("");
  const [draftSortCol, setDraftSortCol] = useState("");
  const [draftSortDir, setDraftSortDir] = useState<"asc" | "desc">("asc");
  const [draftRowCount, setDraftRowCount] = useState("10");
  const [draftRowFrom, setDraftRowFrom] = useState<"top" | "bottom">("top");
  const [draftTypeCol, setDraftTypeCol] = useState("");
  const [draftTypeTo, setDraftTypeTo] = useState<"number" | "string">("number");
  const [draftFillCol, setDraftFillCol] = useState("");
  const [draftGroupKeys, setDraftGroupKeys] = useState("");
  const [draftGroupAggCol, setDraftGroupAggCol] = useState("");
  const [draftGroupAggFn, setDraftGroupAggFn] = useState<DataTransformAgg>("sum");
  const [draftGroupAggAs, setDraftGroupAggAs] = useState("");
  const [draftPivotCol, setDraftPivotCol] = useState("");
  const [draftPivotValue, setDraftPivotValue] = useState("");
  const [draftUnpivotCols, setDraftUnpivotCols] = useState("");
  const [draftMergeSource, setDraftMergeSource] = useState("");
  const [draftMergeLeft, setDraftMergeLeft] = useState("");
  const [draftMergeRight, setDraftMergeRight] = useState("");

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
  const steps = active?.dataTransform?.steps ?? [];

  useEffect(() => {
    setPreviewStepIndex(steps.length > 0 ? steps.length - 1 : null);
    setEditingStepIndex(null);
  }, [activeId, steps.length]);

  useEffect(() => {
    if (previewStepIndex == null || !steps[previewStepIndex]) {
      setFormulaDraft("");
      return;
    }
    const step = steps[previewStepIndex]!;
    if (step.op === "addColumn") {
      setFormulaDraft(step.expr);
      return;
    }
    setFormulaDraft(dataTransformStepFormula(step));
  }, [previewStepIndex, steps]);

  const baseTable = useMemo(() => {
    if (!active) return { columns: [] as string[], rows: [] as Array<Record<string, unknown>> };
    const fromResolved = coercePayloadToTable(active.resolved?.data);
    if (fromResolved?.rows.length) return fromResolved;
    if (active.resolved?.table?.rows?.length) {
      return {
        columns: (active.resolved.table.columns ?? []).map((col) => col.key),
        rows: active.resolved.table.rows.map((row) => ({ ...row })),
      };
    }
    return { columns: [] as string[], rows: [] as Array<Record<string, unknown>> };
  }, [active]);

  const siblingTables = useMemo(() => {
    const map: Record<string, { columns: string[]; rows: Array<Record<string, unknown>> }> = {};
    for (const query of queries) {
      if (query.id === activeId) continue;
      const table =
        coercePayloadToTable(query.resolved?.data) ??
        (query.resolved?.table?.rows?.length
          ? {
              columns: (query.resolved.table.columns ?? []).map((col) => col.key),
              rows: query.resolved.table.rows.map((row) => ({ ...row })),
            }
          : null);
      if (!table) continue;
      const qSteps = query.dataTransform?.steps;
      map[query.id] = qSteps?.length
        ? applyDataTransformSteps(table, qSteps)
        : table;
    }
    return map;
  }, [queries, activeId]);

  const stepsThroughPreview = useMemo(() => {
    if (previewStepIndex == null) return [];
    return steps.slice(0, previewStepIndex + 1);
  }, [previewStepIndex, steps]);

  const preview = useMemo(
    () => applyDataTransformSteps(baseTable, stepsThroughPreview, { siblingTables }),
    [baseTable, stepsThroughPreview, siblingTables],
  );

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
    setEditingStepIndex(null);
  };

  const moveStep = (index: number, delta: number) => {
    const target = index + delta;
    if (target < 0 || target >= steps.length) return;
    const next = [...steps];
    const [item] = next.splice(index, 1);
    next.splice(target, 0, item!);
    persistSteps(next);
  };

  const applyFormulaEdit = () => {
    if (previewStepIndex == null) return;
    const step = steps[previewStepIndex];
    if (!step || step.op !== "addColumn") return;
    const expr = formulaDraft.trim();
    if (!expr || expr === step.expr) return;
    replaceStep(previewStepIndex, { ...step, expr });
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

  const editingStep = editingStepIndex != null ? steps[editingStepIndex] : null;

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
          <div className="td-data-pq__ribbon" role="toolbar" aria-label="Transformações">
            <div className="td-data-pq__ribbon-tabs">
              {(
                [
                  ["home", "Página Inicial"],
                  ["transform", "Transformar"],
                  ["addColumn", "Adicionar coluna"],
                  ["combine", "Combinar"],
                ] as const
              ).map(([id, label]) => (
                <button
                  key={id}
                  type="button"
                  className={
                    ribbonTab === id
                      ? "td-data-pq__ribbon-tab td-data-pq__ribbon-tab--active"
                      : "td-data-pq__ribbon-tab"
                  }
                  onClick={() => setRibbonTab(id)}
                >
                  {label}
                </button>
              ))}
            </div>
            <div className="td-data-pq__ribbon-body">
              {ribbonTab === "home" ? (
                <>
                  <button
                    type="button"
                    className="td-data-pq__ribbon-action"
                    disabled={!active}
                    onClick={() =>
                      void refreshDataPreview({
                        force: true,
                        blockIds: active ? [active.id] : undefined,
                      })
                    }
                  >
                    <RefreshCw size={16} aria-hidden />
                    Atualizar
                  </button>
                  <NativeTextControl
                    id="td-pq-select-cols"
                    className="td-data-pq__ribbon-input"
                    placeholder="col1, col2"
                    value={draftSelect}
                    onChange={setDraftSelect}
                    aria-label="Colunas a manter"
                  />
                  <button
                    type="button"
                    className="td-data-pq__ribbon-action"
                    disabled={!active || !draftSelect.trim()}
                    onClick={() => {
                      const columns = draftSelect
                        .split(",")
                        .map((item) => item.trim())
                        .filter(Boolean);
                      if (!columns.length) return;
                      addStep({ op: "select", columns });
                      setDraftSelect("");
                    }}
                  >
                    <Columns3 size={16} aria-hidden />
                    Escolher colunas
                  </button>
                  <button
                    type="button"
                    className="td-data-pq__ribbon-action"
                    disabled={!active}
                    onClick={() => addStep({ op: "firstRowAsHeader" })}
                  >
                    Usar 1ª linha como cabeçalho
                  </button>
                  {routePreset?.suggestedTransformSteps?.length ? (
                    <button
                      type="button"
                      className="td-data-pq__ribbon-action"
                      onClick={applySuggestedPreset}
                    >
                      <Sparkles size={16} aria-hidden />
                      Preset da rota
                    </button>
                  ) : null}
                </>
              ) : null}
              {ribbonTab === "transform" ? (
                <>
                  <FormSelectControl
                    id="td-pq-rename-from"
                    ariaLabel="Coluna a renomear"
                    value={draftRenameFrom}
                    onChange={setDraftRenameFrom}
                    options={[{ value: "", label: "Coluna…" }, ...columnOptions]}
                  />
                  <NativeTextControl
                    id="td-pq-rename-to"
                    className="td-data-pq__ribbon-input"
                    placeholder="Novo nome"
                    value={draftRenameTo}
                    onChange={setDraftRenameTo}
                  />
                  <button
                    type="button"
                    className="td-data-pq__ribbon-action"
                    disabled={!draftRenameFrom.trim() || !draftRenameTo.trim()}
                    onClick={() => {
                      addStep({
                        op: "rename",
                        from: draftRenameFrom.trim(),
                        to: draftRenameTo.trim(),
                      });
                      setDraftRenameFrom("");
                      setDraftRenameTo("");
                    }}
                  >
                    Renomear
                  </button>
                  <FormSelectControl
                    id="td-pq-filter-col"
                    ariaLabel="Coluna filtro"
                    value={draftFilterCol}
                    onChange={setDraftFilterCol}
                    options={[{ value: "", label: "Coluna…" }, ...columnOptions]}
                  />
                  <FormSelectControl
                    id="td-pq-filter-cmp"
                    ariaLabel="Comparação"
                    value={draftFilterCmp}
                    onChange={(value) => setDraftFilterCmp(value as DataTransformCmp)}
                    options={CMP_OPTIONS}
                  />
                  {draftFilterCmp !== "notNull" ? (
                    <NativeTextControl
                      id="td-pq-filter-value"
                      className="td-data-pq__ribbon-input"
                      placeholder="Valor"
                      value={draftFilterValue}
                      onChange={setDraftFilterValue}
                    />
                  ) : null}
                  <button
                    type="button"
                    className="td-data-pq__ribbon-action"
                    disabled={!draftFilterCol.trim()}
                    onClick={() => {
                      addStep({
                        op: "filter",
                        column: draftFilterCol.trim(),
                        cmp: draftFilterCmp,
                        ...(draftFilterCmp === "notNull" ? {} : { value: draftFilterValue }),
                      });
                      setDraftFilterCol("");
                      setDraftFilterValue("");
                    }}
                  >
                    <Filter size={16} aria-hidden />
                    Filtrar
                  </button>
                  <FormSelectControl
                    id="td-pq-replace-col"
                    ariaLabel="Coluna substituir"
                    value={draftReplaceCol}
                    onChange={setDraftReplaceCol}
                    options={[{ value: "", label: "Coluna…" }, ...columnOptions]}
                  />
                  <NativeTextControl
                    id="td-pq-replace-find"
                    className="td-data-pq__ribbon-input"
                    placeholder="Localizar"
                    value={draftReplaceFind}
                    onChange={setDraftReplaceFind}
                  />
                  <NativeTextControl
                    id="td-pq-replace-with"
                    className="td-data-pq__ribbon-input"
                    placeholder="Substituir por"
                    value={draftReplaceWith}
                    onChange={setDraftReplaceWith}
                  />
                  <button
                    type="button"
                    className="td-data-pq__ribbon-action"
                    disabled={!draftReplaceCol.trim()}
                    onClick={() => {
                      addStep({
                        op: "replace",
                        column: draftReplaceCol.trim(),
                        find: draftReplaceFind,
                        replaceWith: draftReplaceWith,
                      });
                      setDraftReplaceCol("");
                      setDraftReplaceFind("");
                      setDraftReplaceWith("");
                    }}
                  >
                    <Replace size={16} aria-hidden />
                    Substituir
                  </button>
                  <FormSelectControl
                    id="td-pq-sort-col"
                    ariaLabel="Ordenar coluna"
                    value={draftSortCol}
                    onChange={setDraftSortCol}
                    options={[{ value: "", label: "Coluna…" }, ...columnOptions]}
                  />
                  <FormSelectControl
                    id="td-pq-sort-dir"
                    ariaLabel="Direção"
                    value={draftSortDir}
                    onChange={(value) => setDraftSortDir(value === "desc" ? "desc" : "asc")}
                    options={[
                      { value: "asc", label: "A→Z" },
                      { value: "desc", label: "Z→A" },
                    ]}
                  />
                  <button
                    type="button"
                    className="td-data-pq__ribbon-action"
                    disabled={!draftSortCol.trim()}
                    onClick={() => {
                      addStep({
                        op: "sort",
                        column: draftSortCol.trim(),
                        direction: draftSortDir,
                      });
                      setDraftSortCol("");
                    }}
                  >
                    <ArrowDownAZ size={16} aria-hidden />
                    Ordenar
                  </button>
                  <NativeTextControl
                    id="td-pq-row-count"
                    className="td-data-pq__ribbon-input"
                    placeholder="N linhas"
                    value={draftRowCount}
                    onChange={setDraftRowCount}
                  />
                  <FormSelectControl
                    id="td-pq-row-from"
                    ariaLabel="Topo ou base"
                    value={draftRowFrom}
                    onChange={(value) => setDraftRowFrom(value === "bottom" ? "bottom" : "top")}
                    options={[
                      { value: "top", label: "Do topo" },
                      { value: "bottom", label: "Da base" },
                    ]}
                  />
                  <button
                    type="button"
                    className="td-data-pq__ribbon-action"
                    onClick={() => {
                      const count = Math.max(0, Math.floor(Number(draftRowCount) || 0));
                      if (!count) return;
                      addStep({ op: "keepRows", count, from: draftRowFrom });
                    }}
                  >
                    Manter linhas
                  </button>
                  <button
                    type="button"
                    className="td-data-pq__ribbon-action"
                    onClick={() => {
                      const count = Math.max(0, Math.floor(Number(draftRowCount) || 0));
                      if (!count) return;
                      addStep({ op: "removeRows", count, from: draftRowFrom });
                    }}
                  >
                    Remover linhas
                  </button>
                  <FormSelectControl
                    id="td-pq-type-col"
                    ariaLabel="Coluna tipo"
                    value={draftTypeCol}
                    onChange={setDraftTypeCol}
                    options={[{ value: "", label: "Coluna…" }, ...columnOptions]}
                  />
                  <FormSelectControl
                    id="td-pq-type-to"
                    ariaLabel="Tipo destino"
                    value={draftTypeTo}
                    onChange={(value) => setDraftTypeTo(value === "string" ? "string" : "number")}
                    options={[
                      { value: "number", label: "Número" },
                      { value: "string", label: "Texto" },
                    ]}
                  />
                  <button
                    type="button"
                    className="td-data-pq__ribbon-action"
                    disabled={!draftTypeCol.trim()}
                    onClick={() => {
                      addStep({
                        op: "changeType",
                        column: draftTypeCol.trim(),
                        to: draftTypeTo,
                      });
                      setDraftTypeCol("");
                    }}
                  >
                    Alterar tipo
                  </button>
                  <FormSelectControl
                    id="td-pq-fill-col"
                    ariaLabel="Preencher abaixo"
                    value={draftFillCol}
                    onChange={setDraftFillCol}
                    options={[{ value: "", label: "Coluna…" }, ...columnOptions]}
                  />
                  <button
                    type="button"
                    className="td-data-pq__ribbon-action"
                    disabled={!draftFillCol.trim()}
                    onClick={() => {
                      addStep({ op: "fillDown", column: draftFillCol.trim() });
                      setDraftFillCol("");
                    }}
                  >
                    Preencher abaixo
                  </button>
                </>
              ) : null}
              {ribbonTab === "addColumn" ? (
                <>
                  <NativeTextControl
                    id="td-pq-add-name"
                    className="td-data-pq__ribbon-input"
                    placeholder="Nome da coluna"
                    value={draftAddName}
                    onChange={setDraftAddName}
                  />
                  <NativeTextControl
                    id="td-pq-add-expr"
                    className="td-data-pq__ribbon-input td-data-pq__ribbon-input--wide"
                    placeholder="ex.: meta - oee"
                    value={draftAddExpr}
                    onChange={setDraftAddExpr}
                  />
                  <button
                    type="button"
                    className="td-data-pq__ribbon-action"
                    disabled={!draftAddName.trim() || !draftAddExpr.trim()}
                    onClick={() => {
                      addStep({
                        op: "addColumn",
                        name: draftAddName.trim(),
                        expr: draftAddExpr.trim(),
                      });
                      setDraftAddName("");
                      setDraftAddExpr("");
                    }}
                  >
                    <FunctionSquare size={16} aria-hidden />
                    Coluna personalizada
                  </button>
                  <NativeTextControl
                    id="td-pq-group-keys"
                    className="td-data-pq__ribbon-input"
                    placeholder="chaves (a, b)"
                    value={draftGroupKeys}
                    onChange={setDraftGroupKeys}
                  />
                  <FormSelectControl
                    id="td-pq-group-agg-col"
                    ariaLabel="Coluna agregação"
                    value={draftGroupAggCol}
                    onChange={setDraftGroupAggCol}
                    options={[{ value: "", label: "Agregar…" }, ...columnOptions]}
                  />
                  <FormSelectControl
                    id="td-pq-group-agg-fn"
                    ariaLabel="Função"
                    value={draftGroupAggFn}
                    onChange={(value) => setDraftGroupAggFn(value as DataTransformAgg)}
                    options={AGG_OPTIONS}
                  />
                  <NativeTextControl
                    id="td-pq-group-agg-as"
                    className="td-data-pq__ribbon-input"
                    placeholder="Nome resultado"
                    value={draftGroupAggAs}
                    onChange={setDraftGroupAggAs}
                  />
                  <button
                    type="button"
                    className="td-data-pq__ribbon-action"
                    disabled={!draftGroupKeys.trim() || !draftGroupAggCol.trim()}
                    onClick={() => {
                      const keys = draftGroupKeys
                        .split(",")
                        .map((item) => item.trim())
                        .filter(Boolean);
                      const column = draftGroupAggCol.trim();
                      if (!keys.length || !column) return;
                      const asName =
                        draftGroupAggAs.trim() || `${column}_${draftGroupAggFn}`;
                      addStep({
                        op: "groupBy",
                        keys,
                        aggregations: [{ column, fn: draftGroupAggFn, as: asName }],
                      });
                      setDraftGroupKeys("");
                      setDraftGroupAggCol("");
                      setDraftGroupAggAs("");
                    }}
                  >
                    <Layers2 size={16} aria-hidden />
                    Agrupar por
                  </button>
                  <FormSelectControl
                    id="td-pq-pivot-col"
                    ariaLabel="Coluna pivot"
                    value={draftPivotCol}
                    onChange={setDraftPivotCol}
                    options={[{ value: "", label: "Pivot…" }, ...columnOptions]}
                  />
                  <FormSelectControl
                    id="td-pq-pivot-value"
                    ariaLabel="Valores pivot"
                    value={draftPivotValue}
                    onChange={setDraftPivotValue}
                    options={[{ value: "", label: "Valores…" }, ...columnOptions]}
                  />
                  <button
                    type="button"
                    className="td-data-pq__ribbon-action"
                    disabled={!draftPivotCol.trim() || !draftPivotValue.trim()}
                    onClick={() => {
                      addStep({
                        op: "pivot",
                        column: draftPivotCol.trim(),
                        valueColumn: draftPivotValue.trim(),
                        aggregation: "sum",
                      });
                      setDraftPivotCol("");
                      setDraftPivotValue("");
                    }}
                  >
                    Pivot
                  </button>
                  <NativeTextControl
                    id="td-pq-unpivot"
                    className="td-data-pq__ribbon-input td-data-pq__ribbon-input--wide"
                    placeholder="colunas unpivot (a, b)"
                    value={draftUnpivotCols}
                    onChange={setDraftUnpivotCols}
                  />
                  <button
                    type="button"
                    className="td-data-pq__ribbon-action"
                    disabled={!draftUnpivotCols.trim()}
                    onClick={() => {
                      const columns = draftUnpivotCols
                        .split(",")
                        .map((item) => item.trim())
                        .filter(Boolean);
                      if (!columns.length) return;
                      addStep({ op: "unpivot", columns });
                      setDraftUnpivotCols("");
                    }}
                  >
                    Unpivot
                  </button>
                </>
              ) : null}
              {ribbonTab === "combine" ? (
                <>
                  <FormSelectControl
                    id="td-pq-merge-source"
                    ariaLabel="Consulta a mesclar"
                    value={draftMergeSource}
                    onChange={setDraftMergeSource}
                    options={[{ value: "", label: "Consulta…" }, ...siblingOptions]}
                  />
                  <FormSelectControl
                    id="td-pq-merge-left"
                    ariaLabel="Chave esquerda"
                    value={draftMergeLeft}
                    onChange={setDraftMergeLeft}
                    options={[{ value: "", label: "Chave esq…" }, ...columnOptions]}
                  />
                  <NativeTextControl
                    id="td-pq-merge-right"
                    className="td-data-pq__ribbon-input"
                    placeholder="Chave direita"
                    value={draftMergeRight}
                    onChange={setDraftMergeRight}
                  />
                  <button
                    type="button"
                    className="td-data-pq__ribbon-action"
                    disabled={
                      !draftMergeSource.trim() ||
                      !draftMergeLeft.trim() ||
                      !draftMergeRight.trim()
                    }
                    onClick={() => {
                      addStep({
                        op: "merge",
                        sourceId: draftMergeSource.trim(),
                        leftKey: draftMergeLeft.trim(),
                        rightKey: draftMergeRight.trim(),
                        join: "left",
                      });
                      setDraftMergeSource("");
                      setDraftMergeLeft("");
                      setDraftMergeRight("");
                    }}
                  >
                    <GitMerge size={16} aria-hidden />
                    Mesclar consultas
                  </button>
                  {!siblingOptions.length ? (
                    <span className="td-deck-inspector__meta">
                      Inclua outra fonte no slide para mesclar.
                    </span>
                  ) : null}
                </>
              ) : null}
            </div>
          </div>

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
                  Prévia da rota após as etapas. Clique numa coluna ligada ao gráfico para
                  selecionar a série.
                </span>
                <button
                  type="button"
                  className="td-btn td-btn--sm td-btn--ghost"
                  onClick={() =>
                    void refreshDataPreview({
                      force: true,
                      blockIds: active ? [active.id] : undefined,
                    })
                  }
                >
                  Atualizar
                </button>
              </div>
              <div className="td-data-pq__formula" aria-label="Barra de fórmula">
                <span className="td-data-pq__fx" aria-hidden>
                  fx
                </span>
                {previewStepIndex != null && steps[previewStepIndex]?.op === "addColumn" ? (
                  <input
                    className="td-data-pq__formula-input"
                    value={formulaDraft}
                    onChange={(event) => setFormulaDraft(event.target.value)}
                    onBlur={applyFormulaEdit}
                    onKeyDown={(event) => {
                      if (event.key === "Enter") {
                        event.preventDefault();
                        applyFormulaEdit();
                      }
                    }}
                    aria-label="Expressão da coluna"
                  />
                ) : (
                  <code>{formulaDraft || "= Fonte (rota api-delpi)"}</code>
                )}
              </div>
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
                          const isHl = highlightedColumn === col;
                          return (
                            <th
                              key={col}
                              className={
                                isHl
                                  ? "td-data-pq__col--series td-data-pq__col--active"
                                  : linked
                                    ? "td-data-pq__col--series"
                                    : undefined
                              }
                              style={
                                linked?.color
                                  ? { boxShadow: `inset 0 -3px 0 ${linked.color}` }
                                  : undefined
                              }
                              title={
                                linked
                                  ? `Série «${linked.label}» — clique para selecionar`
                                  : col
                              }
                              onClick={() => {
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
                                highlightedColumn === col ? "td-data-pq__cell--active" : undefined
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
                    onClick={() => {
                      setPreviewStepIndex(null);
                      setEditingStepIndex(null);
                    }}
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
                          onClick={() => {
                            setPreviewStepIndex(index);
                            setEditingStepIndex(null);
                          }}
                        >
                          {dataTransformStepLabel(step)}
                        </button>
                        <div className="td-data-pq__step-tools">
                          <button
                            type="button"
                            className="td-btn td-btn--sm td-btn--ghost"
                            aria-label="Editar etapa"
                            onClick={() => {
                              setPreviewStepIndex(index);
                              setEditingStepIndex(index);
                              if (step.op === "addColumn") {
                                setDraftAddName(step.name);
                                setDraftAddExpr(step.expr);
                                setRibbonTab("addColumn");
                              } else if (step.op === "rename") {
                                setDraftRenameFrom(step.from);
                                setDraftRenameTo(step.to);
                                setRibbonTab("transform");
                              } else if (step.op === "filter") {
                                setDraftFilterCol(step.column);
                                setDraftFilterCmp(step.cmp);
                                setDraftFilterValue(String(step.value ?? ""));
                                setRibbonTab("transform");
                              } else if (step.op === "merge") {
                                setDraftMergeSource(step.sourceId);
                                setDraftMergeLeft(step.leftKey);
                                setDraftMergeRight(step.rightKey);
                                setRibbonTab("combine");
                              } else {
                                setRibbonTab("transform");
                              }
                            }}
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
              {editingStep && editingStepIndex != null ? (
                <div className="td-data-pq__edit-step">
                  <p className="td-deck-inspector__meta">
                    Editando etapa {editingStepIndex + 1}: {dataTransformStepLabel(editingStep)}
                  </p>
                  {editingStep.op === "addColumn" ? (
                    <button
                      type="button"
                      className="td-btn td-btn--sm"
                      onClick={() => {
                        if (!draftAddName.trim() || !draftAddExpr.trim()) return;
                        replaceStep(editingStepIndex, {
                          op: "addColumn",
                          name: draftAddName.trim(),
                          expr: draftAddExpr.trim(),
                        });
                        setEditingStepIndex(null);
                      }}
                    >
                      Salvar coluna
                    </button>
                  ) : editingStep.op === "rename" ? (
                    <button
                      type="button"
                      className="td-btn td-btn--sm"
                      onClick={() => {
                        if (!draftRenameFrom.trim() || !draftRenameTo.trim()) return;
                        replaceStep(editingStepIndex, {
                          op: "rename",
                          from: draftRenameFrom.trim(),
                          to: draftRenameTo.trim(),
                        });
                        setEditingStepIndex(null);
                      }}
                    >
                      Salvar renomear
                    </button>
                  ) : editingStep.op === "filter" ? (
                    <button
                      type="button"
                      className="td-btn td-btn--sm"
                      onClick={() => {
                        if (!draftFilterCol.trim()) return;
                        replaceStep(editingStepIndex, {
                          op: "filter",
                          column: draftFilterCol.trim(),
                          cmp: draftFilterCmp,
                          ...(draftFilterCmp === "notNull"
                            ? {}
                            : { value: draftFilterValue }),
                        });
                        setEditingStepIndex(null);
                      }}
                    >
                      Salvar filtro
                    </button>
                  ) : editingStep.op === "merge" ? (
                    <button
                      type="button"
                      className="td-btn td-btn--sm"
                      onClick={() => {
                        if (
                          !draftMergeSource.trim() ||
                          !draftMergeLeft.trim() ||
                          !draftMergeRight.trim()
                        ) {
                          return;
                        }
                        replaceStep(editingStepIndex, {
                          op: "merge",
                          sourceId: draftMergeSource.trim(),
                          leftKey: draftMergeLeft.trim(),
                          rightKey: draftMergeRight.trim(),
                          join: "left",
                        });
                        setEditingStepIndex(null);
                      }}
                    >
                      Salvar mescla
                    </button>
                  ) : (
                    <p className="td-deck-inspector__meta">
                      Remova e recrie a etapa para tipos sem formulário de edição.
                    </p>
                  )}
                </div>
              ) : null}
              {steps.length === 0 ? (
                <p className="td-deck-inspector__meta">
                  Nenhuma etapa — dados da API como vieram. Use a faixa acima para transformar.
                </p>
              ) : null}
              <button
                type="button"
                className="td-btn td-btn--sm"
                style={{ marginTop: 8 }}
                disabled={!active}
                onClick={() => setRibbonTab("addColumn")}
              >
                <Plus size={14} aria-hidden />
                Nova etapa…
              </button>
            </aside>
          </div>
        </div>
      )}
    </Modal>
  );
}
