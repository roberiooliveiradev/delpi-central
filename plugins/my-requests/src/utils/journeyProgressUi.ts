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
