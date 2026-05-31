import { describe, expect, it } from "vitest";

import type { AdminSpecializedAgent } from "../../../../data/api/adminTypes";

import { computeAgentsSummary, filterAgentsByCatalog } from "./agentsSummary";

function agent(
  overrides: Partial<AdminSpecializedAgent> & { id: string },
): AdminSpecializedAgent {
  return {
    name: overrides.id,
    description: null,
    category: null,
    visibility: "system",
    enabled: true,
    hasSpecialization: false,
    specialization: null,
    ...overrides,
  };
}

describe("agentsSummary", () => {
  it("computes agent catalog counts", () => {
    const list = [
      agent({ id: "a", hasSpecialization: true }),
      agent({ id: "b", enabled: false }),
      agent({ id: "c" }),
    ];

    expect(computeAgentsSummary(list)).toEqual({
      total: 3,
      enabled: 2,
      disabled: 1,
      withSpecialization: 1,
    });
  });

  it("filters specialized agents", () => {
    const list = [
      agent({ id: "a", hasSpecialization: true }),
      agent({ id: "b" }),
    ];

    expect(filterAgentsByCatalog(list, "specialized")).toHaveLength(1);
  });
});
