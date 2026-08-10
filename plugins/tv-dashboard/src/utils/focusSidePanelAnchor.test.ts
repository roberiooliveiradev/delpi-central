import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import { focusSidePanelAnchor } from "./focusSidePanelAnchor";

describe("focusSidePanelAnchor", () => {
  beforeEach(() => {
    vi.stubGlobal("requestAnimationFrame", (cb: FrameRequestCallback) => {
      cb(0);
      return 0;
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    document.body.innerHTML = "";
  });

  it("abre details ancestral e rola até o âncora", () => {
    document.body.innerHTML = `
      <div class="td-deck-side-panel">
        <details id="sec">
          <summary>Conexão</summary>
          <div id="td-view-table-columns">colunas</div>
        </details>
      </div>
    `;
    const details = document.getElementById("sec") as HTMLDetailsElement;
    details.removeAttribute("open");
    const target = document.getElementById("td-view-table-columns")!;
    const scrollIntoView = vi.fn();
    target.scrollIntoView = scrollIntoView;

    focusSidePanelAnchor("td-view-table-columns");

    expect(details.getAttribute("open")).not.toBeNull();
    expect(scrollIntoView).toHaveBeenCalled();
  });
});
