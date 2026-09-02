import { describe, expect, it } from "vitest";

import { DEFAULT_BINDING_VALUES, DEFAULT_DEVICE_FORM_VALUES } from "../types/form";
import {
  formatPrimaryMetricFromProbe,
  hasBindingInput,
  validateDeviceForm,
  validateIpv4,
} from "./deviceFormValidation";

describe("deviceFormValidation", () => {
  it("validates ipv4", () => {
    expect(validateIpv4("192.168.20.2")).toBe(true);
    expect(validateIpv4("999.1.1.1")).toBe(false);
  });

  it("requires core device fields", () => {
    const errors = validateDeviceForm(
      { ...DEFAULT_DEVICE_FORM_VALUES, name: "", ipAddress: "bad" },
      DEFAULT_BINDING_VALUES,
    );
    expect(errors.name).toBeTruthy();
    expect(errors.ipAddress).toBeTruthy();
  });

  it("requires equipment label when binding input exists", () => {
    const errors = validateDeviceForm(
      {
        ...DEFAULT_DEVICE_FORM_VALUES,
        name: "ESP A",
        ipAddress: "192.168.20.2",
      },
      { ...DEFAULT_BINDING_VALUES, equipmentLabel: "Ventilador A" },
      { requireBinding: true },
    );
    expect(errors.binding?.equipmentLabel).toBeUndefined();
  });

  it("detects binding input", () => {
    expect(hasBindingInput(DEFAULT_BINDING_VALUES)).toBe(false);
    expect(
      hasBindingInput({ ...DEFAULT_BINDING_VALUES, equipmentLabel: "Motor A" }),
    ).toBe(true);
  });

  it("accepts half-second poll interval", () => {
    const errors = validateDeviceForm(
      {
        ...DEFAULT_DEVICE_FORM_VALUES,
        name: "ESP A",
        ipAddress: "192.168.20.2",
        pollIntervalSeconds: 0.5,
      },
      DEFAULT_BINDING_VALUES,
    );
    expect(errors.pollIntervalSeconds).toBeUndefined();
  });

  it("rejects poll interval below minimum", () => {
    const errors = validateDeviceForm(
      {
        ...DEFAULT_DEVICE_FORM_VALUES,
        name: "ESP A",
        ipAddress: "192.168.20.2",
        pollIntervalSeconds: 0.4,
      },
      DEFAULT_BINDING_VALUES,
    );
    expect(errors.pollIntervalSeconds).toContain("0.5");
    expect(errors.pollIntervalSeconds).toContain("300");
  });

  it("formats probe metrics", () => {
    expect(formatPrimaryMetricFromProbe({ counter: 42 })).toBe("Golpes: 42");
  });
});
