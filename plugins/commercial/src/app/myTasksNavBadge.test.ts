import { describe, expect, it } from "vitest";

import { resolveMyTasksNavBadgeCount } from "./myTasksNavBadge";

describe("resolveMyTasksNavBadgeCount", () => {
  it("usa counts.open quando presente", () => {
    expect(resolveMyTasksNavBadgeCount({ open: 7, overdue: 1, today: 2 })).toBe(7);
  });

  it("faz fallback para overdue+today+later", () => {
    expect(resolveMyTasksNavBadgeCount({ overdue: 2, today: 1, later: 3 })).toBe(6);
  });

  it("retorna 0 para vazio/negativo inválido", () => {
    expect(resolveMyTasksNavBadgeCount(null)).toBe(0);
    expect(resolveMyTasksNavBadgeCount({ open: -2 })).toBe(0);
  });
});
