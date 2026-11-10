import { EngineeringProgressTracker } from "../../../ui/engineeringUi";
import { prcStatusLabel } from "../prcCopy";

/** PRC-REF-020 — caminho operacional sem Em revisão. */
const MAIN_PATH = ["submitted", "in_progress", "completed"];

const STEP_LABELS: Record<string, string> = {
  submitted: "Enviada",
  in_progress: "Em atendimento",
  completed: "Concluída",
};

type StepState = "complete" | "current" | "available" | "locked" | "error";

/** Andamento do workflow PRC — caminho linear
 * submitted → in_progress → completed (REF-020/022).
 * needs_correction / needs_information / under_review / rejected são
 * estados do step atual, sem inventar avanço linear enganoso. */
export function PrcWorkflowProgress({ status }: { status: string }) {
  const mappedStatus =
    status === "needs_information" ||
    status === "under_review" ||
    status === "needs_correction"
      ? "in_progress"
      : status;
  const currentIndex = MAIN_PATH.indexOf(mappedStatus);

  const steps = MAIN_PATH.map((id, index) => {
    let state: StepState = "locked";
    if (status === "rejected") {
      state = index === 0 ? "complete" : "locked";
    } else if (currentIndex >= 0) {
      if (index < currentIndex) state = "complete";
      else if (index === currentIndex) state = "current";
      else state = "available";
    }
    let statusLabel: string | undefined;
    if (index === currentIndex && status === "needs_correction") {
      statusLabel = "em andamento — devolvida para correção";
    } else if (index === currentIndex && status === "needs_information") {
      statusLabel = "em andamento — aguardando informações";
    } else if (index === currentIndex && status === "under_review") {
      statusLabel = "legado em revisão — use Concluir atendimento ou Reabrir";
    } else if (index === 0 && status === "rejected") {
      statusLabel = "concluída — solicitação depois rejeitada";
    }
    return { id, label: STEP_LABELS[id], state, statusLabel };
  });

  const currentStepId =
    status === "rejected" ? "submitted" : MAIN_PATH[Math.max(0, currentIndex)];

  return (
    <EngineeringProgressTracker
      steps={steps}
      currentStepId={currentStepId}
      ariaLabel={`Andamento da solicitação — status atual: ${prcStatusLabel(status)}`}
    />
  );
}
