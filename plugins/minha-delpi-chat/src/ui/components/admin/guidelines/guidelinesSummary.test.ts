import { describe, expect, it } from "vitest";

import type { AdminGuideline } from "../../../../data/api/adminTypes";

import {
  computeGuidelinesSummary,
  filterGuidelinesByStatus,
} from "./guidelinesSummary";

function guideline(status: AdminGuideline["status"], id: string): AdminGuideline {
  return {
    id,
    title: id,
    description: "",
    content: "x",
    category: "behavior",
    environment: "global",
    status,
  };
}

describe("guidelinesSummary", () => {
  it("computes counts by status", () => {
    const list = [
      guideline("active", "1"),
      guideline("active", "2"),
      guideline("draft", "3"),
      guideline("archived", "4"),
    ];

    expect(computeGuidelinesSummary(list)).toEqual({
      total: 4,
      active: 2,
      draft: 1,
      archived: 1,
    });
  });

  it("filters guidelines by status", () => {
    const list = [guideline("draft", "a"), guideline("active", "b")];

    expect(filterGuidelinesByStatus(list, "draft")).toHaveLength(1);
    expect(filterGuidelinesByStatus(list, "all")).toHaveLength(2);
  });
});
