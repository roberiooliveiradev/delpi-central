import { describe, expect, it } from "vitest";

import {
  isFullContentTextSelection,
  stripContentRunStylesOverriddenByContainer,
  typographyKeysFromContainerPatch,
} from "./containerTypographyOverride";
import type { ComunicadoContentRun } from "./comunicadoTypes";

describe("containerTypographyOverride", () => {
  const runs: ComunicadoContentRun[] = [
    { text: "Meta ", style: { fontWeight: "bold", color: "#111" } },
    {
      text: "1.400",
      dataRef: { field: "ppm" },
      style: { fontWeight: "normal", fontStyle: "italic" },
    },
    { text: " PPM", style: { fontSize: 20 } },
  ];

  it("extrai só chaves tipográficas presentes no patch", () => {
    expect(
      typographyKeysFromContainerPatch({
        fontWeight: "bold",
        fill: "#fff",
        color: "#000",
      }),
    ).toEqual(["fontWeight", "color"]);
  });

  it("strip remove tipografia do container e preserva dataRef / outras chaves", () => {
    const next = stripContentRunStylesOverriddenByContainer(runs, ["fontWeight", "fontStyle"]);
    expect(next).toEqual([
      { text: "Meta ", style: { color: "#111" } },
      { text: "1.400", dataRef: { field: "ppm" } },
      { text: " PPM", style: { fontSize: 20 } },
    ]);
  });

  it("detecta seleção de texto inteiro", () => {
    expect(isFullContentTextSelection(runs, undefined, 0, "Meta 1.400 PPM".length)).toBe(true);
    expect(isFullContentTextSelection(runs, undefined, 0, 4)).toBe(false);
  });
});
