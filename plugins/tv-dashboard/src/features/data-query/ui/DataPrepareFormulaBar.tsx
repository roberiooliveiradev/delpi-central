import { HintAction, NativeTextControl } from "@delpi/plugin-ui/index";
import { Check, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import type { DataQueryDiagnosticDto } from "@delpi/tv-dashboard-presentation";

type Props = {
  stepName: string | null;
  formula: string;
  diagnostics: DataQueryDiagnosticDto[];
  onApply: (expression: string) => Promise<void> | void;
};

export function DataPrepareFormulaBar({
  stepName,
  formula,
  diagnostics,
  onApply,
}: Props) {
  const [value, setValue] = useState(formula);
  const inputRef = useRef<HTMLInputElement>(null);
  useEffect(() => setValue(formula), [formula, stepName]);
  const dirty = value !== formula;
  const diagnostic = diagnostics.find((item) => item.severity === "error");

  const discard = () => {
    setValue(formula);
    inputRef.current?.focus();
  };

  return (
    <div className="td-data-pq__formula-wrap">
      <div className="td-data-pq__formula" aria-label="Barra de fórmula M">
        <span className="td-data-pq__fx" aria-hidden>
          fx
        </span>
        <NativeTextControl
          id="td-m-query-formula"
          ref={inputRef}
          className="td-data-pq__formula-input"
          aria-label="Expressão M da etapa"
          aria-invalid={Boolean(diagnostic)}
          value={value}
          disabled={!stepName}
          onChange={setValue}
          onKeyDown={(event) => {
            if (event.key === "Enter" && dirty && stepName) {
              event.preventDefault();
              void onApply(value);
            } else if (event.key === "Escape") {
              event.preventDefault();
              discard();
            }
          }}
        />
        <HintAction hint="Valida e aplica a expressão no servidor." ariaLabel="Ajuda: aplicar expressão">
          <button
            type="button"
            className="td-data-pq__formula-btn"
            aria-label="Aplicar expressão"
            disabled={!dirty || !stepName}
            onClick={() => void onApply(value)}
          >
            <Check size={16} aria-hidden />
          </button>
        </HintAction>
        <HintAction hint="Descarta somente a edição da barra." ariaLabel="Ajuda: descartar expressão">
          <button
            type="button"
            className="td-data-pq__formula-btn"
            aria-label="Descartar expressão"
            disabled={!dirty}
            onClick={discard}
          >
            <X size={16} aria-hidden />
          </button>
        </HintAction>
      </div>
      {diagnostic?.range ? (
        <p className="td-data-pq__formula-error" role="alert">
          {diagnostic.code} — linha {diagnostic.range.startLine}, coluna{" "}
          {diagnostic.range.startColumn}: {diagnostic.message}
        </p>
      ) : null}
    </div>
  );
}
