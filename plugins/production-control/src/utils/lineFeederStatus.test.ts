import { describe, expect, it } from "vitest";

import {
  formatScheduleTime,
  nextPickItemStatus,
  pickItemBadgeVariant,
  requirementBadgeVariant,
} from "./lineFeederStatus";

describe("lineFeederStatus", () => {
  it("mapeia a situação do material para a severidade visual", () => {
    expect(requirementBadgeVariant("covered")).toBe("success");
    expect(requirementBadgeVariant("to_pick")).toBe("warning");
    expect(requirementBadgeVariant("at_risk")).toBe("danger");
    expect(requirementBadgeVariant("unknown")).toBe("neutral");
    expect(requirementBadgeVariant("algo-novo")).toBe("neutral");
  });

  it("mapeia a situação do item da coleta", () => {
    expect(pickItemBadgeVariant("pending")).toBe("warning");
    expect(pickItemBadgeVariant("picked")).toBe("info");
    expect(pickItemBadgeVariant("delivered")).toBe("success");
    expect(pickItemBadgeVariant("")).toBe("neutral");
  });

  it("cicla a coleta e permite voltar depois de entregue", () => {
    expect(nextPickItemStatus("pending")).toBe("picked");
    expect(nextPickItemStatus("picked")).toBe("delivered");
    expect(nextPickItemStatus("delivered")).toBe("pending");
  });

  it("mostra só a hora do horário programado", () => {
    expect(formatScheduleTime("2026-09-22T08:30:00")).toBe("08:30");
    expect(formatScheduleTime(null)).toBe("—");
    expect(formatScheduleTime("2026-09-22")).toBe("—");
  });
});
