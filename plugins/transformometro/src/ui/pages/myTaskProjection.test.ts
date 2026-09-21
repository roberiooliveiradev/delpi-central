import { describe, expect, it } from "vitest";

import { projectPendingSignatureTasks } from "./myTaskProjection";

describe("projectPendingSignatureTasks", () => {
  it("projeta a ata pendente sem copiar prioridade nem prazo", () => {
    const [task] = projectPendingSignatureTasks([
      {
        id: "minute-1",
        unit_code: "01",
        title: "Reunião de melhoria",
        minute_number: "ATA-10",
        meeting_type: "ordinary",
        meeting_date: "2026-09-01",
        status: "awaiting_signatures",
        updated_at: "2026-09-02T12:00:00Z",
      },
    ]);
    expect(task).toEqual({
      id: "meeting_minute_signature:minute-1",
      type: "meeting_minute_signature",
      title: "Reunião de melhoria",
      description: "ATA-10",
      status: "awaiting_signatures",
      sourceType: "meeting_minute",
      sourceId: "minute-1",
      route: "/apps/transformometro/meeting-minutes/minute-1",
      contextLabel: "Unidade 01",
      updatedAt: "2026-09-02T12:00:00Z",
    });
    expect(task).not.toHaveProperty("priority");
    expect(task).not.toHaveProperty("dueDate");
  });

  it("lista vazia permanece vazia", () => {
    expect(projectPendingSignatureTasks([])).toEqual([]);
  });
});
