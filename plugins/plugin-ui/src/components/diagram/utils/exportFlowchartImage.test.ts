import { describe, expect, it } from "vitest";

import { shouldIncludeExportNode } from "./exportFlowchartImage";

describe("shouldIncludeExportNode", () => {
  it("exclui controles e fundo do React Flow", () => {
    const background = document.createElement("div");
    background.className = "react-flow__background";
    expect(shouldIncludeExportNode(background)).toBe(false);

    const controls = document.createElement("div");
    controls.className = "react-flow__controls";
    expect(shouldIncludeExportNode(controls)).toBe(false);

    const child = document.createElement("button");
    controls.appendChild(child);
    expect(shouldIncludeExportNode(child)).toBe(false);
  });

  it("inclui nós BPMN do diagrama", () => {
    const node = document.createElement("div");
    node.className = "tm-diagram-node tm-diagram-node--process";
    expect(shouldIncludeExportNode(node)).toBe(true);
  });
});
