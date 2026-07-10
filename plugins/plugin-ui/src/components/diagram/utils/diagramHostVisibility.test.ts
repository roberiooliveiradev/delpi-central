import { describe, expect, it } from "vitest";

import {
  findDiagramWorkspaceHost,
  isDiagramWorkspaceHostVisible,
} from "./diagramHostVisibility";

describe("diagramHostVisibility", () => {
  it("considera host ativo quando tem classe --active", () => {
    document.body.innerHTML = `
      <div class="tm-processo-workspace-section tm-processo-workspace-section--active" data-section="diagrama">
        <div class="tm-diagram-editor__canvas"></div>
      </div>
    `;
    const canvas = document.querySelector(".tm-diagram-editor__canvas")!;
    expect(findDiagramWorkspaceHost(canvas)?.getAttribute("data-section")).toBe("diagrama");
    expect(isDiagramWorkspaceHostVisible(canvas)).toBe(true);
  });

  it("considera host oculto quando aria-hidden=true sem classe active", () => {
    document.body.innerHTML = `
      <div class="tm-processo-workspace-section" data-section="diagrama" aria-hidden="true">
        <div class="tm-diagram-editor__canvas"></div>
      </div>
    `;
    const canvas = document.querySelector(".tm-diagram-editor__canvas")!;
    expect(isDiagramWorkspaceHostVisible(canvas)).toBe(false);
  });

  it("retorna true fora de workspace host", () => {
    document.body.innerHTML = `<div class="tm-diagram-editor__canvas"></div>`;
    const canvas = document.querySelector(".tm-diagram-editor__canvas")!;
    expect(findDiagramWorkspaceHost(canvas)).toBeNull();
    expect(isDiagramWorkspaceHostVisible(canvas)).toBe(true);
  });
});
