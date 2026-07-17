import { describe, expect, it } from "vitest";

import { canUnit, readableUnits } from "../security/cipaAccess";

const sampleAccess = {
  admin: false,
  can_view: true,
  can_manage: true,
  can_sign: false,
  units: [
    {
      id: "01" as const,
      label: "Santa Catarina",
      view: true,
      manage: true,
      sign: false,
    },
    {
      id: "02" as const,
      label: "Espírito Santo",
      view: false,
      manage: false,
      sign: true,
    },
  ],
};

describe("cipaAccess", () => {
  it("filtra unidades legíveis", () => {
    expect(readableUnits(sampleAccess)).toHaveLength(1);
    expect(readableUnits(sampleAccess)[0]?.id).toBe("01");
  });

  it("valida ação por unidade", () => {
    expect(canUnit(sampleAccess, "01", "manage")).toBe(true);
    expect(canUnit(sampleAccess, "02", "manage")).toBe(false);
    expect(canUnit(sampleAccess, "02", "sign")).toBe(true);
  });
});
