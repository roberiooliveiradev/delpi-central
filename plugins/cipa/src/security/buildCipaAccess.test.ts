import { describe, expect, it } from "vitest";

import { buildCipaAccessFromPermissions } from "./buildCipaAccess";

describe("buildCipaAccessFromPermissions", () => {
  it("monta escopo de visualização por unidade", () => {
    const access = buildCipaAccessFromPermissions([
      "cipa.view",
      "cipa.unit.filial-01",
    ]);
    expect(access.can_view).toBe(true);
    expect(access.can_manage).toBe(false);
    expect(access.units).toEqual([
      {
        id: "01",
        label: "Santa Catarina",
        view: true,
        manage: false,
        sign: false,
      },
    ]);
  });

  it("manage implica leitura na unidade", () => {
    const access = buildCipaAccessFromPermissions([
      "cipa.manage",
      "cipa.unit.filial-02",
    ]);
    expect(access.units[0]).toMatchObject({
      id: "02",
      view: true,
      manage: true,
      sign: false,
    });
  });

  it("admin dispensa demais permissões", () => {
    const access = buildCipaAccessFromPermissions([], true);
    expect(access.admin).toBe(true);
    expect(access.units).toHaveLength(2);
  });
});
