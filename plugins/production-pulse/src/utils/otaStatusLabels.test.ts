import { describe, expect, it } from "vitest";

import {
  formatOtaProgressDisplay,
  resolveOtaProgressPercent,
} from "./otaStatusLabels";

describe("resolveOtaProgressPercent", () => {
  it("returns null for authorized and pending (awaiting chip)", () => {
    expect(resolveOtaProgressPercent({ status: "authorized" })).toBeNull();
    expect(resolveOtaProgressPercent({ status: "pending" })).toBeNull();
    expect(resolveOtaProgressPercent({ status: "authorized", progressPercent: 5 })).toBeNull();
  });

  it("uses real percent only while downloading", () => {
    expect(
      resolveOtaProgressPercent({ status: "downloading", progressPercent: 42 }),
    ).toBe(42);
    expect(resolveOtaProgressPercent({ status: "downloading" })).toBeNull();
  });

  it("maps applying as null (no fake 95) and updated as 100", () => {
    expect(resolveOtaProgressPercent({ status: "applying" })).toBeNull();
    expect(resolveOtaProgressPercent({ status: "applying", progressPercent: 95 })).toBeNull();
    expect(resolveOtaProgressPercent({ status: "updated" })).toBe(100);
  });
});

describe("formatOtaProgressDisplay", () => {
  it("shows awaiting device for authorized/pending", () => {
    expect(formatOtaProgressDisplay({ status: "authorized" })).toBe(
      "Aguardando dispositivo",
    );
    expect(formatOtaProgressDisplay({ status: "pending" })).toBe(
      "Aguardando dispositivo",
    );
  });

  it("shows applying label without percent", () => {
    expect(formatOtaProgressDisplay({ status: "applying" })).toBe(
      "Aplicando firmware",
    );
  });

  it("shows percent or em dash otherwise", () => {
    expect(formatOtaProgressDisplay({ status: "downloading", progressPercent: 17 })).toBe("17%");
    expect(formatOtaProgressDisplay({ status: "downloading" })).toBe("—");
    expect(formatOtaProgressDisplay({ status: "updated" })).toBe("100%");
  });
});
