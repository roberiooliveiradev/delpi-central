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

  it("accepts minimum poll interval of 1 ms", () => {
    const errors = validateDeviceForm(
      {
        ...DEFAULT_DEVICE_FORM_VALUES,
        name: "ESP A",
        ipAddress: "192.168.20.2",
        pollIntervalMs: 1,
      },
      DEFAULT_BINDING_VALUES,
    );
    expect(errors.pollIntervalMs).toBeUndefined();
  });

  it("rejects poll interval below minimum", () => {
    const errors = validateDeviceForm(
      {
        ...DEFAULT_DEVICE_FORM_VALUES,
        name: "ESP A",
        ipAddress: "192.168.20.2",
        pollIntervalMs: 0,
      },
      DEFAULT_BINDING_VALUES,
    );
    expect(errors.pollIntervalMs).toContain("1");
    expect(errors.pollIntervalMs).toContain("300000");
  });

  it("rejects debounce outside range", () => {
    const errors = validateDeviceForm(
      {
        ...DEFAULT_DEVICE_FORM_VALUES,
        name: "ESP A",
        ipAddress: "192.168.20.2",
        debounceMs: "0",
      },
      DEFAULT_BINDING_VALUES,
    );
    expect(errors.debounceMs).toContain("1");
  });

  it("formats probe metrics", () => {
    expect(formatPrimaryMetricFromProbe({ counter: 42 })).toBe("Golpes: 42");
  });
});
