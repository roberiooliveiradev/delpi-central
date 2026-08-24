import { describe, expect, it } from "vitest";

import { isDeliveryMapRowReported } from "./deliveryMapRowReported";

describe("isDeliveryMapRowReported", () => {
  it("não risca com apontamento parcial no PA (50%)", () => {
    expect(
      isDeliveryMapRowReported({
        conjunto_key: "101600",
        total: 4,
        completed: 1,
        in_progress: 1,
        percent: 50,
      }),
    ).toBe(false);
  });

  it("risca quando o conjunto atinge 100%", () => {
    expect(
      isDeliveryMapRowReported({
        conjunto_key: "101600",
        total: 4,
        completed: 4,
        in_progress: 0,
        percent: 100,
      }),
    ).toBe(true);
  });

  it("não risca sem progresso carregado", () => {
    expect(isDeliveryMapRowReported(undefined)).toBe(false);
  });
});
