import { describe, expect, it } from "vitest";

import { canViewMywegNeeds, defaultDemandOrigin } from "./demandOrigin";

const WEG_VIEW = "production-control.myweg-needs.view";

describe("Demandas: origem inicial por filial (#1554)", () => {
  it("na filial 02, usa Todas para quem possui acesso MyWEG", () => {
    expect(defaultDemandOrigin("02", canViewMywegNeeds([WEG_VIEW]))).toBe("both");
    expect(defaultDemandOrigin("02", canViewMywegNeeds([], true))).toBe("both");
  });

  it("na filial 01, mantem Protheus inclusive para superadmin", () => {
    expect(defaultDemandOrigin("01", canViewMywegNeeds([WEG_VIEW]))).toBe("protheus");
    expect(defaultDemandOrigin("01", canViewMywegNeeds([], true))).toBe("protheus");
  });

  it("sem permissao MyWEG na filial 02, nao usa uma fonte restrita", () => {
    expect(defaultDemandOrigin("02", canViewMywegNeeds(["production-control.demand.view"]))).toBe(
      "protheus",
    );
    expect(defaultDemandOrigin("02", canViewMywegNeeds(undefined))).toBe("protheus");
    expect(canViewMywegNeeds([WEG_VIEW])).toBe(true);
    expect(canViewMywegNeeds([])).toBe(false);
  });
});
