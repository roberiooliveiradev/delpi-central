import { describe, expect, it } from "vitest";

import {
  buildAccessFromPermissions,
  canProcessAnyRequest,
} from "./requestsAccess";

describe("buildAccessFromPermissions", () => {
  it("marca canManage com my-requests.manage", () => {
    const access = buildAccessFromPermissions(["my-requests.access", "my-requests.manage"]);
    expect(access.canManage).toBe(true);
    expect(canProcessAnyRequest(access)).toBe(true);
  });

  it("sem manage não libera admin", () => {
    const access = buildAccessFromPermissions([
      "my-requests.access",
      "my-requests.invoice-issuance.create",
    ]);
    expect(access.canManage).toBe(false);
    expect(canProcessAnyRequest(access)).toBe(false);
  });
});
