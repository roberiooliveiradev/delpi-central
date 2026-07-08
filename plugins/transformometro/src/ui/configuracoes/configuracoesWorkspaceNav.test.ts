import { describe, expect, it } from "vitest";

import {
  buildConfiguracoesWorkspaceTree,
  parseConfiguracoesSectionFromPath,
  resolveActiveConfiguracoesNodeId,
} from "./configuracoesWorkspaceNav";

describe("parseConfiguracoesSectionFromPath", () => {
  it("resolve seção por path canônico", () => {
    expect(parseConfiguracoesSectionFromPath("/apps/transformometro/configuracoes/unidades")).toBe(
      "unidades"
    );
    expect(parseConfiguracoesSectionFromPath("/apps/transformometro/configuracoes/departamentos")).toBe(
      "departamentos"
    );
    expect(parseConfiguracoesSectionFromPath("/apps/transformometro/configuracoes/recursos")).toBe(
      "recursos"
    );
  });

  it("aceita rotas legadas", () => {
    expect(parseConfiguracoesSectionFromPath("/apps/transformometro/cadastros/unidades")).toBe("unidades");
    expect(parseConfiguracoesSectionFromPath("/apps/transformometro/filiais")).toBe("unidades");
    expect(parseConfiguracoesSectionFromPath("/apps/transformometro/setores")).toBe("departamentos");
  });
});

describe("buildConfiguracoesWorkspaceTree", () => {
  it("monta pastas com itens filhos", () => {
    const tree = buildConfiguracoesWorkspaceTree({
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

describe("resolveActiveConfiguracoesNodeId", () => {
  it("marca subseção de recurso", () => {
    expect(
      resolveActiveConfiguracoesNodeId({
        view: "recurso",
        recursoId: "r1",
        recursoSection: "custos",
      })
    ).toBe("recurso-section:r1:custos");
  });
});
