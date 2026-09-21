import { describe, expect, it } from "vitest";

import { toTaskItemPresentation } from "./myTaskPresentation";

describe("toTaskItemPresentation", () => {
  it("mapeia tarefa manual sem conhecer persistência", () => {
    const row = toTaskItemPresentation(
      {
        id: "task:1",
        type: "manual_task",
        title: "Validar fluxo",
        description: "Detalhe",
        status: "pending",
        status_label: "Pendente",
        source_label: "Tarefa",
        source_id: "1",
        due_date_label: "25/09/2026",
        overdue: false,
        actions: { can_edit: true, can_complete: true, can_cancel: true },
      },
      "Eu",
    );
    expect(row.title).toBe("Validar fluxo");
    expect(row.sourceLabel).toBe("Tarefa");
    expect(row.actions?.canComplete).toBe(true);
    expect(row.assigneeLabel).toBe("Eu");
  });

  it("projeta assinatura só com abrir", () => {
    const row = toTaskItemPresentation({
      id: "meeting_minute_signature:ata-1",
      type: "meeting_minute_signature",
      title: "Assinar ata",
      status: "pending",
      status_label: "Pendente",
      source_label: "Ata #ATA-10",
      source_id: "ata-1",
      route: "/apps/transformometro/meeting-minutes/ata-1",
      actions: { can_open: true, can_edit: false, can_complete: false, can_cancel: false },
    });
    expect(row.actions).toEqual({
      canOpen: true,
      canEdit: false,
      canComplete: false,
      canCancel: false,
    });
    expect(row.route).toMatch(/meeting-minutes/);
  });
});
