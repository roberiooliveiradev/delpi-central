import { describe, expect, it } from "vitest";

import { buildTransformometroTransitionKey } from "./transitionKey";

describe("buildTransformometroTransitionKey", () => {
  it("normaliza barra final", () => {
    expect(buildTransformometroTransitionKey("/apps/transformometro/processes/")).toBe(
      "/apps/transformometro/processes"
    );
  });

  it("usa chave estável por processo no workspace (processo, instância, revisão)", () => {
    const processoBase = "/apps/transformometro/processes/p1";
    const instanciaPath = "/apps/transformometro/processes/p1/instances/i1";
    const revisaoPath = "/apps/transformometro/processes/p1/instances/i1/revisions/r1";

    expect(buildTransformometroTransitionKey(processoBase)).toBe(processoBase);
    expect(buildTransformometroTransitionKey(instanciaPath)).toBe(processoBase);
    expect(buildTransformometroTransitionKey(revisaoPath)).toBe(processoBase);
  });
});
