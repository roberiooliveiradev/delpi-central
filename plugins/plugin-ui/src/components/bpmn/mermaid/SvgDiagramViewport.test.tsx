import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SvgDiagramViewport } from "./SvgDiagramViewport";

const labels = {
  zoomLabel: "Zoom do diagrama",
  zoomIn: "Aumentar zoom",
  zoomOut: "Diminuir zoom",
  zoomInHint: "Aproxima",
  zoomOutHint: "Afasta",
  zoomFit: "Ajustar",
  zoomFitHint: "Enquadra",
  zoomReset: "100%",
  zoomResetHint: "Restaura 100%",
};

describe("SvgDiagramViewport", () => {
  it("expõe controles de zoom/fit/100% sem expandir o world no HTML", () => {
    const { container } = render(
      <div style={{ width: 320, height: 240 }}>
        <SvgDiagramViewport labels={labels} worldWidth={6400} worldHeight={2200}>
          <svg width="6400" height="2200" viewBox="0 0 6400 2200" data-testid="world-svg" />
        </SvgDiagramViewport>
      </div>
    );

    const viewport = container.querySelector(".delpi-ui-bpmn-svg-viewport");
    expect(viewport).toBeTruthy();
    expect(screen.getByRole("button", { name: "Aumentar zoom" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Diminuir zoom" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Ajustar" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "100%" })).toBeTruthy();
    expect(container.querySelector('[data-testid="world-svg"]')).toBeTruthy();
  });

  it("não usa SVG Lucide do chrome como world do diagrama", () => {
    const { container } = render(
      <div style={{ width: 320, height: 240 }}>
        <SvgDiagramViewport labels={labels} worldWidth={1} worldHeight={1}>
          <div className="delpi-ui-bpmn-mermaid">
            <iframe title="sandbox mermaid" />
          </div>
        </SvgDiagramViewport>
      </div>
    );

    const firstSvg = container.querySelector(".delpi-ui-bpmn-svg-viewport")?.querySelector("svg");
    const worldSvg = container.querySelector(".delpi-ui-bpmn-svg-viewport__world svg");
    expect(firstSvg?.getAttribute("viewBox")).toBe("0 0 24 24");
    expect(worldSvg).toBeNull();
  });
});
