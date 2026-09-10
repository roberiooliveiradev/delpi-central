import { describe, expect, it } from "vitest";

import {
  journeyBarSummary,
  journeyTrackerCompactSummary,
  mapJourneyStagesToTrackerSteps,
  statusBadgeVariant,
} from "./journeyProgressUi";
import type { JourneyProgress } from "../types/requests";

describe("journeyProgressUi", () => {
  it("mapeia stages da API sem inventar percentual", () => {
    const steps = mapJourneyStagesToTrackerSteps([
      { id: "intake", label: "Solicitação criada", state: "complete" },
      { id: "service", label: "Em atendimento", state: "current" },
      { id: "closure", label: "Conclusão", state: "upcoming" },
    ]);
    expect(steps.map((s) => s.state)).toEqual(["complete", "current", "locked"]);
  });

  it("marca cancelamento/rejeição como error no tracker", () => {
    const steps = mapJourneyStagesToTrackerSteps([
      { id: "intake", label: "Solicitação criada", state: "complete" },
      { id: "service", label: "Em atendimento", state: "error" },
      { id: "closure", label: "Conclusão", state: "upcoming" },
    ]);
    expect(steps[1].state).toBe("error");
  });

  it("usa summary da API quando presente", () => {
    const progress: JourneyProgress = {
      percentage: 66,
      current_stage_id: "service",
      outcome: "waiting_requester",
      summary: "Aguardando informação do solicitante",
      stages: [],
    };
    expect(journeyBarSummary(progress)).toBe("Aguardando informação do solicitante");
  });

  it("compactSummary usa posição da etapa atual e não contagem de complete", () => {
    const progress: JourneyProgress = {
      percentage: 33,
      current_stage_id: "intake",
      outcome: "in_progress",
      summary: null,
      stages: [
        { id: "intake", label: "Solicitação criada", state: "current" },
        { id: "service", label: "Em atendimento", state: "upcoming" },
        { id: "closure", label: "Conclusão", state: "upcoming" },
      ],
    };
    expect(journeyTrackerCompactSummary(progress)).toBe(
      "Etapa 1 de 3 · Solicitação criada",
    );
    expect(journeyTrackerCompactSummary(progress)).not.toMatch(/0 de 3 concluídas/);
  });

  it("escolhe variant de badge coerente com outcome", () => {
    expect(statusBadgeVariant("completed", "succeeded")).toBe("success");
    expect(statusBadgeVariant("cancelled", "cancelled")).toBe("danger");
    expect(statusBadgeVariant("needs_information", "waiting_requester")).toBe("warning");
  });
});
