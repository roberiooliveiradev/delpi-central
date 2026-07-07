import { describe, expect, it } from "vitest";

import { buildTransformometroTransitionKey } from "./transitionKey";

describe("buildTransformometroTransitionKey", () => {
  it("normaliza barra final", () => {
    expect(buildTransformometroTransitionKey("/apps/transformometro/processos/")).toBe(
      "/apps/transformometro/processos"
    );
  });

  it("usa chave estável por processo no workspace (processo, instância, revisão)", () => {
    const processoBase = "/apps/transformometro/processos/p1";
    const instanciaPath = "/apps/transformometro/processos/p1/instancias/i1";
    const revisaoPath = "/apps/transformometro/processos/p1/instancias/i1/revisoes/r1";

    expect(buildTransformometroTransitionKey(processoBase)).toBe(processoBase);
    expect(buildTransformometroTransitionKey(instanciaPath)).toBe(processoBase);
    expect(buildTransformometroTransitionKey(revisaoPath)).toBe(processoBase);
  });
});
