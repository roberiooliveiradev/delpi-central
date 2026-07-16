import { FormSelectControl, NativeTextControl } from "@delpi/plugin-ui/index";
import {
  applyDataTransformSteps,
  coercePayloadToTable,
  normalizeDataTransform,
  type ComunicadoDataSourceBlock,
  type DataTransform,
  type DataTransformCmp,
  type DataTransformStep,
} from "@delpi/tv-dashboard-presentation";
import { Plus, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DeckField } from "./deck/DeckField";
import { DeckPropertySection } from "./deck/DeckPropertySection";

type Props = {
  pane?: boolean;
  block: ComunicadoDataSourceBlock;
};

const CMP_OPTIONS: Array<{ value: DataTransformCmp; label: string }> = [
  { value: "eq", label: "igual a" },
  { value: "neq", label: "diferente de" },
  { value: "gt", label: "maior que" },
  { value: "lt", label: "menor que" },
  { value: "notNull", label: "não nulo" },
];

function stepLabel(step: DataTransformStep): string {
  switch (step.op) {
    case "rename":
      return `Renomear ${step.from} → ${step.to}`;
    case "select":
      return `Colunas: ${step.columns.join(", ")}`;
    case "filter":
      return `Filtrar ${step.column} ${step.cmp}${step.cmp === "notNull" ? "" : ` ${String(step.value ?? "")}`}`;
    case "addColumn":
      return `Coluna ${step.name} = ${step.expr}`;
    default:
      return "Step";
  }
}

/**
 * Ambiente tipo Power Query (MVP): preview tabular + Applied Steps na fonte.
 */
