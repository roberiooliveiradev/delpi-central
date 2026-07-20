import { afterEach, describe, expect, it } from "vitest";

import {
  containedModalBoxToStyle,
  measureContainedModalBox,
  resolveContainedModalScrollPort,
} from "./containedModalViewport";

afterEach(() => {
  document.body.innerHTML = "";
});

describe("containedModalViewport", () => {
  it("usa .content como scrollport quando o host MFE está dentro", () => {
    const content = document.createElement("div");
    content.className = "content";
    Object.defineProperty(content, "clientHeight", { configurable: true, value: 800 });

    const host = document.createElement("main");
    host.className = "dashboard-quality-action-plans";
    // Página longa — altura do documento >> viewport (bug antigo do absolute inset 0).
    Object.defineProperty(host, "clientHeight", { configurable: true, value: 4000 });

    content.appendChild(host);
    document.body.appendChild(content);

    expect(resolveContainedModalScrollPort(host)).toBe(content);
  });

  it("mede a caixa pelo scrollport, não pela altura do documento do MFE", () => {
    const content = document.createElement("div");
    content.className = "content";
    content.getBoundingClientRect = () =>
      ({
        top: 48,
        left: 240,
        width: 1000,
        height: 700,
        right: 1240,
        bottom: 748,
        x: 240,
        y: 48,
        toJSON() {
          return {};
        },
      }) as DOMRect;

    const host = document.createElement("main");
    host.className = "dashboard-transformometro";
    host.getBoundingClientRect = () =>
      ({
        top: 48,
        left: 240,
        width: 1000,
        height: 5000,
        right: 1240,
        bottom: 5048,
        x: 240,
        y: 48,
        toJSON() {
          return {};
        },
      }) as DOMRect;

    content.appendChild(host);
    document.body.appendChild(content);

    const box = measureContainedModalBox(host);
    expect(box).toEqual({ top: 48, left: 240, width: 1000, height: 700 });

    const style = containedModalBoxToStyle(box);
    expect(style.position).toBe("fixed");
    expect(style.width).toBe(1000);
    expect(style.height).toBe(700);
    expect(style.top).toBe(48);
    expect(style.left).toBe(240);
    // Regressão: inset shorthand apagava top/left → modal na posição estática.
    expect(style).not.toHaveProperty("inset");
    expect(style.top).not.toBe("auto");
    expect(style.left).not.toBe("auto");
  });
});
