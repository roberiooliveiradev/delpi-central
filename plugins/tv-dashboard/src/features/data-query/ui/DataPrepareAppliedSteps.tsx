import { ArrowDown, ArrowUp, Trash2 } from "lucide-react";

import type { DataQueryCompiledStep } from "../domain/dataQueryTypes";

type Props = {
  steps: DataQueryCompiledStep[];
  selectedStepName: string | null;
  onSelect: (stepName: string | null) => void;
  onMove: (stepName: string, targetIndex: number) => void;
  onRemove: (stepName: string) => void;
};

export function DataPrepareAppliedSteps({
  steps,
  selectedStepName,
  onSelect,
  onMove,
  onRemove,
}: Props) {
  return (
    <aside className="td-data-pq__settings" aria-label="Etapas aplicadas">
      <h2 className="td-data-pq__pane-title">Etapas aplicadas</h2>
      <ol className="td-data-pq__steps">
        <li>
          <button
            type="button"
            className={
              selectedStepName === null
                ? "td-data-pq__step td-data-pq__step--selected"
                : "td-data-pq__step"
            }
            aria-pressed={selectedStepName === null}
            onClick={() => onSelect(null)}
          >
            Fonte
          </button>
        </li>
        {steps.map((step, index) => (
          <li key={step.name} className="td-data-pq__step-row">
            <button
              type="button"
              className={
                selectedStepName === step.name
                  ? "td-data-pq__step td-data-pq__step--selected"
                  : "td-data-pq__step"
              }
              aria-pressed={selectedStepName === step.name}
              onClick={() => onSelect(step.name)}
            >
              {step.label}
            </button>
            <button
              type="button"
              className="td-btn td-btn--sm td-btn--ghost"
              aria-label={`Mover ${step.label} para cima`}
              disabled={index === 0}
              onClick={() => onMove(step.name, index - 1)}
            >
              <ArrowUp size={16} aria-hidden />
            </button>
            <button
              type="button"
              className="td-btn td-btn--sm td-btn--ghost"
              aria-label={`Mover ${step.label} para baixo`}
              disabled={index === steps.length - 1}
              onClick={() => onMove(step.name, index + 1)}
            >
              <ArrowDown size={16} aria-hidden />
            </button>
            <button
              type="button"
              className="td-btn td-btn--sm td-btn--ghost"
              aria-label={`Excluir ${step.label}`}
              onClick={() => onRemove(step.name)}
            >
              <Trash2 size={16} aria-hidden />
            </button>
          </li>
        ))}
      </ol>
    </aside>
  );
}
