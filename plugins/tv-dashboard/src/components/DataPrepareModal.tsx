import { FormSelectControl, NativeTextControl } from "@delpi/plugin-ui/index";
import {
  applyDataTransformSteps,
  coercePayloadToTable,
  isDataSourceBlockType,
  normalizeDataTransform,
  type ComunicadoDataSourceBlock,
  type DataTransform,
  type DataTransformCmp,
  type DataTransformStep,
} from "@delpi/tv-dashboard-presentation";
import {
  Columns3,
  Filter,
  FunctionSquare,
  Plus,
  RefreshCw,
  Settings2,
  Trash2,
  X,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { useComunicadoEditor } from "./comunicadoEditorContext";
import { Modal } from "./ui/Modal";

type Props = {
  open: boolean;
  onClose: () => void;
  /** Fonte inicial ao abrir. */
  initialSourceId?: string | null;
};

const CMP_OPTIONS: Array<{ value: DataTransformCmp; label: string }> = [
  { value: "eq", label: "igual a" },
  { value: "neq", label: "diferente de" },
  { value: "gt", label: "maior que" },
  { value: "lt", label: "menor que" },
  { value: "notNull", label: "não nulo" },
];

function queryLabel(block: ComunicadoDataSourceBlock): string {
  const label = block.dataBinding?.label?.trim();
  if (label) return label;
  const op = block.dataBinding?.operationId?.trim();
  if (op) return op;
  return `Fonte ${block.id.slice(0, 6)}`;
}

function stepLabel(step: DataTransformStep): string {
  switch (step.op) {
    case "rename":
      return `Renomear ${step.from} → ${step.to}`;
    case "select":
      return `Colunas: ${step.columns.join(", ")}`;
    case "filter":
      return `Filtrar ${step.column} ${step.cmp}${
        step.cmp === "notNull" ? "" : ` ${String(step.value ?? "")}`
      }`;
    case "addColumn":
      return `Coluna ${step.name} = ${step.expr}`;
    default:
      return "Etapa";
  }
}

function stepFormula(step: DataTransformStep): string {
  switch (step.op) {
    case "rename":
      return `= RenameColumns(Fonte, ${step.from} → ${step.to})`;
    case "select":
      return `= SelectColumns(Fonte, [${step.columns.join(", ")}])`;
    case "filter":
      return step.cmp === "notNull"
        ? `= FilterRows(Fonte, ${step.column} is not null)`
        : `= FilterRows(Fonte, [${step.column}] ${step.cmp} ${JSON.stringify(step.value ?? "")})`;
    case "addColumn":
      return `= AddColumn(Fonte, ${step.name}, ${step.expr})`;
    default:
      return "= Fonte";
  }
}

type RibbonTab = "home" | "transform" | "addColumn";

/**
 * Ambiente de preparação estilo Power Query — modal.
 * «Consultas» = fontes `data_source` (rotas api-delpi) do slide.
 */
export function DataPrepareModal({ open, onClose, initialSourceId = null }: Props) {
  const { blocks, updateBlock, refreshDataPreview } = useComunicadoEditor();
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
  const [draftRenameFrom, setDraftRenameFrom] = useState("");
  const [draftRenameTo, setDraftRenameTo] = useState("");
  const [draftFilterCol, setDraftFilterCol] = useState("");
  const [draftFilterCmp, setDraftFilterCmp] = useState<DataTransformCmp>("eq");
  const [draftFilterValue, setDraftFilterValue] = useState("");
  const [draftAddName, setDraftAddName] = useState("");
  const [draftAddExpr, setDraftAddExpr] = useState("");
  const [draftSelect, setDraftSelect] = useState("");

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
  }, [activeId, steps.length]);

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

  const stepsThroughPreview = useMemo(() => {
    if (previewStepIndex == null) return [];
    return steps.slice(0, previewStepIndex + 1);
  }, [previewStepIndex, steps]);

  const preview = useMemo(
    () => applyDataTransformSteps(baseTable, stepsThroughPreview),
    [baseTable, stepsThroughPreview],
  );

  const formula =
    previewStepIndex != null && steps[previewStepIndex]
      ? stepFormula(steps[previewStepIndex]!)
      : "= Fonte (rota api-delpi)";

  const persistSteps = (nextSteps: DataTransformStep[]) => {
    if (!active) return;
    const transform = normalizeDataTransform({ steps: nextSteps }) as DataTransform | undefined;
    updateBlock(active.id, { dataTransform: transform } as Partial<ComunicadoDataSourceBlock>);
  };

  const addStep = (step: DataTransformStep) => {
    persistSteps([...steps, step]);
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

  const columnOptions = preview.columns.map((col) => ({ value: col, label: col }));

  const handleCloseAndApply = () => {
    void refreshDataPreview({
      force: true,
      blockIds: active ? [active.id] : undefined,
    });
    onClose();
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
          <div className="td-data-pq__ribbon" role="toolbar" aria-label="Transformações">
            <div className="td-data-pq__ribbon-tabs">
              {(
                [
                  ["home", "Página Inicial"],
                  ["transform", "Transformar"],
                  ["addColumn", "Adicionar coluna"],
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
                    Atualizar visualização
                  </button>
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
                  <NativeTextControl
                    id="td-pq-select-cols"
                    className="td-data-pq__ribbon-input"
                    placeholder="col1, col2"
                    value={draftSelect}
                    onChange={setDraftSelect}
                    ariaLabel="Colunas a manter"
                  />
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
                    Filtrar linhas
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
                </>
              ) : null}
            </div>
          </div>

          <div className="td-data-pq__workspace">
            <aside className="td-data-pq__queries" aria-label="Consultas (rotas)">
              <div className="td-data-pq__pane-title">
                Consultas [{queries.length}]
              </div>
              <ul className="td-data-pq__query-list">
                {queries.map((query) => {
                  const selected = query.id === activeId;
                  return (
                    <li key={query.id}>
                      <button
                        type="button"
                        className={
                          selected
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
                  Prévia da rota após as etapas. Os visuais do slide usam o resultado ao aplicar.
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
                <code>{formula}</code>
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
                        {preview.columns.map((col) => (
                          <th key={col}>
                            <span className="td-data-pq__col-type" aria-hidden>
                              ABC
                            </span>
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {preview.rows.slice(0, 40).map((row, rowIndex) => (
                        <tr key={rowIndex}>
                          <td className="td-data-pq__row-index">{rowIndex + 1}</td>
                          {preview.columns.map((col) => (
                            <td key={col}>{row[col] == null ? "" : String(row[col])}</td>
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
                    onClick={() => setPreviewStepIndex(null)}
                  >
                    Fonte
                  </button>
                </li>
                {steps.map((step, index) => {
                  const selected = previewStepIndex === index;
                  return (
                    <li key={`${step.op}-${index}`}>
                      <div
                        className={
                          selected
                            ? "td-data-pq__step td-data-pq__step--selected"
                            : "td-data-pq__step"
                        }
                      >
                        {selected ? (
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
                          {stepLabel(step)}
                        </button>
                        <div className="td-data-pq__step-tools">
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
              ) : null}
              <button
                type="button"
                className="td-btn td-btn--sm"
                style={{ marginTop: 8 }}
                disabled={!active}
                onClick={() => {
                  setRibbonTab("addColumn");
                }}
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
