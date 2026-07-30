import { describe, expect, it } from "vitest";

import {
  buildInstanciaDiagramaEditPath,
  buildProcessoDiagramaEditPath,
  buildRevisaoDiagramaEditPath,
  parseTransformometroPath,
} from "./routeParser";

describe("parseTransformometroPath - atas Transforma+", () => {
  it.each([
    ["/apps/transformometro/atas", "atas"],
    ["/apps/transformometro/atas/new", "ataNew"],
    ["/apps/transformometro/atas/pending", "atasPending"],
    ["/apps/transformometro/minha-assinatura", "minhaAssinatura"],
  ] as const)("resolve %s", (path, view) => {
    expect(parseTransformometroPath(path).view).toBe(view);
  });

  it("resolve a ata e suas ações", () => {
    expect(parseTransformometroPath("/apps/transformometro/atas/a-1")).toMatchObject({
      view: "ata",
      ataId: "a-1",
    });
    expect(parseTransformometroPath("/apps/transformometro/atas/a-1/edit")).toMatchObject({
      view: "ataEdit",
      ataId: "a-1",
    });
    expect(parseTransformometroPath("/apps/transformometro/atas/a-1/sign")).toMatchObject({
      view: "ataSign",
      ataId: "a-1",
    });
  });
});

describe("parseTransformometroPath - diagrama edit", () => {
  it("resolve edição do diagrama macro do processo", () => {
    expect(
      parseTransformometroPath("/apps/transformometro/processos/p-1/diagrama/edit")
    ).toMatchObject({
      view: "processoDiagramaEdit",
      processoId: "p-1",
    });
    expect(buildProcessoDiagramaEditPath("p-1")).toBe(
      "/apps/transformometro/processos/p-1/diagrama/edit"
    );
  });

  it("resolve edição do escopo no diagrama da instância", () => {
    expect(
      parseTransformometroPath(
        "/apps/transformometro/processos/p-1/instancias/i-1/diagrama/edit"
      )
    ).toMatchObject({
      view: "instanciaDiagramaEdit",
      processoId: "p-1",
      instanciaId: "i-1",
    });
    expect(buildInstanciaDiagramaEditPath("p-1", "i-1")).toBe(
      "/apps/transformometro/processos/p-1/instancias/i-1/diagrama/edit"
    );
  });

  it("resolve edição do diagrama da revisão", () => {
    expect(
      parseTransformometroPath(
        "/apps/transformometro/processos/p-1/instancias/i-1/revisoes/r-1/diagrama/edit"
      )
    ).toMatchObject({
      view: "revisaoDiagramaEdit",
      processoId: "p-1",
      instanciaId: "i-1",
      revisaoId: "r-1",
    });
    expect(buildRevisaoDiagramaEditPath("p-1", "i-1", "r-1")).toBe(
      "/apps/transformometro/processos/p-1/instancias/i-1/revisoes/r-1/diagrama/edit"
    );
  });

  it("não confunde detalhe com rota de edição de diagrama", () => {
    expect(parseTransformometroPath("/apps/transformometro/processos/p-1")).toMatchObject({
      view: "processo",
      processoId: "p-1",
    });
    expect(
      parseTransformometroPath("/apps/transformometro/processos/p-1/instancias/i-1")
    ).toMatchObject({ view: "instancia" });
  });
});
