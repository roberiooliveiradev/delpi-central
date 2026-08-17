import { describe, expect, it } from "vitest";

import {
  buildSettingsWorkspaceTree,
  parseSettingsSectionFromPath,
  resolveActiveSettingsNodeId,
} from "./settingsWorkspaceNav";

describe("parseSettingsSectionFromPath", () => {
  it("resolve seção por path canônico EN e legado PT", () => {
    expect(parseSettingsSectionFromPath("/apps/transformometro/settings/units")).toBe(
      "unidades",
    );
    expect(parseSettingsSectionFromPath("/apps/transformometro/settings/departments")).toBe(
      "departamentos",
    );
    expect(parseSettingsSectionFromPath("/apps/transformometro/settings/shared-resources")).toBe(
      "recursos",
    );
    expect(parseSettingsSectionFromPath("/apps/transformometro/configuracoes/unidades")).toBe(
      "unidades"
    );
    expect(parseSettingsSectionFromPath("/apps/transformometro/configuracoes/departamentos")).toBe(
      "departamentos"
    );
    expect(parseSettingsSectionFromPath("/apps/transformometro/configuracoes/recursos")).toBe(
      "recursos"
    );
  });

  it("aceita rotas legadas", () => {
    expect(parseSettingsSectionFromPath("/apps/transformometro/cadastros/unidades")).toBe("unidades");
    expect(parseSettingsSectionFromPath("/apps/transformometro/filiais")).toBe("unidades");
    expect(parseSettingsSectionFromPath("/apps/transformometro/setores")).toBe("departamentos");
  });
});

describe("buildSettingsWorkspaceTree", () => {
  it("monta pastas com itens filhos", () => {
    const tree = buildSettingsWorkspaceTree({
      filiais: [
        {
          filial_id: "f1",
          codigo_filial: "01",
          nome_filial: "Matriz",
          status_filial: "ativo",
        },
      ],
      setores: [],
      recursos: [],
    });
    expect(tree).toHaveLength(3);
    expect(tree[0]?.children).toHaveLength(1);
    expect(tree[0]?.children?.[0]?.id).toBe("filial:f1");
  });
});

describe("resolveActiveSettingsNodeId", () => {
  it("marca subseção de recurso", () => {
    expect(
      resolveActiveSettingsNodeId({
        view: "recurso",
        recursoId: "r1",
        recursoSection: "custos",
      })
    ).toBe("recurso-section:r1:custos");
  });
});
