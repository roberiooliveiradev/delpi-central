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

  it("SIPAT herda manage e exige flags dedicadas", () => {
    expect(canUnit(sampleAccess, "01", "sipat_manage")).toBe(true);
    expect(canUnit(sampleAccess, "01", "sipat_view")).toBe(true);
    expect(canUnit(sampleAccess, "02", "sipat_view")).toBe(false);

    const sipatOnly = {
      ...sampleAccess,
      units: [
        {
          id: "01" as const,
          label: "Santa Catarina",
          view: false,
          manage: false,
          sign: false,
          sipat_view: true,
          sipat_manage: false,
        },
      ],
    };
    expect(canUnit(sipatOnly, "01", "sipat_view")).toBe(true);
    expect(canUnit(sipatOnly, "01", "sipat_manage")).toBe(false);
    expect(readableUnits(sipatOnly)).toHaveLength(1);
  });
});
