import { describe, expect, it } from "vitest";

import { measureVisualBoxContentSizePx, visualBoxBlockHasHugableText } from "./measureVisualBoxContentSize";

describe("measureVisualBoxContentSize", () => {
  it("visualBoxBlockHasHugableText exige conteúdo", () => {
    expect(visualBoxBlockHasHugableText({ content: "" })).toBe(false);
    expect(visualBoxBlockHasHugableText({ content: "  " })).toBe(false);
    expect(visualBoxBlockHasHugableText({ content: "Oi" })).toBe(true);
    expect(visualBoxBlockHasHugableText({ contentRuns: [{ text: "A" }] })).toBe(true);
  });

  it("mede scrollWidth/Height do texto interno", () => {
    const root = document.createElement("div");
    root.innerHTML = `
      <div class="tdp-comunicado__visual-box-content">
        <p class="td-composer__inline-text">Olá</p>
      </div>
    `;
    const text = root.querySelector<HTMLElement>(".td-composer__inline-text")!;
    Object.defineProperty(text, "scrollWidth", { configurable: true, get: () => 120 });
    Object.defineProperty(text, "scrollHeight", { configurable: true, get: () => 40 });
    const size = measureVisualBoxContentSizePx(root, { axes: { width: true, height: true } });
    expect(size).not.toBeNull();
    expect(size!.w).toBeGreaterThanOrEqual(120);
    expect(size!.h).toBeGreaterThanOrEqual(40);
  });
});
