import { describe, expect, it } from "vitest";

import { parseTransformometroPath } from "./routeParser";

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
