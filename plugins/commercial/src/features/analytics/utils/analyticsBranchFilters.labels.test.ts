import { describe, expect, it } from "vitest";

import {
  ANALYTICS_CONVERSION_SERIES_LABELS,
  ANALYTICS_OTD_SERIES_LABELS,
  ANALYTICS_ROL_SERIES_LABELS,
  ANALYTICS_UNIT_FIELD_LABEL,
  formatOperationalUnitCode,
} from "./analyticsBranchFilters";

describe("analyticsBranchFilters — rótulos de unidade", () => {
  it("mapeia códigos TOTVS para nomes de estado", () => {
    expect(formatOperationalUnitCode("01")).toBe("Santa Catarina");
    expect(formatOperationalUnitCode("02")).toBe("Espírito Santo");
  });

  it("expõe séries ROL/OTD/conversão alinhadas ao dashboard", () => {
    expect(ANALYTICS_UNIT_FIELD_LABEL).toBe("Unidade (indicadores)");
    expect(ANALYTICS_ROL_SERIES_LABELS.unit01).toBe("ROL Santa Catarina");
    expect(ANALYTICS_ROL_SERIES_LABELS.unit02).toBe("ROL Espírito Santo");
    expect(ANALYTICS_OTD_SERIES_LABELS.unit01).toBe("OTD Santa Catarina");
    expect(ANALYTICS_OTD_SERIES_LABELS.unit02).toBe("OTD Espírito Santo");
    expect(ANALYTICS_CONVERSION_SERIES_LABELS.unit01).toBe("Conversão Santa Catarina");
    expect(ANALYTICS_CONVERSION_SERIES_LABELS.unit02).toBe("Conversão Espírito Santo");
  });
});
