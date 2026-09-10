import { describe, expect, it } from "vitest";

import {
  formatAdminEntity,
  hubFocusToPanel,
  parseAdminDrawer,
  parseAdminEntity,
  parseAdminModal,
  parseAdminPanel,
  resolveAdminModalFromQuery,
} from "./adminHubUiState";

describe("adminHubUiState", () => {
  it("parses and formats entity refs", () => {
    expect(parseAdminEntity("device:abc")).toEqual({ type: "device", id: "abc" });
    expect(parseAdminEntity("firmware:fw-1")).toEqual({ type: "firmware", id: "fw-1" });
    expect(parseAdminEntity("job:j1")).toEqual({ type: "job", id: "j1" });
    expect(parseAdminEntity("driver:esp8266_counter_v1")).toEqual({
      type: "driver",
      id: "esp8266_counter_v1",
    });
    expect(parseAdminEntity("unknown:x")).toBeNull();
    expect(formatAdminEntity({ type: "device", id: "x" })).toBe("device:x");
    expect(formatAdminEntity({ type: "driver", id: "d1" })).toBe("driver:d1");
  });

  it("parses panels and focus aliases", () => {
    expect(parseAdminPanel("jobs")).toBe("jobs");
    expect(parseAdminPanel("fleet-health")).toBe("fleet-health");
    expect(parseAdminPanel("drivers")).toBe("drivers");
    expect(parseAdminPanel("nope")).toBeNull();
    expect(hubFocusToPanel("catalog")).toBe("firmwares");
    expect(hubFocusToPanel("jobs")).toBe("jobs");
  });

  it("parses canonical modal keys", () => {
    expect(parseAdminModal("device-create")).toBe("device-create");
    expect(parseAdminModal("firmware-detail")).toBe("firmware-detail");
    expect(parseAdminModal("device-detail")).toBe("device-detail");
    expect(parseAdminModal("driver-create")).toBe("driver-create");
    expect(parseAdminModal("driver-detail")).toBe("driver-detail");
    expect(parseAdminModal("job-detail")).toBe("job-detail");
    expect(parseAdminModal("ota-schedule")).toBe("ota-schedule");
    expect(parseAdminModal("nope")).toBeNull();
  });

  it("aliases legacy drawer=firmware-edit to firmware-detail", () => {
    expect(parseAdminDrawer("firmware-edit")).toBe("firmware-detail");
    expect(parseAdminModal("firmware-edit")).toBe("firmware-detail");
    expect(resolveAdminModalFromQuery({ drawer: "device-create" })).toBe("device-create");
    expect(resolveAdminModalFromQuery({ modal: "firmware-detail", drawer: "device-create" })).toBe(
      "firmware-detail",
    );
  });
});
