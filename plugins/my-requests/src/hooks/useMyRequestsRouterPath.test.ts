import { describe, expect, it } from "vitest";

import { resolveInternalRoute } from "./useMyRequestsRouterPath";

describe("resolveInternalRoute", () => {
  it("raiz e /mine apontam para mine", () => {
    expect(resolveInternalRoute("/apps/my-requests").name).toBe("mine");
    expect(resolveInternalRoute("/apps/my-requests/mine").name).toBe("mine");
  });

  it("resolve fila, nova e detalhe", () => {
    expect(resolveInternalRoute("/apps/my-requests/work-queue").name).toBe("work-queue");
    expect(resolveInternalRoute("/apps/my-requests/new").name).toBe("new");
    const detail = resolveInternalRoute("/apps/my-requests/requests/abc-123");
    expect(detail).toEqual({ name: "detail", requestId: "abc-123" });
  });
});
