import { describe, expect, it } from "vitest";

import { statusPresentation } from "./tablePresentation";

describe("statusPresentation — STATUS_PROCESSO canônico", () => {
  it("ativo → success + label Ativo", () => {
    expect(statusPresentation("ativo")).toEqual({
      label: "Ativo",
      className: "ds-badge ds-badge--success",
    });
  });

  it("em_implantacao → badge explícito + label Em implantação (nunca raw)", () => {
    const out = statusPresentation("em_implantacao");
    expect(out.className).toContain("ds-badge--warning");
    expect(out.label).toBe("Em implantação");
  });

  it("descontinuado → badge explícito + label Descontinuado", () => {
    const out = statusPresentation("descontinuado");
    expect(out.className).toContain("ds-badge--info");
    expect(out.label).toBe("Descontinuado");
  });

  it("valor desconhecido → badge neutro + label humanizado", () => {
    const out = statusPresentation("congelado_total");
    expect(out.className).toBe("ds-badge");
    expect(out.label).toBe("Congelado total");
  });
});
