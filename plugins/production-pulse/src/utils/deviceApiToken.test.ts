import { describe, expect, it } from "vitest";

import {
  canCopyDeviceApiToken,
  ensureDeviceApiTokenForCreate,
  generateDeviceApiToken,
  resolveDeviceApiTokenFieldStatus,
} from "./deviceApiToken";

describe("deviceApiToken", () => {
  it("positive: create auto-fill generates token when empty", () => {
    const token = ensureDeviceApiTokenForCreate("   ");
    expect(token.length).toBeGreaterThan(8);
    expect(token).not.toMatch(/\s/);
  });

  it("sibling: create keeps manual token", () => {
    expect(ensureDeviceApiTokenForCreate("  my-manual-token  ")).toBe("my-manual-token");
  });

  it("sibling: badge configured when set and field empty", () => {
    expect(
      resolveDeviceApiTokenFieldStatus({ apiToken: "", apiTokenSet: true }),
    ).toBe("configured");
  });

  it("sibling: badge missing when unset and field empty", () => {
    expect(
      resolveDeviceApiTokenFieldStatus({ apiToken: "", apiTokenSet: false }),
    ).toBe("missing");
  });

  it("sibling: badge pending_save when session value present", () => {
    expect(
      resolveDeviceApiTokenFieldStatus({ apiToken: "abc", apiTokenSet: true }),
    ).toBe("pending_save");
  });

  it("negative: copy disabled without session value", () => {
    expect(canCopyDeviceApiToken("")).toBe(false);
    expect(canCopyDeviceApiToken("   ")).toBe(false);
  });

  it("positive: copy enabled with session value", () => {
    expect(canCopyDeviceApiToken("secret")).toBe(true);
  });

  it("generateDeviceApiToken returns non-empty opaque string", () => {
    const a = generateDeviceApiToken();
    const b = generateDeviceApiToken();
    expect(a.length).toBeGreaterThan(8);
    expect(b.length).toBeGreaterThan(8);
    expect(a).not.toBe(b);
  });
});
