import { describe, expect, it } from "vitest";

import { PRODUCTION_APPOINTMENTS_BASE_PATH } from "./branches";
import { buildOpDetailPath, parseAppointmentsPath } from "./routes";

describe("parseAppointmentsPath", () => {
  it("detecta dashboard SC/ES", () => {
    expect(parseAppointmentsPath("/apps/production-appointments/sc")).toEqual({
      view: "dashboard",
      branchRoute: "SC",
    });
    expect(parseAppointmentsPath("/apps/production-appointments/es")).toEqual({
      view: "dashboard",
      branchRoute: "ES",
    });
  });

  it("detecta detalhe da OP", () => {
    expect(parseAppointmentsPath("/apps/production-appointments/sc/op/000123")).toEqual({
      view: "op-detail",
      branchRoute: "SC",
      productionOrder: "000123",
    });
  });

  it("decodifica OP com caracteres especiais", () => {
    const path = `${PRODUCTION_APPOINTMENTS_BASE_PATH}/sc/op/${encodeURIComponent("OP 1/2")}`;
    expect(parseAppointmentsPath(path)).toEqual({
      view: "op-detail",
      branchRoute: "SC",
      productionOrder: "OP 1/2",
    });
  });
});

describe("buildOpDetailPath", () => {
  it("monta path com período", () => {
    expect(
      buildOpDetailPath("SC", "000123", {
        dateStart: "2026-06-16",
        dateEnd: "2026-07-15",
      }),
    ).toBe(
      "/apps/production-appointments/sc/op/000123?date_start=2026-06-16&date_end=2026-07-15",
    );
  });
});
