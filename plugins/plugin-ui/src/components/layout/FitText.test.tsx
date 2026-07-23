import { afterEach, describe, expect, it, vi } from "vitest";
import { render, waitFor } from "@testing-library/react";

import { FitText } from "./FitText";

describe("FitText", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("aumenta a fonte quando o host tem espaço (layout flex)", async () => {
    vi.spyOn(HTMLElement.prototype, "clientWidth", "get").mockImplementation(function (
      this: HTMLElement,
    ) {
      if (this.classList.contains("delpi-ui-fit-text")) return 80;
      return 320;
    });
    vi.spyOn(HTMLElement.prototype, "clientHeight", "get").mockImplementation(function (
      this: HTMLElement,
    ) {
      if (this.classList.contains("delpi-ui-fit-text")) return 20;
      return 120;
    });
    vi.spyOn(HTMLElement.prototype, "scrollWidth", "get").mockImplementation(function (
      this: HTMLElement,
    ) {
      const px = Number.parseFloat(this.style.fontSize || "14");
      return Math.ceil(px * 4.2);
    });
    vi.spyOn(HTMLElement.prototype, "scrollHeight", "get").mockImplementation(function (
      this: HTMLElement,
    ) {
      const px = Number.parseFloat(this.style.fontSize || "14");
      return Math.ceil(px * 1.05);
    });

    const { container } = render(
      <div data-testid="host" style={{ width: 320, height: 120 }}>
        <FitText minPx={14} maxPx={200}>
          1.470,25
        </FitText>
      </div>,
    );
    const el = container.querySelector(".delpi-ui-fit-text") as HTMLElement;
    await waitFor(() => {
      const px = Number.parseFloat(el.style.fontSize);
      expect(px).toBeGreaterThan(14);
      expect(px).toBeLessThanOrEqual(120);
    });
  });

  it("respeita fixedPx sem auto-fit", () => {
    const { container } = render(
      <div style={{ width: 320, height: 120 }}>
        <FitText fixedPx={48} minPx={14} maxPx={200}>
          10
        </FitText>
      </div>,
    );
    const el = container.querySelector(".delpi-ui-fit-text") as HTMLElement;
    expect(el.style.fontSize).toBe("48px");
  });
});