export function DataPreparePanel({ pane = false, block }: Props) {
  const { selected, updateSelected, updateBlock } = useComunicadoEditor();
  const [draftRenameFrom, setDraftRenameFrom] = useState("");
  const [draftRenameTo, setDraftRenameTo] = useState("");
  const [draftFilterCol, setDraftFilterCol] = useState("");
  const [draftFilterCmp, setDraftFilterCmp] = useState<DataTransformCmp>("eq");
  const [draftFilterValue, setDraftFilterValue] = useState("");
  const [draftAddName, setDraftAddName] = useState("");
  const [draftAddExpr, setDraftAddExpr] = useState("");
  const [draftSelect, setDraftSelect] = useState("");

  const steps = block.dataTransform?.steps ?? [];

  const baseTable = useMemo(() => {
    const fromResolved = coercePayloadToTable(block.resolved?.data);
    if (fromResolved?.rows.length) return fromResolved;
    if (block.resolved?.table?.rows?.length) {
      return {
        columns: (block.resolved.table.columns ?? []).map((col) => col.key),
        rows: block.resolved.table.rows.map((row) => ({ ...row })),
      };
    }
    return { columns: [] as string[], rows: [] as Array<Record<string, unknown>> };
  }, [block.resolved?.data, block.resolved?.table]);

  /** Preview: steps no cliente sobre data cru (servidor usa o mesmo para View). */
  const preview = useMemo(() => applyDataTransformSteps(baseTable, steps), [baseTable, steps]);

  const persistSteps = (nextSteps: DataTransformStep[]) => {
    const transform = normalizeDataTransform({ steps: nextSteps }) as DataTransform | undefined;
    const patch = { dataTransform: transform } as Partial<ComunicadoDataSourceBlock>;
    if (selected?.id === block.id) updateSelected(patch);
    else updateBlock(block.id, patch);
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

  return (
    <DeckPropertySection
      pane={pane}
      title="Preparar dados"
      hint={TV_DASHBOARD_HELP_TOOLTIPS.data.prepareData}
      defaultOpen={steps.length > 0}
    >
      <p className="td-deck-inspector__hint">
        Transformações na fonte (Query). O visual continua usando a projeção (View) sobre o resultado.
      </p>

      <div className="td-data-prepare__grid-wrap" role="region" aria-label="Prévia da tabela">
        {preview.rows.length === 0 ? (
          <p className="td-deck-inspector__hint">
            Sem linhas para prévia. Teste a rota ou atualize o visual após configurar a fonte.
          </p>
        ) : (
          <table className="td-data-prepare__grid">
            <thead>
              <tr>
                {preview.columns.map((col) => (
                  <th key={col}>{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {preview.rows.slice(0, 12).map((row, rowIndex) => (
                <tr key={rowIndex}>
                  {preview.columns.map((col) => (
                    <td key={col}>{row[col] == null ? "" : String(row[col])}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {preview.rows.length > 12 ? (
          <p className="td-deck-inspector__meta">Mostrando 12 de {preview.rows.length} linhas</p>
        ) : null}
      </div>

      <div className="td-data-prepare__steps" role="list" aria-label="Passos aplicados">
        <p className="td-deck-inspector__hint">Passos aplicados</p>
        {steps.length === 0 ? (
          <p className="td-deck-inspector__meta">Nenhum passo — dados da API como vieram.</p>
        ) : (
          steps.map((step, index) => (
            <div key={`${step.op}-${index}`} className="td-data-prepare__step" role="listitem">
              <span className="td-data-prepare__step-label">
                {index + 1}. {stepLabel(step)}
              </span>
              <div className="td-data-prepare__step-actions">
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
                  aria-label="Remover passo"
                  onClick={() => removeStep(index)}
                >
                  <Trash2 size={14} aria-hidden />
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="td-data-prepare__add">
        <p className="td-deck-inspector__hint">Adicionar passo</p>
        <DeckField id="td-prepare-rename" label="Renomear coluna">
          <div className="td-data-prepare__row">
            <FormSelectControl
              id="td-prepare-rename-from"
              ariaLabel="Coluna atual"
              value={draftRenameFrom}
              onChange={setDraftRenameFrom}
              options={[{ value: "", label: "Coluna…" }, ...columnOptions]}
            />
            <NativeTextControl
              id="td-prepare-rename-to"
              placeholder="Novo nome"
              value={draftRenameTo}
              onChange={setDraftRenameTo}
            />
            <button
              type="button"
              className="td-btn td-btn--sm"
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
              <Plus size={14} aria-hidden />
              Renomear
            </button>
          </div>
        </DeckField>

        <DeckField id="td-prepare-select" label="Selecionar colunas">
          <div className="td-data-prepare__row">
            <NativeTextControl
              id="td-prepare-select-cols"
              placeholder="col1, col2"
              value={draftSelect}
              onChange={setDraftSelect}
            />
            <button
              type="button"
              className="td-btn td-btn--sm"
              disabled={!draftSelect.trim()}
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
              <Plus size={14} aria-hidden />
              Selecionar
            </button>
          </div>
        </DeckField>

        <DeckField id="td-prepare-filter" label="Filtrar">
          <div className="td-data-prepare__row">
            <FormSelectControl
              id="td-prepare-filter-col"
              ariaLabel="Coluna"
              value={draftFilterCol}
              onChange={setDraftFilterCol}
              options={[{ value: "", label: "Coluna…" }, ...columnOptions]}
            />
            <FormSelectControl
              id="td-prepare-filter-cmp"
              ariaLabel="Comparação"
              value={draftFilterCmp}
              onChange={(value) => setDraftFilterCmp(value as DataTransformCmp)}
              options={CMP_OPTIONS}
            />
            {draftFilterCmp !== "notNull" ? (
              <NativeTextControl
                id="td-prepare-filter-value"
                placeholder="Valor"
                value={draftFilterValue}
                onChange={setDraftFilterValue}
              />
            ) : null}
            <button
              type="button"
              className="td-btn td-btn--sm"
              disabled={!draftFilterCol.trim()}
              onClick={() => {
                addStep({
                  op: "filter",
                  column: draftFilterCol.trim(),
                  cmp: draftFilterCmp,
                  ...(draftFilterCmp === "notNull"
                    ? {}
                    : { value: draftFilterValue }),
                });
                setDraftFilterCol("");
                setDraftFilterValue("");
              }}
            >
              <Plus size={14} aria-hidden />
              Filtrar
            </button>
          </div>
        </DeckField>

        <DeckField id="td-prepare-add" label="Coluna calculada">
          <div className="td-data-prepare__row">
            <NativeTextControl
              id="td-prepare-add-name"
              placeholder="Nome"
              value={draftAddName}
              onChange={setDraftAddName}
            />
            <NativeTextControl
              id="td-prepare-add-expr"
              placeholder="ex.: meta - oee"
              value={draftAddExpr}
              onChange={setDraftAddExpr}
            />
            <button
              type="button"
              className="td-btn td-btn--sm"
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
              <Plus size={14} aria-hidden />
              Calcular
            </button>
          </div>
        </DeckField>
      </div>
    </DeckPropertySection>
  );
}
