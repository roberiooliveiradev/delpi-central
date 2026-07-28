import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { render, screen, act } from "@testing-library/react";

import {
  generateBrandLightning,
  lightningPathStartsNearOrigin,
} from "./brandLightning";
import { ScreenLoading, screenLoadingBemClasses } from "./ScreenLoading";

describe("generateBrandLightning", () => {
  it("gera paths que partem do origin", () => {
    const origin = { x: 200, y: 150 };
    const paths = generateBrandLightning({
      width: 400,
      height: 300,
      origin,
      density: "medium",
    });
    expect(paths.length).toBeGreaterThanOrEqual(3);
    for (const path of paths) {
      expect(lightningPathStartsNearOrigin(path, origin)).toBe(true);
      expect(path.d).toMatch(/^M /);
    }
  });
});

describe("ScreenLoading", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "ResizeObserver",
      class {
        callback: ResizeObserverCallback;
        constructor(cb: ResizeObserverCallback) {
          this.callback = cb;
        }
        observe(target: Element) {
          const rect = {
            width: 640,
            height: 360,
            x: 0,
            y: 0,
            top: 0,
            left: 0,
            bottom: 360,
            right: 640,
            toJSON: () => ({}),
          };
          this.callback(
            [
              {
                target,
                contentRect: rect,
                borderBoxSize: [],
                contentBoxSize: [],
                devicePixelContentBoxSize: [],
              },
            ],
            this as unknown as ResizeObserver,
          );
        }
        unobserve() {}
        disconnect() {}
      },
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renderiza badge, label e classes fullscreen/dark sem lightning", () => {
    const { container } = render(
      <ScreenLoading
        label="Carregando apresentação"
        variant="fullscreen"
        tone="dark"
        logoSrc="/p/logoMinhaDelpi.svg"
      />,
    );
    const root = container.firstElementChild as HTMLElement;
    expect(root.className).toContain("delpi-ui-screen-loading");
    expect(root.className).toContain("delpi-ui-screen-loading--fullscreen");
    expect(root.className).toContain("delpi-ui-screen-loading--dark");
    expect(root.className).not.toContain("delpi-ui-screen-loading--lightning");
    expect(root.getAttribute("role")).toBe("status");
    expect(screen.getByText("Carregando apresentação")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-screen-loading__badge")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-screen-loading__orbit-ring")).toBeTruthy();
    expect(container.querySelector('img[src="/p/logoMinhaDelpi.svg"]')).toBeTruthy();
  });

  it("renderiza tom light com classes corretas", () => {
    const { container } = render(
      <ScreenLoading label="Carregando" tone="light" logoSrc="/p/logoMinhaDelpi.svg" />,
    );
    const root = container.firstElementChild as HTMLElement;
    expect(root.className).toContain("delpi-ui-screen-loading--light");
    expect(root.className).not.toContain("delpi-ui-screen-loading--dark");
  });

  it("factory aplica prefixo BEM dual-class", () => {
    const cn = screenLoadingBemClasses("pub");
    const { container } = render(
      <ScreenLoading classNames={cn} label="Aguarde" tone="brand" variant="embedded" />,
    );
    const root = container.firstElementChild as HTMLElement;
    expect(root.className).toContain("pub-screen-loading");
    expect(root.className).toContain("delpi-ui-screen-loading");
  });

  it("showLightning opcional renderiza camada SVG", async () => {
    const { container } = render(
      <ScreenLoading label="TV" variant="fullscreen" tone="dark" showLightning />,
    );
    await act(async () => {
      await Promise.resolve();
    });
    expect(container.querySelector("svg.delpi-ui-screen-loading__lightning")).toBeTruthy();
  });
});
