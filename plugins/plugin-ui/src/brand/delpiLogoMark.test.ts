import { describe, expect, it } from "vitest";

import { DELPI_LOGO_MARK_SVG } from "./delpiLogoMark";
import {
  buildDelpiCableLabelDocumentHtml,
  buildDelpiCableLabelLabeledCodeHtml,
  buildDelpiCableLabelStyles,
  buildDelpiQualitySealSvg,
  formatDelpiCableLabelCustomerItem,
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
    expect(css).toContain(".tag__customer");
    expect(css).toContain(".tag__code-label");
    expect(css).toContain(".tag__meta");
  });
});

describe("formatDelpiCableLabelCustomerItem", () => {
  it("devolve o item do cliente sem revisão", () => {
    expect(formatDelpiCableLabelCustomerItem("2229-07/1")).toBe("2229-07/1");
  });

  it("anexa a revisão quando o item existe", () => {
    expect(formatDelpiCableLabelCustomerItem("2229-07/1", "00")).toBe(
      "2229-07/1 Rev.00",
    );
  });

  it("não imprime revisão se o item do cliente estiver vazio", () => {
    expect(formatDelpiCableLabelCustomerItem("  ", "00")).toBe("");
    expect(formatDelpiCableLabelCustomerItem(null, "00")).toBe("");
  });
});

describe("buildDelpiCableLabelLabeledCodeHtml", () => {
  it("monta a linha CLIENTE na frente da etiqueta", () => {
    const html = buildDelpiCableLabelLabeledCodeHtml(
      "customer",
      "CLIENTE",
      "2229-07/1 Rev.00",
    );
    expect(html).toContain('class="tag__customer"');
    expect(html).toContain('class="tag__code-label"');
    expect(html).toContain("CLIENTE");
    expect(html).toContain("2229-07/1 Rev.00");
  });

  it("monta a linha DELPI no verso da etiqueta", () => {
    const html = buildDelpiCableLabelLabeledCodeHtml("product", "DELPI", "90300005");
    expect(html).toContain('class="tag__product"');
    expect(html).toContain("DELPI");
    expect(html).toContain("90300005");
  });

  it("omite o bloco quando o valor está vazio", () => {
    expect(buildDelpiCableLabelLabeledCodeHtml("customer", "CLIENTE", "  ")).toBe(
      "",
    );
  });

  it("escapa HTML no valor", () => {
    const html = buildDelpiCableLabelLabeledCodeHtml(
      "customer",
      "CLIENTE",
      '<b>x</b>',
    );
    expect(html).toContain("&lt;b&gt;x&lt;/b&gt;");
    expect(html).not.toContain("<b>x</b>");
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

  it("repassa item do cliente na frente e código Delpi no verso", () => {
    const html = buildDelpiCableLabelDocumentHtml({
      title: "Etiqueta da Qualidade",
      qrDataUrl: "data:image/png;base64,xx",
      qrAlt: "QR",
      qrFooterHtml: `${buildDelpiCableLabelLabeledCodeHtml("customer", "CLIENTE", "2229-07/1")}<div class="tag__meta">OP 1 · 11/09/2026</div>`,
      brandFooterHtml: buildDelpiCableLabelLabeledCodeHtml("product", "DELPI", "90300005"),
      sealTopLabel: "APROVADO",
      hintHtml: "Dobre no centro.",
    });
    expect(html).toContain("tag__customer");
    expect(html).toContain("CLIENTE");
    expect(html).toContain("2229-07/1");
    expect(html).toContain("tag__product");
    expect(html).toContain("DELPI");
    expect(html).toContain("90300005");
    expect(html).toContain("OP 1 · 11/09/2026");
  });
});
