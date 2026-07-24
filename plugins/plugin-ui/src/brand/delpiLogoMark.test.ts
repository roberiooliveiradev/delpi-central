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
  it("inclui regras canônicas (padding, name, product, meta)", () => {
    const css = buildDelpiCableLabelStyles();
    expect(css).toContain("padding: 1.2mm 7mm");
    expect(css).toContain(".tag__name");
    expect(css).toContain(".tag__product");
    expect(css).toContain(".tag__meta");
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
    expect(html).toContain("padding: 1.2mm 7mm");
    expect(html).toContain(".tag__name");
    expect(html).not.toContain("516.792");
    expect(html).toContain("Fulano");
    expect(html).toContain("APROVADO");
  });
});
