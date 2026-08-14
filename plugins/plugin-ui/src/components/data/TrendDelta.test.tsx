import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";

import {
  TrendDelta,
  formatTrendDeltaPct,
  resolveTrendDeltaTone,
  trendDeltaBemClasses,
} from "./TrendDelta";

const classNames = trendDeltaBemClasses("delpi-ui");

describe("TrendDelta helpers", () => {
  it("formata e classifica tom", () => {
    expect(formatTrendDeltaPct(12.5)).toMatch(/\+12/);
    expect(formatTrendDeltaPct(-9)).toMatch(/-9/);
    expect(formatTrendDeltaPct(null)).toBe("—");
    expect(resolveTrendDeltaTone(5)).toBe("up");
    expect(resolveTrendDeltaTone(-1)).toBe("down");
    expect(resolveTrendDeltaTone(0)).toBe("flat");
  });
});

describe("TrendDelta", () => {
  it("aplica classe de tom", () => {
    const { container } = render(
      <TrendDelta classNames={classNames} value={10} />,
    );
    expect(container.querySelector(".delpi-ui-trend-delta--up")).toBeTruthy();
  });
});
