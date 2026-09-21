import { describe, expect, it } from "vitest";

import { buildTaskWorkspaceHighlights } from "./taskPresentation";

describe("buildTaskWorkspaceHighlights", () => {
  it("omite vencendo/vencidas quando o portal não tem prazo", () => {
    const highlights = buildTaskWorkspaceHighlights(
      { pending: 2 },
      { includeDueBuckets: false },
    );
    expect(highlights.map((item) => item.id)).toEqual(["pending"]);
  });

  it("marca vencidas quando a contagem é real", () => {
    const highlights = buildTaskWorkspaceHighlights({
      pending: 3,
      dueSoon: 1,
      overdue: 2,
    });
    expect(highlights.find((item) => item.id === "overdue")?.tone).toBe("danger");
  });
});
