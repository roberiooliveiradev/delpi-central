import { describe, expect, it } from "vitest";

import type { DriverListItem } from "../api/productionPulseApi";
import {
  resolveDriverProtocolDisplay,
  summarizeDriverCatalogItem,
} from "./driverCatalogDisplay";

function baseDriver(overrides: Partial<DriverListItem> = {}): DriverListItem {
  return {
    key: "esp8266_counter_v1",
    protocolKind: "http_counter",
    roleKey: "counter",
    labelPt: "ESP8266 — contador",
    metrics: [{ key: "hits", type: "integer", labelPt: "Golpes" }],
    commands: ["increment", "reset"],
    operatorSurface: "counter_controls",
    operatorEligible: true,
    poll: { timeoutMs: 2000 },
    ...overrides,
  };
}

describe("resolveDriverProtocolDisplay", () => {
  it("maps known protocol kinds", () => {
    expect(resolveDriverProtocolDisplay("http_counter").shortLabel).toBe("Contador");
    expect(resolveDriverProtocolDisplay("http_gauge").label).toBe("Sensores HTTP");
  });

  it("keeps unknown protocol as-is", () => {
    expect(resolveDriverProtocolDisplay("custom_proto")).toEqual({
      kind: "custom_proto",
      label: "custom_proto",
      shortLabel: "custom_proto",
    });
  });
});

describe("summarizeDriverCatalogItem", () => {
  it("summarizes metrics, commands and archive state", () => {
    const summary = summarizeDriverCatalogItem(
      baseDriver({ archivedAt: "2026-01-01T00:00:00Z", operatorEligible: false }),
    );
    expect(summary.metricCount).toBe(1);
    expect(summary.commandCount).toBe(2);
    expect(summary.archived).toBe(true);
    expect(summary.eligible).toBe(false);
    expect(summary.protocol.shortLabel).toBe("Contador");
  });
});
