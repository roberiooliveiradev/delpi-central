import { describe, expect, it } from "vitest";

import {
  buildProcessoWorkspaceTree,
  defaultRevisaoSection,
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
