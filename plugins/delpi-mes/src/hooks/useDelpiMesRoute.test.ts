import { describe, expect, it } from "vitest";

import { buildDelpiMesHref, parseDelpiMesRoute } from "./useDelpiMesRoute";

describe("Delpi MES routing", () => {
  it("defaults the product root to monitoring and branch 01", () => {
    expect(parseDelpiMesRoute("/apps/delpi-mes", "")).toEqual({ area: "monitoring", branch: "01", workCenter: null });
  });

  it("preserves area and branch in a shareable URL", () => {
    expect(parseDelpiMesRoute("/apps/delpi-mes/downtimes", "?branch=02")).toEqual({ area: "downtimes", branch: "02", workCenter: null });
    expect(buildDelpiMesHref("history", "02")).toBe("/apps/delpi-mes/history?branch=02");
  });

  it("parses the selected work center only on monitoring", () => {
    expect(parseDelpiMesRoute("/apps/delpi-mes/monitoring", "?branch=01&workCenter=CT-35")).toEqual({ area: "monitoring", branch: "01", workCenter: "CT-35" });
    expect(parseDelpiMesRoute("/apps/delpi-mes/downtimes", "?branch=01&workCenter=CT-35").workCenter).toBeNull();
    expect(buildDelpiMesHref("monitoring", "01", "CT 35")).toBe("/apps/delpi-mes/monitoring?branch=01&workCenter=CT%2035");
  });
});
