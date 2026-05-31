import { describe, expect, it } from "vitest";

import type { AdminChatSkill } from "../../../../data/api/adminTypes";

import { computeSkillsSummary, filterSkillsByStatus } from "./skillsSummary";

function skill(isActive: boolean, id: string): AdminChatSkill {
  return {
    id,
    skillKey: id,
    label: id,
    description: "",
    metadataFlag: "enabled",
    isActive,
    sortOrder: 0,
  };
}

describe("skillsSummary", () => {
  it("computes active and inactive counts", () => {
    const list = [skill(true, "a"), skill(true, "b"), skill(false, "c")];

    expect(computeSkillsSummary(list)).toEqual({
      total: 3,
      active: 2,
      inactive: 1,
    });
  });

  it("filters skills by status", () => {
    const list = [skill(true, "a"), skill(false, "b")];

    expect(filterSkillsByStatus(list, "active")).toHaveLength(1);
    expect(filterSkillsByStatus(list, "inactive")[0]?.id).toBe("b");
  });
});
