import { describe, expect, it } from "vitest";

import {
  buildProcessoWorkspaceTree,
  defaultInstanciaSection,
  defaultRevisaoSection,
  parseInstanciaSectionFromHash,
  parseRevisaoSectionFromHash,
  resolveActiveWorkspaceNodeId,
} from "./processoWorkspaceNav";

const processo = {
  processo_id: "proc-1",
  codigo_processo: "PROC-0001",
  nome_processo: "Processo teste",
} as const;

const instancia = {
  instancia_id: "inst-1",
  processo_id: "proc-1",
  todas_filiais_ativas: true,
} as const;

const revisaoMelhoria = {
  revisao_id: "rev-1",
  instancia_id: "inst-1",
  processo_id: "proc-1",
  versao_revisao: "1.1.0",
  cenario_tipo: "melhoria",
} as const;

const revisaoBaseline = {
  revisao_id: "rev-0",
  instancia_id: "inst-1",
  processo_id: "proc-1",
  versao_revisao: "1.0.0",
  cenario_tipo: "baseline",
} as const;

describe("revisao workspace sections", () => {
  it("expõe subpastas nas revisões da árvore", () => {
    const tree = buildProcessoWorkspaceTree({
      processo: processo as never,
      instancias: [instancia as never],
      revisoes: [revisaoMelhoria as never, revisaoBaseline as never],
    });

    const melhorias = tree.find((node) => node.id === "section:melhorias");
    const instanciaNode = melhorias?.children?.[0];
    const melhoriaNode = instanciaNode?.children?.find((node) => node.id === "revisao:rev-1");
    const baselineNode = instanciaNode?.children?.find((node) => node.id === "revisao:rev-0");

    expect(melhoriaNode?.children?.length).toBeGreaterThan(0);
    expect(melhoriaNode?.children?.some((node) => node.id === "revisao-section:rev-1:matriz")).toBe(true);
    expect(baselineNode?.children?.some((node) => node.id === "revisao-section:rev-0:matriz")).toBe(false);
    expect(baselineNode?.children?.some((node) => node.id === "revisao-section:rev-0:vigencia")).toBe(true);
  });

  it("resolve nó ativo da subpasta da revisão", () => {
    expect(
      resolveActiveWorkspaceNodeId({
        view: "revisao",
        revisaoId: "rev-1",
        revisaoSection: "medicao",
      })
    ).toBe("revisao-section:rev-1:medicao");
  });

  it("omite matriz no hash para baseline", () => {
    expect(parseRevisaoSectionFromHash("#matriz", "baseline")).toBe("vigencia");
    expect(defaultRevisaoSection("baseline")).toBe("vigencia");
    expect(defaultRevisaoSection("melhoria")).toBe("vigencia");
  });
});

describe("instancia workspace sections", () => {
  it("expõe subpastas dos cards da melhoria na árvore", () => {
    const tree = buildProcessoWorkspaceTree({
      processo: processo as never,
      instancias: [instancia as never],
      revisoes: [revisaoMelhoria as never],
    });

    const melhorias = tree.find((node) => node.id === "section:melhorias");
    const instanciaNode = melhorias?.children?.[0];
    const sectionIds = (instanciaNode?.children ?? [])
      .filter((node) => node.kind === "instancia-section")
      .map((node) => node.id);

    expect(sectionIds).toEqual([
      "instancia-section:inst-1:dados",
      "instancia-section:inst-1:mapeamento",
      "instancia-section:inst-1:contexto",
      "instancia-section:inst-1:diagrama",
      "instancia-section:inst-1:revisoes",
    ]);
    expect(instanciaNode?.children?.some((node) => node.id === "revisao:rev-1")).toBe(true);
  });

  it("resolve nó ativo da subpasta da melhoria", () => {
    expect(
      resolveActiveWorkspaceNodeId({
        view: "instancia",
        instanciaId: "inst-1",
        instanciaSection: "diagrama",
      })
    ).toBe("instancia-section:inst-1:diagrama");
    expect(
      resolveActiveWorkspaceNodeId({
        view: "instancia",
        instanciaId: "inst-1",
      })
    ).toBe(`instancia-section:inst-1:${defaultInstanciaSection()}`);
  });

  it("interpreta hash da melhoria e nova-revisao", () => {
    expect(parseInstanciaSectionFromHash("")).toBe("dados");
    expect(parseInstanciaSectionFromHash("#contexto")).toBe("contexto");
    expect(parseInstanciaSectionFromHash("#nova-revisao")).toBe("revisoes");
    expect(parseInstanciaSectionFromHash("#desconhecido")).toBe("dados");
  });
});
