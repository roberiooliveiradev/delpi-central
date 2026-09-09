import { describe, expect, it } from "vitest";

import {
  formatAdminEntity,
  hubFocusToPanel,
  parseAdminDrawer,
  parseAdminEntity,
  parseAdminPanel,
} from "./adminHubUiState";

describe("adminHubUiState", () => {
  it("parses entity refs (positive)", () => {
    expect(parseAdminEntity("device:abc")).toEqual({ type: "device", id: "abc" });
    expect(parseAdminEntity("firmware:fw-1")).toEqual({ type: "firmware", id: "fw-1" });
    expect(parseAdminEntity("job:j:with:colons")).toEqual({ type: "job", id: "j:with:colons" });
  });

  it("rejects invalid entity (negative)", () => {
    expect(parseAdminEntity(null)).toBeNull();
    expect(parseAdminEntity("unknown:x")).toBeNull();
    expect(parseAdminEntity("device:")).toBeNull();
  });

  it("formats entity and maps legacy focus (sibling)", () => {
    expect(formatAdminEntity({ type: "device", id: "1" })).toBe("device:1");
    expect(hubFocusToPanel("catalog")).toBe("firmwares");
    expect(hubFocusToPanel("jobs")).toBe("jobs");
    expect(hubFocusToPanel("canvas")).toBeNull();
    expect(parseAdminPanel("devices")).toBe("devices");
    expect(parseAdminPanel("nope")).toBeNull();
    expect(parseAdminDrawer("firmware-create")).toBe("firmware-create");
    expect(parseAdminDrawer("delete-draft")).toBeNull();
  });
});
