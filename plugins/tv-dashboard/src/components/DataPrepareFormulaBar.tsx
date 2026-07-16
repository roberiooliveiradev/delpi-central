import {
  canEditFormula,
  formulaBarDisplayValue,
  formatStepFormula,
  parseFormulaBarText,
  type FormulaParseResult,
} from "@delpi/tv-dashboard-presentation";
import type { DataTransformStep } from "@delpi/tv-dashboard-presentation";
import { useEffect, useRef, useState } from "react";

type Props = {
  step: DataTransformStep | null;
  /** Modo criar nova coluna pela barra. */
  newColumnDraft?: boolean;
  columnHints?: string[];
  onCommit: (step: DataTransformStep) => void;
  onCancelDraft?: () => void;
  /** Foco programático (ex.: botão Nova coluna fx). */
  focusToken?: number;
};

/**
 * Barra fx da preparação de dados — só edita texto; cálculo no backend.
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
  const [value, setValue] = useState(() =>
    formulaBarDisplayValue(step, { newColumnDraft }),
  );
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

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

  const hint = (() => {
    if (!editable) return null;
    if (newColumnDraft || step?.op === "addColumn") {
      const cols =
        columnHints.length > 0
          ? `Colunas: ${columnHints.slice(0, 12).join(", ")}${columnHints.length > 12 ? "…" : ""}`
          : null;
      const dsl = "DSL: if(cond, a, b), concat, abs/min/max/coalesce/len/lower/upper/trim";
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
      <div className="td-data-pq__formula" aria-label="Barra de fórmula">
        <span className="td-data-pq__fx" aria-hidden>
          fx
        </span>
        {editable ? (
          <input
            ref={inputRef}
            className="td-data-pq__formula-input"
            value={value}
            onChange={(event) => {
              setValue(event.target.value);
              if (error) setError(null);
            }}
            onBlur={commit}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                commit();
              }
              if (event.key === "Escape" && newColumnDraft) {
                event.preventDefault();
                onCancelDraft?.();
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
        ) : (
          <code>{formatStepFormula(step)}</code>
        )}
      </div>
      {error ? (
        <p className="td-data-pq__formula-error" role="alert">
          {error}
        </p>
      ) : hint && editable ? (
        <p className="td-data-pq__formula-hint">{hint}</p>
      ) : null}
    </div>
  );
}
