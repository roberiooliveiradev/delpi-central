import { describe, expect, it } from "vitest";

import {
  filterActiveMachineLoadOperations,
  isMachineLoadFinishedOperation,
  isMachineLoadStarted,
  machineLoadRowModifierClass,
  machineLoadStatusBadge,
  machineLoadStatusRank,
} from "./machineLoadStatus";

describe("machineLoadStatus", () => {
  it("marca em produção com verde", () => {
    expect(machineLoadStatusBadge("in_progress").variant).toBe("success");
  });

  it("distingue já apontada de não iniciada", () => {
    expect(machineLoadStatusBadge("started").variant).toBe("info");
    expect(machineLoadStatusBadge("not_started").variant).toBe("neutral");
  });

  it("cai em não iniciada quando o status vem vazio ou desconhecido", () => {
    expect(machineLoadStatusBadge(null).label).toBe(machineLoadStatusBadge("not_started").label);
    expect(machineLoadStatusBadge("running").variant).toBe("neutral");
  });

  it("ordena em produção antes de já apontada e não iniciada", () => {
    const ordered = ["not_started", "in_progress", "started"].sort(
      (a, b) => machineLoadStatusRank(a) - machineLoadStatusRank(b),
    );
    expect(ordered).toEqual(["in_progress", "started", "not_started"]);
  });

  it("identifica já apontada para tachar a linha", () => {
    expect(isMachineLoadStarted("started")).toBe(true);
    expect(isMachineLoadStarted("in_progress")).toBe(false);
    expect(
      machineLoadRowModifierClass({
        production_status: "started",
        is_in_production: false,
      }),
    ).toBe("ppc-load__row--started");
    expect(
      machineLoadRowModifierClass({
        production_status: "started",
        is_in_production: true,
      }),
    ).toBe("ppc-load__row--running");
  });

  it("filtra operações finalizadas mantendo as em produção", () => {
    const rows = [
      { production_status: "started" as const, is_in_production: false },
      { production_status: "in_progress" as const, is_in_production: true },
      { production_status: "not_started" as const, is_in_production: false },
      { production_status: "started" as const, is_in_production: true },
    ];
    expect(filterActiveMachineLoadOperations(rows)).toEqual([
      { production_status: "in_progress", is_in_production: true },
      { production_status: "not_started", is_in_production: false },
      { production_status: "started", is_in_production: true },
    ]);
    expect(isMachineLoadFinishedOperation(rows[0]!)).toBe(true);
    expect(isMachineLoadFinishedOperation(rows[3]!)).toBe(false);
  });
});
