import { describe, expect, it } from "vitest";

import {
  parseProductionPulseRoute,
  productionPulseDeviceDetailPath,
  productionPulseDeviceNewPath,
  productionPulseOperatorDevicePath,
  productionPulseOperatorPath,
  productionPulseOperatorPlacementPath,
  parseDeviceDetailTab,
} from "./routes";

describe("parseProductionPulseRoute", () => {
  it("maps panel root", () => {
    expect(parseProductionPulseRoute("/apps/production-pulse").kind).toBe("panel");
  });

  it("maps operator hub with filters", () => {
    expect(parseProductionPulseRoute("/apps/production-pulse/operator", "?branch=02&anchorType=machine&search=motor")).toEqual({
      kind: "operatorHub",
      branch: "02",
      anchorType: "machine",
      search: "motor",
    });
  });

  it("maps operator picker and device routes", () => {
    expect(
      parseProductionPulseRoute(
        "/apps/production-pulse/operator/placements/wc%3A01%3ACT-53",
        "?branch=01",
      ),
    ).toEqual({
      kind: "operatorPicker",
      placementKey: "wc:01:CT-53",
      branch: "01",
    });

    expect(
      parseProductionPulseRoute("/apps/production-pulse/operator/devices/dev-1", "?branch=01&placementKey=wc:01:CT-53"),
    ).toEqual({
      kind: "operatorDevice",
      deviceId: "dev-1",
      branch: "01",
      placementKey: "wc:01:CT-53",
    });
  });

  it("maps device create and edit routes", () => {
    expect(parseProductionPulseRoute("/apps/production-pulse/devices/new", "?branch=02")).toEqual({
      kind: "deviceNew",
      branch: "02",
    });
    expect(parseProductionPulseRoute("/apps/production-pulse/devices/abc-123/edit").kind).toBe(
      "deviceEdit",
    );
    expect(parseProductionPulseRoute("/apps/production-pulse/devices/abc-123").kind).toBe(
      "deviceDetail",
    );
  });

  it("maps device detail tabs from query", () => {
    expect(parseProductionPulseRoute("/apps/production-pulse/devices/abc-123", "?tab=history")).toEqual({
      kind: "deviceDetail",
      deviceId: "abc-123",
      tab: "history",
    });
    expect(parseProductionPulseRoute("/apps/production-pulse/devices/abc-123", "?tab=commands")).toEqual({
      kind: "deviceDetail",
      deviceId: "abc-123",
      tab: "commands",
    });
    expect(parseDeviceDetailTab("invalid")).toBe("overview");
  });

  it("builds detail path with tab", () => {
    expect(productionPulseDeviceDetailPath("abc-123")).toBe("/apps/production-pulse/devices/abc-123");
    expect(productionPulseDeviceDetailPath("abc-123", "history")).toBe(
      "/apps/production-pulse/devices/abc-123?tab=history",
    );
  });

  it("builds operator paths", () => {
    expect(productionPulseOperatorPath("01")).toBe("/apps/production-pulse/operator?branch=01");
    expect(productionPulseOperatorPlacementPath("wc:01:CT-53", "01")).toBe(
      "/apps/production-pulse/operator/placements/wc%3A01%3ACT-53?branch=01",
    );
    expect(productionPulseOperatorDevicePath("dev-1", "01", "wc:01:CT-53")).toBe(
      "/apps/production-pulse/operator/devices/dev-1?branch=01&placementKey=wc%3A01%3ACT-53",
    );
  });

  it("builds new device path with branch", () => {
    expect(productionPulseDeviceNewPath("01")).toBe("/apps/production-pulse/devices/new?branch=01");
  });

  it("returns unknown for foreign paths", () => {
    expect(parseProductionPulseRoute("/apps/production-pulse/legacy").kind).toBe("unknown");
  });
});
