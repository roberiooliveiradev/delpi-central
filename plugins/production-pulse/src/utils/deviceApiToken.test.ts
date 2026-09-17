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

  it("negative: reveal/copy disabled without session value", () => {
    expect(canRevealDeviceApiToken("")).toBe(false);
    expect(canRevealDeviceApiToken("   ")).toBe(false);
    expect(canCopyDeviceApiToken("")).toBe(false);
    expect(canCopyDeviceApiToken("   ")).toBe(false);
  });

  it("positive: reveal/copy enabled with session value", () => {
    expect(canRevealDeviceApiToken("secret")).toBe(true);
    expect(canCopyDeviceApiToken("secret")).toBe(true);
  });

  it("sibling: canReveal matches canCopy", () => {
    expect(canRevealDeviceApiToken("x")).toBe(canCopyDeviceApiToken("x"));
    expect(canRevealDeviceApiToken("")).toBe(canCopyDeviceApiToken(""));
  });

  it("generateDeviceApiToken returns non-empty opaque string", () => {
    const a = generateDeviceApiToken();
    const b = generateDeviceApiToken();
    expect(a.length).toBeGreaterThan(8);
    expect(b.length).toBeGreaterThan(8);
    expect(a).not.toBe(b);
  });

  it("help keys for token action buttons exist", () => {
    expect(PP_HELP.form.apiTokenShowHelp.length).toBeGreaterThan(10);
    expect(PP_HELP.form.apiTokenCopyHelp.length).toBeGreaterThan(10);
    expect(PP_HELP.form.apiTokenGenerateHelp.length).toBeGreaterThan(10);
    expect(PP_HELP.form.apiTokenCopyDisabledHint).toMatch(/mostrar|copiar/i);
  });
});
