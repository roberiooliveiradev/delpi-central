import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render } from "@testing-library/react";

import { FillGradientPanel } from "./FillGradientPanel";
import { DELPI_STANDARD_COLORS, DELPI_THEME_COLOR_GRID } from "./colorPalettes";

afterEach(() => {
  cleanup();
});

describe("FillGradientPanel", () => {
  it("arrastar a marca do meio emite nova position", () => {
    const onChange = vi.fn();
    const { container } = render(
      <FillGradientPanel
        value={{
          kind: "gradient",
          angle: 180,
          stops: [
            { color: "#111111", position: 0 },
            { color: "#888888", position: 50 },
            { color: "#eeeeee", position: 100 },
          ],
        }}
        onChange={onChange}
        themeRows={DELPI_THEME_COLOR_GRID}
        standardColors={DELPI_STANDARD_COLORS}
      />,
    );
    const bar = container.querySelector(".delpi-ui-fill-stops__bar");
    const marks = container.querySelectorAll(".delpi-ui-fill-stops__mark");
    expect(bar).toBeTruthy();
    expect(marks).toHaveLength(3);
    vi.spyOn(bar as HTMLDivElement, "getBoundingClientRect").mockReturnValue({
      left: 0,
      width: 100,
      top: 0,
      height: 16,
      right: 100,
      bottom: 16,
      x: 0,
      y: 0,
      toJSON: () => ({}),
    });
    fireEvent.pointerDown(marks[1]!, { clientX: 50, pointerId: 1 });
    fireEvent.pointerMove(bar!, { clientX: 35, pointerId: 1 });
    expect(onChange).toHaveBeenCalled();
    const last = onChange.mock.calls.at(-1)?.[0];
    expect(last?.kind).toBe("gradient");
    expect(last?.stops.some((stop: { position: number }) => Math.abs(stop.position - 35) < 1)).toBe(
      true,
    );
  });
});
