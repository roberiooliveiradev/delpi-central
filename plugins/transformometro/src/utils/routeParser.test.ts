import { describe, expect, it } from "vitest";

import {
  buildInstanciaDiagramaEditPath,
  buildProcessoDiagramaEditPath,
  buildRevisaoDiagramaEditPath,
  canonicalizeTransformometroPath,
  parseTransformometroPath,
} from "./routeParser";

describe("canonicalizeTransformometroPath", () => {
  it("reescreve bookmarks PT para EN", () => {
    expect(canonicalizeTransformometroPath("/apps/transformometro/atas")).toBe(
      "/apps/transformometro/meeting-minutes",
    );
    expect(canonicalizeTransformometroPath("/apps/transformometro/minha-assinatura")).toBe(
      "/apps/transformometro/my-signature",
    );
    expect(
      canonicalizeTransformometroPath(
        "/apps/transformometro/processos/p-1/instancias/i-1/revisoes/r-1/diagrama/edit",
      ),
    ).toBe("/apps/transformometro/processes/p-1/instances/i-1/revisions/r-1/diagram/edit");
  });
});

describe("parseTransformometroPath - meeting minutes", () => {
  it.each([
    ["/apps/transformometro/meeting-minutes", "atas"],
    ["/apps/transformometro/atas", "atas"],
    ["/apps/transformometro/meeting-minutes/new", "ataNew"],
    ["/apps/transformometro/atas/pending", "atasPending"],
    ["/apps/transformometro/my-signature", "minhaAssinatura"],
    ["/apps/transformometro/minha-assinatura", "minhaAssinatura"],
  ] as const)("resolve %s", (path, view) => {
    expect(parseTransformometroPath(path).view).toBe(view);
  });

  it("resolve a ata e suas ações (EN e legado)", () => {
    expect(parseTransformometroPath("/apps/transformometro/meeting-minutes/a-1")).toMatchObject({
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

describe("parseTransformometroPath - diagram edit", () => {
  it("resolve edição do diagrama macro do processo", () => {
    expect(
      parseTransformometroPath("/apps/transformometro/processes/p-1/diagram/edit"),
    ).toMatchObject({
      view: "processoDiagramaEdit",
      processoId: "p-1",
    });
    expect(buildProcessoDiagramaEditPath("p-1")).toBe(
      "/apps/transformometro/processes/p-1/diagram/edit",
    );
  });

  it("resolve edição do escopo no diagrama da instância", () => {
    expect(
      parseTransformometroPath("/apps/transformometro/processes/p-1/instances/i-1/diagram/edit"),
    ).toMatchObject({
      view: "instanciaDiagramaEdit",
      processoId: "p-1",
      instanciaId: "i-1",
    });
    expect(buildInstanciaDiagramaEditPath("p-1", "i-1")).toBe(
      "/apps/transformometro/processes/p-1/instances/i-1/diagram/edit",
    );
  });

  it("resolve edição do diagrama da revisão", () => {
    expect(
      parseTransformometroPath(
        "/apps/transformometro/processes/p-1/instances/i-1/revisions/r-1/diagram/edit",
      ),
    ).toMatchObject({
      view: "revisaoDiagramaEdit",
      processoId: "p-1",
      instanciaId: "i-1",
      revisaoId: "r-1",
    });
    expect(buildRevisaoDiagramaEditPath("p-1", "i-1", "r-1")).toBe(
      "/apps/transformometro/processes/p-1/instances/i-1/revisions/r-1/diagram/edit",
    );
  });

  it("aceita legado PT e canônico EN", () => {
    expect(
      parseTransformometroPath("/apps/transformometro/processos/p-1/diagrama/edit"),
    ).toMatchObject({ view: "processoDiagramaEdit", processoId: "p-1" });
    expect(parseTransformometroPath("/apps/transformometro/processes/p-1")).toMatchObject({
      view: "processo",
      processoId: "p-1",
    });
    expect(
      parseTransformometroPath("/apps/transformometro/processes/p-1/instances/i-1"),
    ).toMatchObject({ view: "instancia" });
  });
});
