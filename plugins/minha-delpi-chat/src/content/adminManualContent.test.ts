import { describe, expect, it } from "vitest";

import {
  ADMIN_MANUAL_PERSONAS,
  getAdminManualPersona,
} from "./adminManualContent";

describe("adminManualContent", () => {
  it("expõe três personas com links EN", () => {
    expect(ADMIN_MANUAL_PERSONAS).toHaveLength(3);
    expect(getAdminManualPersona("curator")?.links[0]?.nav.subTab).toBe("documents");
    expect(getAdminManualPersona("platform")?.links.some((l) => l.nav.subTab === "intelligence")).toBe(
      true,
    );
    expect(getAdminManualPersona("auditor")?.links.some((l) => l.nav.subTab === "audit")).toBe(
      true,
    );
  });

  it("não inventa persona inexistente", () => {
    expect(getAdminManualPersona("unknown" as "curator")).toBeUndefined();
  });
});
