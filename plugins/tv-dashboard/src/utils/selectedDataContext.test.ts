import { describe, expect, it } from "vitest";

import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import { resolveSelectedDataContext } from "./selectedDataContext";

describe("resolveSelectedDataContext", () => {
  const source: ComunicadoBlock = {
    id: "src-1",
    type: "data_source",
    frame: { x: 0, y: 0, w: 10, h: 10 },
    dataBinding: { operationId: "get_oee", displayMode: "auto", params: {} },
  };

  const textLinked: ComunicadoBlock = {
    id: "txt-1",
    type: "text",
    content: "—",
    frame: { x: 0, y: 0, w: 20, h: 10 },
    dataSourceId: "src-1",
    textProjection: { field: "oee", format: "number" },
  };

  it("inclui texto ligado como bloco de dados", () => {
    const ctx = resolveSelectedDataContext([source, textLinked], ["txt-1"]);
    expect(ctx.kind).toBe("single");
    expect(ctx.primary?.id).toBe("txt-1");
    expect(ctx.bindingTarget?.id).toBe("src-1");
  });

  it("agrupa seleção homogênea de textos na mesma fonte", () => {
    const text2: ComunicadoBlock = {
      ...textLinked,
      id: "txt-2",
      frame: { x: 10, y: 0, w: 20, h: 10 },
    };
    const ctx = resolveSelectedDataContext([source, textLinked, text2], ["txt-1", "txt-2"]);
    expect(ctx.kind).toBe("homogeneous");
    expect(ctx.bindingTarget?.id).toBe("src-1");
  });

  it("inclui texto sem vínculo como bloco de dados (mesmo fluxo do KPI)", () => {
    const textUnbound: ComunicadoBlock = {
      id: "txt-u",
      type: "text",
      content: "—",
      frame: { x: 0, y: 0, w: 20, h: 10 },
    };
    const ctx = resolveSelectedDataContext([source, textUnbound], ["txt-u"]);
    expect(ctx.kind).toBe("single");
    expect(ctx.primary?.id).toBe("txt-u");
    expect(ctx.bindingTarget).toBeNull();
  });
});
