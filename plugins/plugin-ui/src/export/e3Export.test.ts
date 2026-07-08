import { describe, expect, it } from "vitest";

import { sanitizePdfText } from "./jspdf/exportDocument";
import {
  exportMatrixTableFormat,
  tableExportPayloadFromMatrix,
} from "./matrixAdapter";
import { prepareSvgCloneForRasterExport } from "./chartPngExport";

describe("sanitizePdfText", () => {
  it("normaliza unicode problemático para jsPDF", () => {
    expect(sanitizePdfText("valor\u2212teste")).toBe("valor-teste");
    expect(sanitizePdfText("a\u2192b")).toBe("a->b");
    expect(sanitizePdfText(null)).toBe("");
  });
});

describe("matrixAdapter helpers", () => {
  it("exportMatrixTableFormat monta payload a partir de headers/rows", () => {
    const table = {
      title: "OEE",
      headers: ["Recurso", "Valor"],
      rows: [["LN-01", 10]],
    };
    const payload = tableExportPayloadFromMatrix(table);
    expect(payload.title).toBe("OEE");
    expect(payload.columns).toHaveLength(2);
    expect(typeof exportMatrixTableFormat).toBe("function");
  });
});

describe("prepareSvgCloneForRasterExport", () => {
  it("clonagem define xmlns, tamanho e fundo", () => {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 100 50");
    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("cx", "10");
    circle.setAttribute("cy", "10");
    circle.setAttribute("r", "5");
    svg.appendChild(circle);
    document.body.appendChild(svg);

    const clone = prepareSvgCloneForRasterExport(svg, 200, 100, "#fafafa");
    expect(clone.getAttribute("xmlns")).toBe("http://www.w3.org/2000/svg");
    expect(clone.getAttribute("width")).toBe("200");
    expect(clone.getAttribute("height")).toBe("100");
    const rect = clone.querySelector("rect");
    expect(rect?.getAttribute("fill")).toBe("#fafafa");

    svg.remove();
  });
});
