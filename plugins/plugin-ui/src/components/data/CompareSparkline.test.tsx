import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";

import {
  CompareSparkline,
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

describe("CompareSparkline", () => {
  it("renderiza barras e spark com tom up", () => {
    const { container } = render(
      <CompareSparkline classNames={classNames} prior={100} current={150} />,
    );
    expect(container.querySelector(".delpi-ui-compare-sparkline--up")).toBeTruthy();
    expect(container.querySelectorAll(".delpi-ui-compare-sparkline__bar")).toHaveLength(2);
    expect(container.querySelector("svg path")).toBeTruthy();
  });
});
