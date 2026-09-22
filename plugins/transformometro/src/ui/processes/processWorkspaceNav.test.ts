import { describe, expect, it } from "vitest";

import {
  buildProcessoWorkspaceTree,
  defaultInstanciaSection,
  defaultRevisaoSection,
  parseInstanciaSectionFromHash,
  parseProcessDocumentIdFromHash,
  parseProcessoSecondaryFocusFromHash,
  parseProcessoSectionFromHash,
  parseRevisaoSectionFromHash,
  resolveActiveWorkspaceNodeId,
  PROCESSO_WORKSPACE_SECTIONS,
} from "./processWorkspaceNav";

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

describe("processo workspace sections", () => {
  it("expõe exatamente 8 seções primárias sem Atas/Evidências", () => {
    const ids = PROCESSO_WORKSPACE_SECTIONS.map((section) => section.id);
    expect(ids).toEqual([
      "visao-geral",
      "mapeamento",
      "documentacao",
      "melhorias",
      "resultados",
      "tarefas",
      "sala",
      "historico",
    ]);
    expect(ids).not.toContain("atas");
    expect(ids).not.toContain("evidencias");
    expect(ids).not.toContain("dados");
    expect(ids).not.toContain("diagrama");
    expect(ids).not.toContain("arquivos");
    expect(ids).not.toContain("priorizacao");
    expect(ids).not.toContain("timeline");
  });

  it("mapeia hashes legados para primary + secondary", () => {
    expect(parseProcessoSectionFromHash("#dados")).toBe("visao-geral");
    expect(parseProcessoSectionFromHash("#diagrama")).toBe("mapeamento");
    expect(parseProcessoSectionFromHash("#arquivos")).toBe("documentacao");
    expect(parseProcessoSectionFromHash("#priorizacao")).toBe("melhorias");
    expect(parseProcessoSectionFromHash("#timeline")).toBe("historico");
    expect(parseProcessoSectionFromHash("#tarefas")).toBe("tarefas");
    expect(parseProcessoSectionFromHash("#sala")).toBe("sala");
    expect(parseProcessoSectionFromHash("#resultados")).toBe("resultados");

    expect(parseProcessoSecondaryFocusFromHash("#diagrama")).toBe("fluxo");
    expect(parseProcessoSecondaryFocusFromHash("#mapeamento")).toBe("estrutura");
    expect(parseProcessoSecondaryFocusFromHash("#arquivos")).toBe("arquivos");
    expect(parseProcessoSecondaryFocusFromHash("#documentacao")).toBe("documentos");
    expect(parseProcessoSecondaryFocusFromHash("#priorizacao")).toBe("priorizacao");
    expect(parseProcessoSecondaryFocusFromHash("#dados")).toBeNull();
  });

  it("interpreta hash de documentação com documento selecionado", () => {
    expect(parseProcessoSectionFromHash("#documentacao")).toBe("documentacao");
    expect(
      parseProcessDocumentIdFromHash(
        "#documentacao/33333333-3333-3333-3333-333333333333",
      ),
    ).toBe("33333333-3333-3333-3333-333333333333");
    expect(parseProcessDocumentIdFromHash("#documentacao")).toBeNull();
  });
});

describe("revisao workspace sections", () => {
  it("expõe subpastas nas revisões da árvore", () => {
    const tree = buildProcessoWorkspaceTree({
      processo: processo as never,
      instancias: [instancia as never],
      revisoes: [revisaoMelhoria as never, revisaoBaseline as never],
    });

    const melhorias = tree.find((node) => node.id === "section:melhorias");
    const instanciaNode = melhorias?.children?.[0];
    const revisoesFolder = instanciaNode?.children?.find(
      (node) => node.id === "instancia-section:inst-1:revisoes"
    );
    const melhoriaNode = revisoesFolder?.children?.find((node) => node.id === "revisao:rev-1");
    const baselineNode = revisoesFolder?.children?.find((node) => node.id === "revisao:rev-0");

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
      "instancia-section:inst-1:diagrama",
      "instancia-section:inst-1:contexto",
      "instancia-section:inst-1:revisoes",
    ]);
    const revisoesFolder = instanciaNode?.children?.find(
      (node) => node.id === "instancia-section:inst-1:revisoes"
    );
    expect(revisoesFolder?.children?.some((node) => node.id === "revisao:rev-1")).toBe(true);
    expect(revisoesFolder?.badge).toBe("1");
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
