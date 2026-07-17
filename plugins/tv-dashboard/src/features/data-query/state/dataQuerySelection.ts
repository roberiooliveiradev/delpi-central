import type { DataQueryCompiledStep } from "../domain/dataQueryTypes";

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
