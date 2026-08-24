import { describe, expect, it } from "vitest";

import { buildDeliveryMapExportFileName } from "./deliveryMapExportFileName";

describe("buildDeliveryMapExportFileName", () => {
  const exportedAt = new Date(2026, 7, 24, 15, 30);

  it("usa MATRIZ na filial 01", () => {
    expect(buildDeliveryMapExportFileName("01", exportedAt)).toBe("MAPA 24-08-2026 MATRIZ");
  });

  it("usa FILIAL na filial 02", () => {
    expect(buildDeliveryMapExportFileName("02", exportedAt)).toBe("MAPA 24-08-2026 FILIAL");
  });
});
