import { describe, expect, it } from "vitest";

import { buildTransformometroTransitionKey } from "./transitionKey";

describe("buildTransformometroTransitionKey", () => {
  it("normaliza barra final", () => {
    expect(buildTransformometroTransitionKey("/apps/transformometro/processos/")).toBe(
      "/apps/transformometro/processos"
    );
  });

  it("preserva rota aninhada de revisão", () => {
    const path =
      "/apps/transformometro/processos/p1/instancias/i1/revisoes/r1";
    expect(buildTransformometroTransitionKey(path)).toBe(path);
  });
});
