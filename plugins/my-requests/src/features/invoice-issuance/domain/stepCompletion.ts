import { buildReviewChecklist } from "./reviewChecklist";
import type { FreightMode, InvoiceType, IssuanceItem, Party } from "./types";
import { WIZARD_STEPS } from "./wizardSteps";

export type WizardStepId = (typeof WIZARD_STEPS)[number]["id"];

export type WizardStepState =
  | "complete"
  | "current"
  | "available"
  | "locked"
  | "error";

export type WizardDraft = {
  party: Party | null;
  invoiceType: InvoiceType;
  invoiceTypeOther: string;
  items: IssuanceItem[];
  freightMode: FreightMode;
  weightKg: string;
  volumeCount: string;
};

export type StepCompletionMap = Record<WizardStepId, boolean>;

const STEP_IDS = WIZARD_STEPS.map((s) => s.id);

/** Align UX completeness with requests-api quantity minimum (≥ 0.001). */
export function isStepComplete(stepId: WizardStepId, draft: WizardDraft): boolean {
  const flags = buildReviewChecklist({
    party: draft.party,
    items: draft.items,
    invoiceType: draft.invoiceType,
    invoiceTypeOther: draft.invoiceTypeOther,
    freightMode: draft.freightMode,
    weightKg: draft.weightKg,
    volumeCount: draft.volumeCount,
  });

  switch (stepId) {
    case "recipient":
      return flags.recipient;
    case "invoiceType":
      return flags.invoice_type;
    case "items":
      return (
        flags.item_codes &&
        flags.quantity_price &&
        flags.stock_write_off &&
        draft.items.every((item) => Number(item.quantity) >= 0.001)
      );
    case "freight":
      return flags.freight_mode;
    case "extras":
      return flags.weight_volumes;
    case "review":
      return Object.values(flags).every(Boolean);
    default:
      return false;
  }
}

export function buildStepCompletionMap(draft: WizardDraft): StepCompletionMap {
  return {
    recipient: isStepComplete("recipient", draft),
    invoiceType: isStepComplete("invoiceType", draft),
    items: isStepComplete("items", draft),
    freight: isStepComplete("freight", draft),
    extras: isStepComplete("extras", draft),
    review: isStepComplete("review", draft),
  };
}

/**
 * Longest sequential prefix of steps that are field-complete.
 * Future steps with defaults (sale/cif/weight) do not count until unlocked in order.
 */
export function computeSequentialCompletedCount(
  completion: StepCompletionMap,
): number {
  let count = 0;
  for (const id of STEP_IDS) {
    if (!completion[id]) break;
    count += 1;
  }
  return count;
}

export function computeMaxUnlockedIndex(completion: StepCompletionMap): number {
  let max = 0;
  for (let i = 0; i < STEP_IDS.length - 1; i += 1) {
    const id = STEP_IDS[i];
    if (!completion[id]) break;
    max = i + 1;
  }
  return max;
}

export function progressPercent(completion: StepCompletionMap): number {
  const done = computeSequentialCompletedCount(completion);
  return Math.round((done / STEP_IDS.length) * 100);
}

export function completedStepCount(completion: StepCompletionMap): number {
  return computeSequentialCompletedCount(completion);
}

function allPreviousComplete(
  completion: StepCompletionMap,
  index: number,
): boolean {
  for (let i = 0; i < index; i += 1) {
    if (!completion[STEP_IDS[i]]) return false;
  }
  return true;
}

export function computeStepStates(input: {
  currentStepId: WizardStepId;
  completion: StepCompletionMap;
  stepErrorIds?: ReadonlySet<WizardStepId>;
}): Array<{ id: WizardStepId; label: string; state: WizardStepState }> {
  const maxUnlocked = computeMaxUnlockedIndex(input.completion);
  const errors = input.stepErrorIds ?? new Set<WizardStepId>();

  return WIZARD_STEPS.map((step, index) => {
    let state: WizardStepState;
    if (errors.has(step.id)) {
      state = "error";
    } else if (step.id === input.currentStepId) {
      state = "current";
    } else if (
      input.completion[step.id] &&
      allPreviousComplete(input.completion, index)
    ) {
      state = "complete";
    } else if (index <= maxUnlocked) {
      state = "available";
    } else {
      state = "locked";
    }
    return { id: step.id, label: step.label, state };
  });
}

export function canOpenStep(
  stepId: WizardStepId,
  completion: StepCompletionMap,
): boolean {
  const index = STEP_IDS.indexOf(stepId);
  if (index < 0) return false;
  return index <= computeMaxUnlockedIndex(completion);
}

export function resolveNextStepAfterEdit(input: {
  editedStepId: WizardStepId;
  completion: StepCompletionMap;
  returnToReview: boolean;
}): WizardStepId {
  if (input.returnToReview && input.completion[input.editedStepId]) {
    return "review";
  }
  return input.editedStepId;
}
