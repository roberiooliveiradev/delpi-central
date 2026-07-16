import {
  canEditFormula,
  formulaBarDisplayValue,
  formatStepFormula,
  parseFormulaBarText,
  type FormulaParseResult,
} from "@delpi/tv-dashboard-presentation";
import { HintAction } from "@delpi/plugin-ui/index";
import type { DataTransformStep } from "@delpi/tv-dashboard-presentation";
import { Check, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";

const H = TV_DASHBOARD_HELP_TOOLTIPS.dataPrepare;

type Props = {
  step: DataTransformStep | null;
  newColumnDraft?: boolean;
  columnHints?: string[];
  onCommit: (step: DataTransformStep) => void;
  onCancelDraft?: () => void;
  focusToken?: number;
};

/**
 * Barra fx estilo Power Query: edita a etapa selecionada; ✓ aplica, ✕ descarta.
 * Cálculo permanece no backend.
 */
export function DataPrepareFormulaBar({
  step,
  newColumnDraft = false,
  columnHints = [],
  onCommit,
  onCancelDraft,
  focusToken = 0,
}: Props) {
  const editable = newColumnDraft || canEditFormula(step);
  const baseline = formulaBarDisplayValue(step, { newColumnDraft });
  const [value, setValue] = useState(baseline);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const dirty = editable && value !== baseline;

  useEffect(() => {
    setValue(formulaBarDisplayValue(step, { newColumnDraft }));
    setError(null);
  }, [step, newColumnDraft]);

  useEffect(() => {
    if (!focusToken) return;
    inputRef.current?.focus();
    inputRef.current?.select();
  }, [focusToken]);

  const commit = () => {
    if (!editable) return;
    const result: FormulaParseResult = parseFormulaBarText(value, {
      step,
      newColumnDraft,
    });
    if (!result.ok) {
      setError(result.error);
      return;
    }
    setError(null);
    onCommit(result.step);
  };

  const discard = () => {
    setValue(baseline);
    setError(null);
    if (newColumnDraft) onCancelDraft?.();
  };

  const hint = (() => {
    if (!editable) return null;
    if (newColumnDraft || step?.op === "addColumn") {
      const cols =
        columnHints.length > 0
          ? `Colunas: ${columnHints.slice(0, 12).join(", ")}${columnHints.length > 12 ? "…" : ""}`
          : null;
      const dsl = "DSL: if(cond, a, b), concat, abs/min/max/coalesce…";
      return cols ? `${cols} · ${dsl}` : dsl;
    }
    if (step?.op === "rename") return "Ex.: = RenameColumns(Fonte, de → para)";
    if (step?.op === "select") return "Ex.: = SelectColumns(Fonte, [col1, col2])";
    if (step?.op === "filter") return 'Ex.: = FilterRows(Fonte, [col] eq "valor")';
    if (step?.op === "sort") return "Ex.: = Sort(Fonte, coluna, asc|desc)";
    if (step?.op === "replace") return 'Ex.: = ReplaceValue(Fonte, coluna, "a" → "b")';
    return null;
  })();

  return (
    <div className="td-data-pq__formula-wrap">
      <HintAction hint={H.formulaBar} ariaLabel="Ajuda: barra de fórmula" placement="bottom">
        <div className="td-data-pq__formula" aria-label="Barra de fórmula">
          <span className="td-data-pq__fx" aria-hidden>
            fx
          </span>
          {editable ? (
            <>
              <input
                ref={inputRef}
                className="td-data-pq__formula-input"
                value={value}
                onChange={(event) => {
                  setValue(event.target.value);
                  if (error) setError(null);
                }}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    event.preventDefault();
                    commit();
                  }
                  if (event.key === "Escape") {
                    event.preventDefault();
                    discard();
                  }
                }}
                aria-label="Fórmula da etapa"
                aria-invalid={Boolean(error)}
                placeholder={
                  newColumnDraft
                    ? "= AddColumn(Fonte, nome, expr)"
                    : formatStepFormula(step)
                }
              />
              <HintAction hint={H.formulaApply} ariaLabel="Ajuda: aplicar fórmula" placement="bottom">
                <button
                  type="button"
                  className="td-data-pq__formula-btn"
                  aria-label="Aplicar fórmula"
                  disabled={!dirty && !newColumnDraft}
                  onClick={commit}
                >
                  <Check size={14} aria-hidden />
                </button>
              </HintAction>
              <HintAction hint={H.formulaDiscard} ariaLabel="Ajuda: descartar fórmula" placement="bottom">
                <button
                  type="button"
                  className="td-data-pq__formula-btn"
                  aria-label="Descartar"
                  disabled={!dirty && !newColumnDraft}
                  onClick={discard}
                >
                  <X size={14} aria-hidden />
                </button>
              </HintAction>
            </>
          ) : (
            <code>{formatStepFormula(step)}</code>
          )}
        </div>
      </HintAction>
      {error ? (
        <p className="td-data-pq__formula-error" role="alert">
          {error}
        </p>
      ) : hint && editable ? (
        <p className="td-data-pq__formula-hint">{hint}</p>
      ) : !editable && step ? (
        <p className="td-data-pq__formula-hint">
          Etapa só leitura na barra — use o lápis nas etapas ou a ribbon para recriar.
        </p>
      ) : null}
    </div>
  );
}
