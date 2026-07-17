import { NativeTextControl } from "@delpi/plugin-ui/index";
import { ArrowDown, ArrowUp, Pencil, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";

import type { DataQueryCompiledStep } from "../domain/dataQueryTypes";

type Props = {
  steps: DataQueryCompiledStep[];
  selectedStepName: string | null;
  onSelect: (stepName: string | null) => void;
  onMove: (stepName: string, targetIndex: number) => void;
  onRemove: (stepName: string) => void;
  onRename: (stepName: string, newName: string) => void;
};

export function DataPrepareAppliedSteps({
  steps,
  selectedStepName,
  onSelect,
  onMove,
  onRemove,
  onRename,
}: Props) {
  const [search, setSearch] = useState("");
  const [renaming, setRenaming] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const visibleSteps = useMemo(
    () =>
      steps.filter((step) =>
        step.label.toLocaleLowerCase("pt-BR").includes(search.trim().toLocaleLowerCase("pt-BR")),
      ),
    [search, steps],
  );
  return (
    <aside className="td-data-pq__settings" aria-label="Etapas aplicadas">
      <h2 className="td-data-pq__pane-title">Etapas aplicadas</h2>
      <NativeTextControl
        type="search"
        value={search}
        aria-label="Buscar etapa"
        placeholder="Buscar etapa"
        onChange={setSearch}
      />
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
        {visibleSteps.map((step) => {
          const index = steps.findIndex((item) => item.name === step.name);
          return (
          <li key={step.name} className="td-data-pq__step-row">
            {renaming === step.name ? (
              <NativeTextControl
                value={renameValue}
                aria-label={`Novo nome de ${step.label}`}
                onChange={setRenameValue}
                autoFocus
                onKeyDown={(event) => {
                  if (event.key === "Enter" && renameValue.trim()) {
                    onRename(step.name, renameValue.trim());
                    setRenaming(null);
                  } else if (event.key === "Escape") {
                    setRenaming(null);
                  }
                }}
              />
            ) : (
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
            )}
            <div className="td-data-pq__step-actions">
              <button
                type="button"
                className="td-btn td-btn--sm td-btn--ghost"
                aria-label={`Renomear ${step.label}`}
                onClick={() => {
                  setRenaming(step.name);
                  setRenameValue(step.name);
                }}
              >
                <Pencil size={16} aria-hidden />
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
            </div>
          </li>
          );
        })}
      </ol>
    </aside>
  );
}
