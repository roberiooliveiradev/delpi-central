import { describe, expect, it } from "vitest";

import { resolveMetricThresholdLevel } from "./gaugeThresholds";

describe("resolveMetricThresholdLevel", () => {
  const thresholds = {
    temperature_c: { warnAbove: 75, dangerAbove: 90 },
  };

  it("returns normal below warn threshold", () => {
    expect(resolveMetricThresholdLevel("temperature_c", 67, thresholds)).toBe("normal");
  });

  it("returns warn between warn and danger", () => {
    expect(resolveMetricThresholdLevel("temperature_c", 78, thresholds)).toBe("warn");
  });

  it("returns danger at or above danger threshold", () => {
    expect(resolveMetricThresholdLevel("temperature_c", 92, thresholds)).toBe("danger");
  });
});
