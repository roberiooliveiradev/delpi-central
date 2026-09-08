import { describe, expect, it } from "vitest";

import { buildAdminAuditHrefWithTrace } from "./adminAuditDeepLink";

describe("buildAdminAuditHrefWithTrace", () => {
  it("appends traceId query on audit path", () => {
    expect(buildAdminAuditHrefWithTrace("abc-1")).toBe(
      "/apps/minha-delpi-chat/admin/governance/audit?traceId=abc-1",
    );
  });

  it("returns audit path without query when traceId missing", () => {
    expect(buildAdminAuditHrefWithTrace("")).toBe(
      "/apps/minha-delpi-chat/admin/governance/audit",
    );
    expect(buildAdminAuditHrefWithTrace(null)).toBe(
      "/apps/minha-delpi-chat/admin/governance/audit",
    );
  });
});
