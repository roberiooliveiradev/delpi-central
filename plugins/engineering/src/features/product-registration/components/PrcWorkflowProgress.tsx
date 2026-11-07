import { EngineeringProgressTracker } from "../../../ui/engineeringUi";
import { prcStatusLabel } from "../prcCopy";

const MAIN_PATH = ["submitted", "in_progress", "under_review", "completed"];

const STEP_LABELS: Record<string, string> = {
  submitted: "Enviada",
  in_progress: "Em atendimento",
  under_review: "Em revisão",
  completed: "Concluída",
};

type StepState = "complete" | "current" | "available" | "locked" | "error";

/** Andamento do workflow PRC — caminho linear
 * submitted → in_progress → under_review → completed, com
 * needs_information/rejected representados como estado do step atual
 * (não como avanço linear, que seria enganoso). */
export function PrcWorkflowProgress({ status }: { status: string }) {
  const currentIndex = MAIN_PATH.indexOf(
    status === "needs_information" ? "in_progress" : status,
  );

  const steps = MAIN_PATH.map((id, index) => {
    let state: StepState = "locked";
    if (status === "rejected") {
      state = index === 0 ? "complete" : "locked";
    } else if (currentIndex >= 0) {
      if (index < currentIndex) state = "complete";
      else if (index === currentIndex) state = "current";
      else state = "available";
    }
    const statusLabel =
      index === currentIndex && status === "needs_information"
        ? "em andamento — aguardando informações"
        : index === 0 && status === "rejected"
          ? "concluída — solicitação depois rejeitada"
          : undefined;
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
