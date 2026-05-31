import { describe, expect, it } from "vitest";

import { computeAuditSummary } from "./auditSummary";

describe("computeAuditSummary", () => {
  it("usa total da paginação e contagens da página atual", () => {
    expect(
      computeAuditSummary(
        [
          { id: 1, action: "a", userId: "u1" } as never,
          { id: 2, action: "b", userId: "u1" } as never,
        ],
        120,
        7,
      ),
    ).toEqual({
      total: "120",
      pageEvents: "2",
      uniqueActions: "2",
      uniqueUsers: "1",
      timelineDays: "7",
    });
  });
});
