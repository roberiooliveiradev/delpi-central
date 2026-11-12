import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { ApprovalRequestProducts } from "./ApprovalRequestProducts";

describe("ApprovalRequestProducts", () => {
  it("shows product code and description in one row for a multi-item SC", () => {
    const html = renderToStaticMarkup(
      <ApprovalRequestProducts products={[
        { product_code: "30194570", product_description: "TUBO PVC 75MM", line_count: 1 },
        { product_code: "30193744", product_description: "CAP ESGOTO 75MM", line_count: 1 },
      ]} />,
    );
    expect(html).toContain("30194570");
    expect(html).toContain("TUBO PVC 75MM");
    expect(html).toContain("30193744");
    expect(html).toContain("CAP ESGOTO 75MM");
    expect(html).toContain("Ver mais 1 produto");
  });

  it("indicates repeated SC lines without duplicating the product", () => {
    const html = renderToStaticMarkup(
      <ApprovalRequestProducts products={[
        { product_code: "41000018", product_description: "ALIMENTAÇÃO", line_count: 35 },
      ]} />,
    );
    expect(html).toContain("41000018");
    expect(html).toContain("ALIMENTAÇÃO");
    expect(html).toContain("35 itens da SC");
    expect(html).not.toContain("Ver mais");
  });

  it("handles missing product and description explicitly", () => {
    expect(renderToStaticMarkup(<ApprovalRequestProducts products={[]} />))
      .toContain("Produto não informado");
    expect(renderToStaticMarkup(<ApprovalRequestProducts products={[
      { product_code: "41000019", product_description: null, line_count: 1 },
    ]} />)).toContain("Descrição não informada");
  });
});
