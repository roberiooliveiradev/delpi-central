import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ComunicadoTextSurface, resolveTextSurfaceDisplay } from "./ComunicadoTextSurface";
import { ComunicadoVisualBoxView } from "./ComunicadoVisualBoxView";
import type { ComunicadoShapeBlock } from "./comunicadoTypes";

/** Fixture do bug «Meta 1.400 PPM» — negrito só em «Meta», sem data binding. */
function metaPpmShape(): ComunicadoShapeBlock {
  return {
    id: "shape-meta-ppm",
    type: "shape",
    shape: "rounded-rect",
    frame: { x: 10, y: 10, w: 40, h: 12 },
    content: "Meta 1.400 PPM",
    contentRuns: [
      { text: "Meta", style: { fontWeight: "bold", color: "#b91c1c" } },
      { text: " 1.400 PPM" },
    ],
    style: {
      fontSize: 28,
      color: "#0f172a",
      fill: "#ffffff",
      stroke: "#cbd5e1",
    },
  };
}

describe("ComunicadoTextSurface — formatação parcial em forma", () => {
  it("resolve display com contentRuns sem data binding", () => {
    const display = resolveTextSurfaceDisplay(metaPpmShape());
    expect(display.content).toBe("Meta 1.400 PPM");
    expect(display.contentRuns).toHaveLength(2);
    expect(display.contentRuns?.[0]?.style?.fontWeight).toBe("bold");
  });

  it("pinta trechos com estilo no readonly/TV (sem binding)", () => {
    const { container } = render(<ComunicadoTextSurface block={metaPpmShape()} />);
    expect(screen.getByText("Meta")).toBeTruthy();
    expect(screen.getByText((text) => text.includes("1.400 PPM"))).toBeTruthy();
    const boldSpan = Array.from(container.querySelectorAll("span")).find(
      (el) => el.textContent === "Meta" && (el as HTMLElement).style.fontWeight === "bold",
    );
    expect(boldSpan).toBeTruthy();
  });

  it("ComunicadoVisualBoxView usa TextSurface para shape sem binding", () => {
    const { container } = render(<ComunicadoVisualBoxView block={metaPpmShape()} />);
    expect(container.textContent).toContain("Meta");
    expect(container.textContent).toContain("1.400 PPM");
    const boldSpan = Array.from(container.querySelectorAll("span")).find(
      (el) => el.textContent === "Meta" && (el as HTMLElement).style.fontWeight === "bold",
    );
    expect(boldSpan).toBeTruthy();
  });
});
