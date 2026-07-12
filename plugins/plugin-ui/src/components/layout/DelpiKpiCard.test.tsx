import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";

import {
  DelpiKpiCard,
  parseKpiNumericValue,
  resolveDelpiKpiTone,
  type DelpiKpiColorRule,
} from "./DelpiKpiCard";

describe("resolveDelpiKpiTone", () => {
  const rules: DelpiKpiColorRule[] = [
    { op: "gte", value: 90, tone: "positive" },
    { op: "lt", value: 70, tone: "negative" },
    { op: "between", value: 70, valueTo: 89.99, tone: "warning" },
  ];

  it("aplica a primeira regra que casa", () => {
    expect(resolveDelpiKpiTone(95, rules).tone).toBe("positive");
    expect(resolveDelpiKpiTone(65, rules).tone).toBe("negative");
    expect(resolveDelpiKpiTone(80, rules).tone).toBe("warning");
  });

  it("usa fallback sem regras ou valor inválido", () => {
    expect(resolveDelpiKpiTone(null, rules).tone).toBe("default");
    expect(resolveDelpiKpiTone(50, undefined, "warning").tone).toBe("warning");
  });

  it("parseia valores percentuais e com milhar", () => {
    expect(parseKpiNumericValue("86,2%")).toBeCloseTo(86.2);
    expect(parseKpiNumericValue(42)).toBe(42);
  });
});

describe("DelpiKpiCard chrome", () => {
  it("aplica borda só via CSS vars no shell (sem border inline duplicado)", () => {
    const { container } = render(
      <DelpiKpiCard
        label="Taxa"
        value="10%"
        backgroundColor="#334155"
        kpiParts={{
          card: { style: { fill: "#334155", stroke: "#ef4444", strokeWidth: 6, borderRadius: 20 } },
        }}
        interaction={{}}
      />,
    );
    const shell = container.querySelector(".delpi-kpi-card-shell") as HTMLElement;
    const card = container.querySelector(".delpi-kpi-card") as HTMLElement;
    expect(shell.style.border).toBe("");
    expect(shell.style.getPropertyValue("--delpi-kpi-card-border-width")).toBe("6px");
    expect(shell.style.getPropertyValue("--delpi-kpi-card-border-color")).toBe("#ef4444");
    expect(card.getAttribute("style") ?? "").not.toMatch(/border:/);
  });

  it("não reexibe título oculto no modo sem interação (MetricKpiCard)", () => {
    const { container } = render(
      <DelpiKpiCard
        label="Indicador — Taxa de fechamento comercial"
        value="166,7%"
        kpiParts={{ title: { visible: false, content: "Indicador — Taxa de fechamento comercial" } }}
        kpiOptions={{ showTitle: false }}
      />,
    );
    expect(container.querySelector(".delpi-kpi-card__label")).toBeNull();
    expect(container.textContent).toContain("166,7%");
    expect(container.textContent).not.toContain("Taxa de fechamento");
    expect(container.querySelector(".delpi-kpi-card--value-dominant")).toBeTruthy();
  });
});
