import type {
  DataQueryCompiledStep,
  DataQueryMutationAction,
} from "../domain/dataQueryTypes";

/**
 * Etapa que deve ficar em foco após uma mutação, espelhando o Power Query:
 * inserir foca a etapa nova; coalescer (sort/reorder reaplicado) foca a etapa
 * cuja fórmula mudou. Sem isso a prévia continua na etapa anterior e a
 * ordenação "não funciona" para o usuário.
 */
export function resolveStepAfterMutation(
  action: DataQueryMutationAction,
  selectedStepName: string | null,
  previousSteps: readonly DataQueryCompiledStep[],
  nextSteps: readonly DataQueryCompiledStep[],
): string | null {
  if (action.type !== "insert_step") {
    return reconcileSelectedStepName(selectedStepName, nextSteps);
  }
  const previousByName = new Map(previousSteps.map((step) => [step.name, step]));
  const inserted = nextSteps.find((step) => !previousByName.has(step.name));
  if (inserted) return inserted.name;
  const changed = nextSteps.find(
    (step) => previousByName.get(step.name)?.formula !== step.formula,
  );
  if (changed) return changed.name;
  return reconcileSelectedStepName(selectedStepName, nextSteps);
}

export function reconcileSelectedStepName(
  selectedStepName: string | null,
  steps: readonly DataQueryCompiledStep[],
): string | null {
  if (selectedStepName && steps.some((step) => step.name === selectedStepName)) {
    return selectedStepName;
  }
  return steps.at(-1)?.name ?? null;
}

export function stepIndexByName(
  steps: readonly DataQueryCompiledStep[],
  stepName: string | null,
): number {
  return stepName ? steps.findIndex((step) => step.name === stepName) : -1;
}
