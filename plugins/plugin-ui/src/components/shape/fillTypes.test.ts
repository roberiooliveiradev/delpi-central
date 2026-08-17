import { describe, expect, it } from "vitest";

import {
  fillToCssBackground,
  normalizeFillAngle,
  normalizeGradientStops,
  resolveFillKindTabChange,
  resolveFillTriggerPreview,
  solidFromFill,
  stopsFromLegacyFromTo,
} from "./fillTypes";

describe("fillTypes", () => {
  it("completa um stop para o mínimo de dois", () => {
    const stops = normalizeGradientStops([{ color: "#112233", position: 40 }]);
    expect(stops).toHaveLength(2);
    expect(stops[0]?.position).toBe(0);
    expect(stops[1]?.position).toBe(100);
  });

  it("normaliza ângulo para 0–359", () => {
    expect(normalizeFillAngle(360)).toBe(0);
    expect(normalizeFillAngle(-90)).toBe(270);
    expect(normalizeFillAngle(450)).toBe(90);
  });

  it("emite CSS linear com stops ordenados", () => {
    expect(
      fillToCssBackground({
        kind: "gradient",
        angle: 90,
        stops: [
          { color: "#fff", position: 100 },
          { color: "#000", position: 0 },
        ],
      }),
    ).toBe("linear-gradient(90deg, #000 0%, #fff 100%)");
  });

  it("solidFromFill cobre none, sólido e primeiro stop", () => {
    expect(solidFromFill({ kind: "none" })).toBe("transparent");
    expect(solidFromFill({ kind: "solid", color: "#abc" })).toBe("#abc");
    expect(
      solidFromFill({
        kind: "gradient",
        angle: 180,
        stops: stopsFromLegacyFromTo("#111", "#eee"),
      }),
    ).toBe("#111");
  });

  it("resolveFillTriggerPreview: fill sólido manda mesmo sem value", () => {
    const preview = resolveFillTriggerPreview({ kind: "solid", color: "#089bdb" }, undefined, "fill");
    expect(preview.mode).toBe("color");
    expect(preview.background).toBe("#089bdb");
  });

  it("resolveFillTriggerPreview: gradiente usa background CSS, não borderColor", () => {
    const preview = resolveFillTriggerPreview(
      {
        kind: "gradient",
        angle: 135,
        stops: [
          { color: "#089bdb", position: 0 },
          { color: "#be123c", position: 100 },
        ],
      },
      undefined,
      "outline",
    );
    expect(preview.mode).toBe("color");
    expect(preview.background).toContain("linear-gradient(135deg");
    expect(preview.background).toContain("#089bdb");
  });

  it("resolveFillTriggerPreview: none e value transparent → sem prévia", () => {
    expect(resolveFillTriggerPreview({ kind: "none" }, "#fff", "fill")).toEqual({ mode: "none" });
    expect(resolveFillTriggerPreview(undefined, "transparent", "outline").mode).toBe("none");
  });

  it("aba Cor sobre gradiente não emite sólido", () => {
    const current = {
      kind: "gradient" as const,
      angle: 135,
      stops: [
        { color: "#089bdb", position: 0 },
        { color: "#be123c", position: 100 },
      ],
    };
    expect(resolveFillKindTabChange("solid", current, "#089bdb")).toBeNull();
  });

  it("aba Gradiente sobre sólido emite gradiente a partir do hex", () => {
    const next = resolveFillKindTabChange("gradient", { kind: "solid", color: "#ef4444" }, "#ef4444");
    expect(next).toEqual(
      expect.objectContaining({
        kind: "gradient",
        angle: 180,
        stops: expect.arrayContaining([expect.objectContaining({ color: "#ef4444", position: 0 })]),
      }),
    );
  });

  it("re-clicar Gradiente devolve o fill atual", () => {
    const current = {
      kind: "gradient" as const,
      angle: 45,
      stops: [
        { color: "#111111", position: 0 },
        { color: "#eeeeee", position: 100 },
      ],
    };
    expect(resolveFillKindTabChange("gradient", current)).toBe(current);
  });

  it("aplica opacidade do stop no CSS", () => {
    expect(
      fillToCssBackground({
        kind: "gradient",
        angle: 0,
        stops: [
          { color: "#000000", position: 0, opacity: 0.5 },
          { color: "#ffffff", position: 100 },
        ],
      }),
    ).toContain("rgba(0, 0, 0, 0.5)");
  });
});
