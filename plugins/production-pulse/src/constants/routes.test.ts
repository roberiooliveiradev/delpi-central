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
  it("maps firmwares, firmware-new, firmware-jobs and firmware-links", () => {
    expect(parseProductionPulseRoute("/apps/production-pulse/firmwares").kind).toBe("firmwares");
    expect(parseProductionPulseRoute("/apps/production-pulse/firmwares/new").kind).toBe(
      "firmwareNew",
    );
    expect(parseProductionPulseRoute("/apps/production-pulse/firmware-jobs", "?branch=02")).toEqual({
      kind: "firmwareJobs",
      branch: "02",
    });
    expect(
      parseProductionPulseRoute(
        "/apps/production-pulse/firmware-links",
        "?branch=01&firmwareKey=esp8266_counter_v1&focus=catalog",
      ),
    ).toEqual({
      kind: "firmwareLinks",
      branch: "01",
      firmwareKey: "esp8266_counter_v1",
      focus: "catalog",
    });
  });

  it("keeps firmware-jobs parse for App redirect to firmware-links", () => {
    const route = parseProductionPulseRoute("/apps/production-pulse/firmware-jobs", "?branch=02");
    expect(route).toEqual({ kind: "firmwareJobs", branch: "02" });
  });

  it("maps firmware-links entity panel modal query", () => {
    expect(
      parseProductionPulseRoute(
        "/apps/production-pulse/firmware-links",
        "?branch=02&entity=device:abc&panel=jobs&modal=device-create",
      ),
    ).toEqual({
      kind: "firmwareLinks",
      branch: "02",
      firmwareKey: undefined,
      focus: undefined,
      entity: "device:abc",
      panel: "jobs",
      modal: "device-create",
      drawer: undefined,
    });
  });

  it("keeps legacy drawer query on firmware-links parse", () => {
    expect(
      parseProductionPulseRoute(
        "/apps/production-pulse/firmware-links",
        "?branch=02&entity=device:abc&panel=jobs&drawer=device-create",
      ),
    ).toEqual({
      kind: "firmwareLinks",
      branch: "02",
      firmwareKey: undefined,
      focus: undefined,
      entity: "device:abc",
      panel: "jobs",
      modal: undefined,
      drawer: "device-create",
    });
  });

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
    expect(parseProductionPulseRoute("/apps/production-pulse/devices/abc-123", "?tab=firmware")).toEqual({
      kind: "deviceDetail",
      deviceId: "abc-123",
      tab: "firmware",
    });
    expect(parseDeviceDetailTab("invalid")).toBe("overview");
  });

  it("builds detail path with tab", () => {
    expect(productionPulseDeviceDetailPath("abc-123")).toBe("/apps/production-pulse/devices/abc-123");
    expect(productionPulseDeviceDetailPath("abc-123", "history")).toBe(
      "/apps/production-pulse/devices/abc-123?tab=history",
    );
    expect(productionPulseDeviceDetailPath("abc-123", "firmware")).toBe(
      "/apps/production-pulse/devices/abc-123?tab=firmware",
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
