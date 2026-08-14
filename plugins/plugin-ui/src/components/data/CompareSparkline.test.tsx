import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";

import {
  CompareSparkline,
  compareBarHeight,
  compareSparklineBemClasses,
  resolveCompareSparklineTone,
} from "./CompareSparkline";

const classNames = compareSparklineBemClasses("delpi-ui");

describe("resolveCompareSparklineTone", () => {
  it("classifica up down flat", () => {
    expect(resolveCompareSparklineTone(10, 20)).toBe("up");
    expect(resolveCompareSparklineTone(20, 10)).toBe("down");
    expect(resolveCompareSparklineTone(10, 10)).toBe("flat");
  });
});

describe("compareBarHeight", () => {
  it("escala proporcional e mantém mínimo", () => {
    expect(compareBarHeight(50, 100)).toBeGreaterThan(compareBarHeight(25, 100));
    expect(compareBarHeight(0, 100)).toBeGreaterThanOrEqual(3);
  });
});

describe("CompareSparkline", () => {
  it("renderiza gráfico SVG unificado com tom up", () => {
    const { container } = render(
      <CompareSparkline classNames={classNames} prior={100} current={150} />,
    );
    expect(container.querySelector(".delpi-ui-compare-sparkline--up")).toBeTruthy();
    expect(container.querySelectorAll(".delpi-ui-compare-sparkline__bar")).toHaveLength(2);
    expect(container.querySelector(".delpi-ui-compare-sparkline__line")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-compare-sparkline__area")).toBeTruthy();
    expect(container.querySelectorAll(".delpi-ui-compare-sparkline__dot")).toHaveLength(2);
  });
});
