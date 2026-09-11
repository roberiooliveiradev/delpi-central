import { describe, expect, it } from "vitest";

import {
  buildProductionPulseRealtimeWsUrl,
  isHubRealtimeHint,
  parseProductionPulseRealtimeEvent,
} from "./constants";
import { isHubInteractionBlocking } from "./hubInteractionGuard";

describe("production pulse realtime constants", () => {
  it("builds ws url under production-pulse-api", () => {
    const url = buildProductionPulseRealtimeWsUrl({
      token: "abc",
      clientId: "client-1",
    });
    expect(url).toContain("/apps/production-pulse-api/v1/realtime/ws");
    expect(url).toContain("token=abc");
    expect(url).toContain("client_id=client-1");
  });

  it("parses hub hint events", () => {
    const event = parseProductionPulseRealtimeEvent(
      JSON.stringify({ type: "device.updated", deviceId: "d1", branch: "01" }),
    );
    expect(event?.type).toBe("device.updated");
    expect(event && isHubRealtimeHint(event)).toBe(true);
  });
});

describe("hub interaction guard", () => {
  it("blocks during link mode and drag", () => {
    expect(
      isHubInteractionBlocking({
        linkMode: true,
        dragging: false,
        openLayer: "none",
      }),
    ).toBe(true);
    expect(
      isHubInteractionBlocking({
        linkMode: false,
        dragging: true,
        openLayer: "none",
      }),
    ).toBe(true);
  });

  it("blocks overlay layers and allows idle canvas", () => {
    expect(
      isHubInteractionBlocking({
        linkMode: false,
        dragging: false,
        openLayer: "menu",
      }),
    ).toBe(true);
    expect(
      isHubInteractionBlocking({
        linkMode: false,
        dragging: false,
        openLayer: "none",
      }),
    ).toBe(false);
  });
});
