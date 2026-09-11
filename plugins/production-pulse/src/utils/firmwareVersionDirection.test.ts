import { describe, expect, it } from "vitest";

import {
  normalizeFirmwareVersionToken,
  parseSemVer,
  resolveFirmwareChangeDirection,
} from "./firmwareVersionDirection";

describe("normalizeFirmwareVersionToken", () => {
  it("strips v prefix and extracts trailing SemVer from firmware keys", () => {
    expect(normalizeFirmwareVersionToken("v1.0.0")).toBe("1.0.0");
    expect(normalizeFirmwareVersionToken("esp8266_counter_v1.3.2")).toBe("1.3.2");
    expect(normalizeFirmwareVersionToken("1.0.0")).toBe("1.0.0");
  });
});

describe("parseSemVer", () => {
  it("parses major.minor.patch", () => {
    expect(parseSemVer("1.10.0")).toEqual({ major: 1, minor: 10, patch: 0 });
    expect(parseSemVer("v0.1.3")).toEqual({ major: 0, minor: 1, patch: 3 });
  });
});

describe("resolveFirmwareChangeDirection", () => {
  it("detects upgrade", () => {
    expect(resolveFirmwareChangeDirection("0.1.3", "1.0.0")).toBe("upgrade");
    expect(resolveFirmwareChangeDirection("1.0.9", "1.0.10")).toBe("upgrade");
    expect(resolveFirmwareChangeDirection("2.0.0", "10.0.0")).toBe("upgrade");
  });

  it("detects downgrade", () => {
    expect(resolveFirmwareChangeDirection("1.0.0", "0.1.3")).toBe("downgrade");
    expect(resolveFirmwareChangeDirection("1.10.0", "1.9.0")).toBe("downgrade");
  });

  it("detects same", () => {
    expect(resolveFirmwareChangeDirection("1.0.0", "1.0.0")).toBe("same");
    expect(resolveFirmwareChangeDirection("esp32_counter_v1.0.1", "esp32_counter_v1.0.1")).toBe(
      "same",
    );
  });

  it("returns unknown when not SemVer-comparable", () => {
    expect(resolveFirmwareChangeDirection("build-a", "build-b")).toBe("unknown");
    expect(resolveFirmwareChangeDirection("", "1.0.0")).toBe("unknown");
    expect(resolveFirmwareChangeDirection("1.0.0", null)).toBe("unknown");
  });
});
