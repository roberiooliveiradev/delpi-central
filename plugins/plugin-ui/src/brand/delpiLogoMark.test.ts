import { describe, expect, it } from "vitest";

import { DELPI_LOGO_MARK_SVG } from "./delpiLogoMark";
import {
  buildDelpiCableLabelStyles,
  buildDelpiQualitySealSvg,
} from "./delpiCableLabel";

describe("DELPI_LOGO_MARK_SVG", () => {
  it("não inclui o slogan Conexões Elétricas", () => {
    expect(DELPI_LOGO_MARK_SVG).not.toContain("516.792");
    expect(DELPI_LOGO_MARK_SVG.toLowerCase()).not.toContain("conex");
    expect(DELPI_LOGO_MARK_SVG).toContain('viewBox="0 0 832 440"');
  });
});

describe("buildDelpiCableLabelStyles", () => {
  it("aplica padding lateral canônico na etiqueta", () => {
    const css = buildDelpiCableLabelStyles();
    expect(css).toContain("padding: 1.2mm 7mm");
  });
});

describe("buildDelpiQualitySealSvg", () => {
  it("renderiza textos em negrito e tamanho maior", () => {
    const svg = buildDelpiQualitySealSvg("APROVADO");
    expect(svg).toContain('font-weight="900"');
    expect(svg).toContain('font-size="20"');
    expect(svg).toContain("QUALIDADE");
  });
});
