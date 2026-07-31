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
        sipat_view: false,
        sipat_manage: false,
      },
    ]);
  });

  it("manage implica leitura e SIPAT na unidade", () => {
    const access = buildCipaAccessFromPermissions([
      "cipa.manage",
      "cipa.unit.filial-02",
    ]);
    expect(access.units[0]).toMatchObject({
      id: "02",
      view: true,
      manage: true,
      sign: false,
      sipat_view: true,
      sipat_manage: true,
    });
  });

  it("sipat.view + unidade habilita só SIPAT", () => {
    const access = buildCipaAccessFromPermissions([
      "cipa.sipat.view",
      "cipa.unit.filial-01",
    ]);
    expect(access.can_sipat_view).toBe(true);
    expect(access.units[0]).toMatchObject({
      id: "01",
      view: false,
      sipat_view: true,
      sipat_manage: false,
    });
  });

  it("admin dispensa demais permissões", () => {
    const access = buildCipaAccessFromPermissions([], true);
    expect(access.admin).toBe(true);
    expect(access.units).toHaveLength(2);
  });
});
