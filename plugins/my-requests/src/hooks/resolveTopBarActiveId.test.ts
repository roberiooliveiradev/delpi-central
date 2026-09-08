import { describe, expect, it } from "vitest";

import { resolveTopBarActiveId } from "./resolveTopBarActiveId";

describe("resolveTopBarActiveId", () => {
  it("mapeia rotas principais", () => {
    expect(resolveTopBarActiveId("/apps/my-requests")).toBe("mine");
    expect(resolveTopBarActiveId("/apps/my-requests/mine")).toBe("mine");
    expect(resolveTopBarActiveId("/apps/my-requests/work-queue")).toBe("work_queue");
    expect(resolveTopBarActiveId("/apps/my-requests/new")).toBe("new");
    expect(resolveTopBarActiveId("/apps/my-requests/admin")).toBe("admin");
  });

  it("detalhe sem origem cai em mine; new permanece new", () => {
    expect(resolveTopBarActiveId("/apps/my-requests/requests/abc")).toBe("mine");
    expect(resolveTopBarActiveId("/apps/my-requests/new/")).toBe("new");
  });
});
