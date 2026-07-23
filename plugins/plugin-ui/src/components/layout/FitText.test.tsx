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
    vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function (
      this: HTMLElement,
    ) {
      if (this.classList.contains("delpi-ui-fit-text")) {
        return {
          width: 80,
          height: 20,
          top: 0,
          left: 0,
          bottom: 20,
          right: 80,
          x: 0,
          y: 0,
          toJSON() {},
        } as DOMRect;
      }
      return {
        width: 320,
        height: 120,
        top: 0,
        left: 0,
        bottom: 120,
        right: 320,
        x: 0,
        y: 0,
        toJSON() {},
      } as DOMRect;
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

  it("tenta de novo quando o host ainda não tem altura", async () => {
    let hostH = 0;
    vi.spyOn(HTMLElement.prototype, "clientWidth", "get").mockReturnValue(320);
    vi.spyOn(HTMLElement.prototype, "clientHeight", "get").mockImplementation(function (
      this: HTMLElement,
    ) {
      if (this.classList.contains("delpi-ui-fit-text")) return 20;
      return hostH;
    });
    vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function (
      this: HTMLElement,
    ) {
      const h = this.classList.contains("delpi-ui-fit-text") ? 20 : hostH;
      const w = this.classList.contains("delpi-ui-fit-text") ? 80 : 320;
      return {
        width: w,
        height: h,
        top: 0,
        left: 0,
        bottom: h,
        right: w,
        x: 0,
        y: 0,
        toJSON() {},
      } as DOMRect;
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
      <div style={{ width: 320, height: 120 }}>
        <FitText minPx={14} maxPx={200}>
          99
        </FitText>
      </div>,
    );
    const el = container.querySelector(".delpi-ui-fit-text") as HTMLElement;
    expect(Number.parseFloat(el.style.fontSize)).toBe(14);
    hostH = 120;
    await waitFor(() => {
      expect(Number.parseFloat(el.style.fontSize)).toBeGreaterThan(14);
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
