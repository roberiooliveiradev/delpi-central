import { describe, expect, it } from "vitest";

import {
  openFirmwareVersionAction,
  parseOpenFirmwareVersionAction,
} from "./openFirmwareVersionAction";

describe("openFirmwareVersionAction", () => {
  it("round-trips firmware id", () => {
    expect(parseOpenFirmwareVersionAction(openFirmwareVersionAction("fw-123"))).toBe("fw-123");
  });

  it("rejects unrelated actions", () => {
    expect(parseOpenFirmwareVersionAction("edit")).toBeNull();
    expect(parseOpenFirmwareVersionAction("open-version:")).toBeNull();
  });
});
