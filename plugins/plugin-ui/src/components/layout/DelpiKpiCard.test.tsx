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
    expect(parseKpiNumericValue("78.91")).toBeCloseTo(78.91);
    expect(parseKpiNumericValue("1.234,56")).toBeCloseTo(1234.56);
    expect(parseKpiNumericValue("1.234")).toBe(1234);
  });

  it("aplica tom da regra a valores decimais com ponto (API)", () => {
    const rules: DelpiKpiColorRule[] = [{ op: "lte", value: 80, tone: "negative" }];
    const numeric = parseKpiNumericValue("78.91");
    expect(resolveDelpiKpiTone(numeric, rules).tone).toBe("negative");
  });
});

describe("DelpiKpiCard tone vs cor explícita", () => {
  it("não força cor inline quando o tom vem da regra", () => {
    const { container } = render(
      <DelpiKpiCard label="OEE" value="78.91" tone="negative" />,
    );
    const shell = container.querySelector(".delpi-kpi-card-shell") as HTMLElement;
    const value = container.querySelector(".delpi-kpi-card__value") as HTMLElement;
    expect(shell.getAttribute("data-custom-value")).toBeNull();
    expect(container.querySelector(".delpi-kpi-card--negative")).toBeTruthy();
    expect(value.style.color).toBe("");
  });
});

describe("DelpiKpiCard chrome", () => {
  it("aplica raio e sombra padrão via CSS vars no shell", () => {
    const { container } = render(<DelpiKpiCard label="% no prazo" value="100" />);
    const shell = container.querySelector(".delpi-kpi-card-shell") as HTMLElement;
    expect(shell.style.getPropertyValue("--delpi-kpi-card-radius")).toBe("16px");
    expect(shell.style.getPropertyValue("--delpi-kpi-card-shadow")).toContain("rgba(15, 23, 42");
    expect(shell.style.getPropertyValue("--delpi-kpi-card-border-color")).toBe("#b4b4b4");
  });

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

  it("não reexibe título oculto sem interação", () => {
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

  it("mantém tipografia de parts com e sem interaction (deselect)", () => {
    const kpiParts = {
      title: { style: { fontSize: 18, color: "#94a3b8" } },
      value: { style: { fontSize: 64, color: "#ffffff" } },
    };

    const selected = render(
      <DelpiKpiCard label="Consumo" value="10" kpiParts={kpiParts} interaction={{}} />,
    );
    const deselected = render(
      <DelpiKpiCard label="Consumo" value="10" kpiParts={kpiParts} interaction={null} />,
    );

    const selectedTitle = selected.container.querySelector(".delpi-kpi-card__label") as HTMLElement;
    const deselectedTitle = deselected.container.querySelector(
      ".delpi-kpi-card__label",
    ) as HTMLElement;
    expect(selectedTitle.style.fontSize).toBe("18px");
    expect(deselectedTitle.style.fontSize).toBe("18px");

    const selectedValue = selected.container.querySelector(".delpi-ui-fit-text") as HTMLElement;
    const deselectedValue = deselected.container.querySelector(".delpi-ui-fit-text") as HTMLElement;
    expect(selectedValue.style.fontSize).toBe("64px");
    expect(deselectedValue.style.fontSize).toBe("64px");
  });

  it("aplica alinhamento tipográfico das parts (caixa coluna)", () => {
    const { container } = render(
      <DelpiKpiCard
        label="Consumo"
        value="10"
        kpiParts={{
          title: { style: { textAlign: "right", verticalAlign: "bottom" } },
          value: { style: { textAlign: "center", verticalAlign: "bottom" } },
        }}
      />,
    );
    const title = container.querySelector(".delpi-kpi-card__label") as HTMLElement;
    const value = container.querySelector(".delpi-kpi-card__value") as HTMLElement;
    expect(title.style.flexDirection).toBe("column");
    expect(title.style.textAlign).toBe("right");
    expect(title.style.alignItems).toBe("flex-end");
    expect(title.style.justifyContent).toBe("flex-end");
    expect(value.style.flexDirection).toBe("column");
    expect(value.style.justifyContent).toBe("flex-end");
    expect(value.style.alignItems).toBe("center");
  });

  it("ícone respeita frame e chrome (cores/cantos)", () => {
    const { container } = render(
      <DelpiKpiCard
        label="Consumo"
        value="10"
        icon={<span data-testid="kpi-icon">i</span>}
        kpiParts={{
          icon: {
            visible: true,
            frame: { x: 70, y: 8, w: 18, h: 30 },
            style: {
              fill: "#102a43",
              color: "#7dd3fc",
              borderRadius: 20,
              stroke: "#38bdf8",
              strokeWidth: 2,
            },
          },
        }}
      />,
    );
    const icon = container.querySelector(".delpi-kpi-icon") as HTMLElement;
    expect(icon.className).toContain("delpi-kpi-icon--framed");
    expect(icon.style.left).toBe("70%");
    expect(icon.style.width).toBe("18%");
    expect(icon.style.height).toBe("30%");
    expect(icon.style.borderRadius).toBe("20px");
    expect(icon.style.background).toBe("rgb(16, 42, 67)");
    expect(icon.style.color).toBe("rgb(125, 211, 252)");
  });

  it("título com frame usa posição absoluta no card", () => {
    const { container } = render(
      <DelpiKpiCard
        label="Consumo"
        value="10"
        kpiParts={{
          title: {
            visible: true,
            frame: { x: 5, y: 10, w: 50, h: 20 },
            style: { borderRadius: 6 },
          },
        }}
      />,
    );
    const title = container.querySelector(".delpi-kpi-card__label") as HTMLElement;
    expect(title.className).toContain("delpi-kpi-part--framed");
    expect(title.style.left).toBe("5%");
    expect(title.style.top).toBe("10%");
    expect(title.style.width).toBe("50%");
    expect(title.style.height).toBe("20%");
    expect(title.style.borderRadius).toBe("6px");
  });

  it("Tamanho fixo (px) dimensiona o box do ícone quando sem frame", () => {
    const { container } = render(
      <DelpiKpiCard
        label="Consumo"
        value="10"
        icon={<span data-testid="kpi-icon">i</span>}
        kpiParts={{
          icon: {
            visible: true,
            style: { iconSize: 96 },
          },
        }}
      />,
    );
    const icon = container.querySelector(".delpi-kpi-icon") as HTMLElement;
    expect(icon.style.width).toBe("96px");
    expect(icon.style.height).toBe("96px");
  });

  it("valor usa tipografia padrão 40px (KPI_PART_FONT_SIZE_DEFAULTS), sem auto-fit", () => {
    const { container } = render(
      <DelpiKpiCard label="Consumo" value="10" />,
    );
    const fit = container.querySelector(".delpi-ui-fit-text") as HTMLElement;
    expect(fit?.style.fontSize).toBe("40px");
  });

  it("não reexibe ícone oculto só porque o ReactNode icon foi passado", () => {
    const { container } = render(
      <DelpiKpiCard
        label="Consumo"
        value="10"
        icon={<span data-testid="kpi-icon">i</span>}
        kpiOptions={{ showIcon: true, iconName: "Gauge" }}
        kpiParts={{ icon: { visible: false, style: { fill: "#ffffff" } } }}
      />,
    );
    expect(container.querySelector(".delpi-kpi-icon")).toBeNull();
    expect(container.querySelector("[data-testid='kpi-icon']")).toBeNull();
  });
});
