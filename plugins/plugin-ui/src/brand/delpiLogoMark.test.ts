import { describe, expect, it } from "vitest";

import { DELPI_LOGO_MARK_SVG } from "./delpiLogoMark";
import {
  buildDelpiCableLabelDocumentHtml,
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
  it("inclui padding vertical e logo menor para o código do produto caber", () => {
    const css = buildDelpiCableLabelStyles();
    expect(css).toContain("padding: 2mm 7mm");
    expect(css).toContain(".tag__logo svg {\n      width: 13mm;");
    expect(css).toContain(".tag__name");
    expect(css).toContain(".tag__product");
    expect(css).toContain(".tag__meta");
  });
});

describe("buildDelpiQualitySealSvg", () => {
  it("usa anel amplo e ícone menor para o texto caber", () => {
    const svg = buildDelpiQualitySealSvg("APROVADO");
    expect(svg).toContain('font-weight="900"');
    expect(svg).toContain('font-size="17"');
    expect(svg).toContain('r="68"');
    expect(svg).toContain("scale(1.28)");
    expect(svg).toContain("QUALIDADE");
  });
});

describe("buildDelpiCableLabelDocumentHtml", () => {
  it("embute o CSS do kit e o wordmark sem slogan", () => {
    const html = buildDelpiCableLabelDocumentHtml({
      title: "Etiqueta teste",
      qrDataUrl: "data:image/png;base64,xx",
      qrAlt: "QR",
      qrFooterHtml: '<div class="tag__name">Fulano</div>',
      sealTopLabel: "APROVADO",
      hintHtml: "Dobre no centro.",
    });
    expect(html).toContain("<style>");
    expect(html).toContain("padding: 2mm 7mm");
    expect(html).toContain(".tag__name");
    expect(html).not.toContain("516.792");
    expect(html).toContain("Fulano");
    expect(html).toContain("APROVADO");
  });
});
