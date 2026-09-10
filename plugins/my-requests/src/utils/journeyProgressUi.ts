import type { JourneyProgress, JourneyProgressStage } from "../types/requests";

type TrackerStepState = "complete" | "current" | "available" | "locked" | "error";

export type DetailTrackerStep = {
  id: string;
  label: string;
  state: TrackerStepState;
};

/** Map API journey stages to ProgressTracker steps — no local percentage math. */
export function mapJourneyStagesToTrackerSteps(
  stages: JourneyProgressStage[],
): DetailTrackerStep[] {
  return stages.map((stage) => ({
    id: stage.id,
    label: stage.label,
    state: mapStageState(stage.state),
  }));
}

function mapStageState(state: JourneyProgressStage["state"]): TrackerStepState {
  if (state === "complete") return "complete";
  if (state === "current") return "current";
  if (state === "error") return "error";
  return "locked";
}

export function journeyBarSummary(progress: JourneyProgress): string | undefined {
  if (progress.summary) return progress.summary;
  if (progress.outcome === "succeeded") return "Atendimento concluído";
  if (progress.outcome === "cancelled") return "Solicitação cancelada";
  if (progress.outcome === "rejected") return "Solicitação rejeitada";
  if (progress.outcome === "waiting_requester") {
    return "Aguardando informação do solicitante";
  }
  return undefined;
}

/**
 * Compact tracker copy: current stage position (not count of complete steps),
 * so it does not contradict journey.percentage from the API.
 */
export function journeyTrackerCompactSummary(progress: JourneyProgress): string {
  const stages = progress.stages || [];
  const total = stages.length;
  if (total === 0) return "Etapas do atendimento";
  let index = stages.findIndex((stage) => stage.id === progress.current_stage_id);
  if (index < 0) {
    index = stages.findIndex((stage) => stage.state === "current");
  }
  if (index < 0) index = 0;
  const label = stages[index]?.label || "—";
  return `Etapa ${index + 1} de ${total} · ${label}`;
}

export function statusBadgeVariant(
  status: string,
  outcome?: JourneyProgress["outcome"] | null,
): "neutral" | "info" | "success" | "warning" | "danger" {
  if (outcome === "succeeded" || status === "completed") return "success";
  if (outcome === "cancelled" || status === "cancelled") return "danger";
  if (outcome === "rejected" || status === "rejected") return "danger";
  if (outcome === "waiting_requester" || status === "needs_information") {
    return "warning";
  }
  if (status === "in_progress") return "info";
  return "neutral";
}
