import { afterEach, describe, expect, it, vi } from "vitest";
import { act, render, waitFor } from "@testing-library/react";

import { StableResponsiveContainer } from "./StableResponsiveContainer";

type RoCallback = ResizeObserverCallback;

describe("StableResponsiveContainer", () => {
  const observers: Array<{ cb: RoCallback; el: Element }> = [];

  afterEach(() => {
    observers.length = 0;
    vi.restoreAllMocks();
  });

  it("não dispara cascata de updates quando a largura oscila (scrollbar/sidebar)", async () => {
    let hostWidth = 1000;
    vi.spyOn(HTMLElement.prototype, "clientWidth", "get").mockImplementation(function (
      this: HTMLElement,
    ) {
      if (this.hasAttribute("data-stable-chart-host")) return hostWidth;
      return 1000;
    });
    vi.spyOn(HTMLElement.prototype, "clientHeight", "get").mockReturnValue(280);

    class MockRO {
      constructor(private readonly cb: RoCallback) {}
      observe(el: Element) {
        observers.push({ cb: this.cb, el });
      }
      unobserve() {}
      disconnect() {}
    }
    vi.stubGlobal("ResizeObserver", MockRO);

    let renders = 0;
    function Probe() {
      renders += 1;
      return <div data-testid="probe">ok</div>;
    }

    render(
      <StableResponsiveContainer height={280} sizeEpsilonPx={1}>
        <Probe />
      </StableResponsiveContainer>,
    );

    await waitFor(() => {
      expect(renders).toBeGreaterThanOrEqual(1);
    });
    const afterMount = renders;

    await act(async () => {
      /* Oscilação clássica scrollbar / flex: ±15px em rajada síncrona + rAF. */
      for (const w of [985, 1000, 985, 1000, 985, 1000]) {
        hostWidth = w;
        for (const obs of observers) {
          obs.cb(
            [
              {
                target: obs.el,
                contentRect: {
                  width: w,
                  height: 280,
                  top: 0,
                  left: 0,
                  bottom: 280,
                  right: w,
                  x: 0,
                  y: 0,
                  toJSON() {},
                },
                borderBoxSize: [],
                contentBoxSize: [],
                devicePixelContentBoxSize: [],
              } as ResizeObserverEntry,
            ],
            obs as unknown as ResizeObserver,
          );
        }
        await new Promise<void>((resolve) => requestAnimationFrame(() => resolve()));
      }
    });

    /* Com epsilon 1 cada flip ±15 atualiza — mas rAF + bailout impede #185 (dezenas sync). */
    expect(renders - afterMount).toBeLessThan(40);
  });
});
