import { describe, expect, it } from "vitest";

import { PP_HELP } from "../content/helpTooltips";
import {
  canCopyDeviceApiToken,
  canRevealDeviceApiToken,
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

  it("positive: loaded token from GET is configured", () => {
    expect(
      resolveDeviceApiTokenFieldStatus({
        apiToken: "persisted",
        apiTokenSet: true,
        baselineToken: "persisted",
      }),
    ).toBe("configured");
  });

  it("sibling: badge missing when unset and field empty", () => {
    expect(
      resolveDeviceApiTokenFieldStatus({ apiToken: "", apiTokenSet: false }),
    ).toBe("missing");
  });

  it("sibling: badge pending_save when value differs from baseline", () => {
    expect(
      resolveDeviceApiTokenFieldStatus({
        apiToken: "new-one",
        apiTokenSet: true,
        baselineToken: "old-one",
      }),
    ).toBe("pending_save");
  });

  it("negative: reveal/copy disabled without value", () => {
    expect(canRevealDeviceApiToken("")).toBe(false);
    expect(canCopyDeviceApiToken("   ")).toBe(false);
  });

  it("positive: reveal/copy enabled with loaded value", () => {
    expect(canRevealDeviceApiToken("secret")).toBe(true);
    expect(canCopyDeviceApiToken("secret")).toBe(true);
  });

  it("generateDeviceApiToken returns non-empty opaque string", () => {
    const a = generateDeviceApiToken();
    const b = generateDeviceApiToken();
    expect(a.length).toBeGreaterThan(8);
    expect(b.length).toBeGreaterThan(8);
    expect(a).not.toBe(b);
  });

  it("help keys for token action buttons exist", () => {
    expect(PP_HELP.form.apiTokenShowHelp).toMatch(/campo|cadastro/i);
    expect(PP_HELP.form.apiTokenCopyHelp.length).toBeGreaterThan(10);
    expect(PP_HELP.form.apiTokenGenerateHelp.length).toBeGreaterThan(10);
  });
});
