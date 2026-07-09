import { describe, expect, it } from "vitest";

import { resolveConnectionHandleIds } from "./diagramConnectionHandles";

describe("resolveConnectionHandleIds", () => {
  it("usa handles verticais quando o destino está abaixo na mesma coluna", () => {
    const handles = resolveConnectionHandleIds(
      { position: { x: 400, y: 48 } },
      { position: { x: 420, y: 240 } },
      "process",
      "process"
    );

    expect(handles).toEqual({
      sourceHandle: "bottom-source",
      targetHandle: "top-target",
    });
  });

  it("usa handles horizontais quando o fluxo é lateral", () => {
    const handles = resolveConnectionHandleIds(
      { position: { x: 180, y: 120 } },
      { position: { x: 420, y: 130 } },
      "process",
      "process"
    );

    expect(handles).toEqual({
      sourceHandle: "right-source",
      targetHandle: "left-target",
    });
  });

  it("usa handles verticais para conexão ascendente", () => {
    const handles = resolveConnectionHandleIds(
      { position: { x: 1280, y: 224 } },
      { position: { x: 1260, y: 48 } },
      "process",
      "process"
    );

    expect(handles).toEqual({
      sourceHandle: "top-source",
      targetHandle: "bottom-target",
    });
  });
});
