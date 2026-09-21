import { describe, expect, it } from "vitest";

import { resolveStrategicIndicatorsBranch } from "./strategicIndicatorsBranch";

describe("resolveStrategicIndicatorsBranch", () => {
  it("omite branch no consolidado", () => {
    expect(resolveStrategicIndicatorsBranch("consolidated", ["01"])).toBeUndefined();
  });

  it("encaminha a unidade única nas visões Unidade e Departamento", () => {
    expect(resolveStrategicIndicatorsBranch("filial", ["01"])).toBe("01");
    expect(resolveStrategicIndicatorsBranch("department", ["02"])).toBe("02");
  });

  it("omite branch quando há várias unidades", () => {
    expect(resolveStrategicIndicatorsBranch("filial", ["01", "02"])).toBeUndefined();
  });
});
