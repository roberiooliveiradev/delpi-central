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

  it("maps applying and updated phases", () => {
    expect(resolveOtaProgressPercent({ status: "applying" })).toBe(95);
    expect(resolveOtaProgressPercent({ status: "updated" })).toBe(100);
  });
});

describe("formatOtaProgressDisplay", () => {
  it("shows awaiting chip for authorized/pending", () => {
    expect(formatOtaProgressDisplay({ status: "authorized" })).toBe("Aguardando chip");
    expect(formatOtaProgressDisplay({ status: "pending" })).toBe("Aguardando chip");
  });

  it("shows percent or em dash otherwise", () => {
    expect(formatOtaProgressDisplay({ status: "downloading", progressPercent: 17 })).toBe("17%");
    expect(formatOtaProgressDisplay({ status: "downloading" })).toBe("—");
    expect(formatOtaProgressDisplay({ status: "updated" })).toBe("100%");
  });
});
