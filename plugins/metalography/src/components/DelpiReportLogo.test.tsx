/** @vitest-environment jsdom */
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it } from "vitest";

import { DelpiReportLogo } from "./DelpiReportLogo";

let root: Root | undefined;

afterEach(() => {
  act(() => root?.unmount());
  root = undefined;
  document.body.innerHTML = "";
  document.documentElement.removeAttribute("data-theme");
});

function mount(): HTMLImageElement {
  const host = document.createElement("div");
  document.body.appendChild(host);
  root = createRoot(host);
  act(() => {
    root?.render(<DelpiReportLogo alt="Delpi — conexões elétricas" />);
  });
  const image = host.querySelector("img");
  if (!(image instanceof HTMLImageElement)) throw new Error("logo ausente");
  return image;
}

describe("logo Delpi do relatório", () => {
  it("usa a logo documental no tema claro", () => {
    document.documentElement.setAttribute("data-theme", "light");
    const image = mount();
    expect(image.getAttribute("src")).toContain("delpi-logo");
    expect(image.getAttribute("src")).not.toContain("on-dark");
    expect(image.getAttribute("data-print-src")).toBe(image.getAttribute("src"));
  });

  it("troca para a logo de fundo escuro quando o Portal muda o tema", async () => {
    document.documentElement.setAttribute("data-theme", "light");
    const image = mount();
    await act(async () => {
      document.documentElement.setAttribute("data-theme", "dark");
    });
    expect(image.getAttribute("src")).toContain("delpi-logo-on-dark");
    expect(image.getAttribute("data-print-src")).not.toContain("on-dark");
  });

  it("não troca a logo quando outro atributo do documento muda", async () => {
    document.documentElement.setAttribute("data-theme", "light");
    const image = mount();
    await act(async () => {
      document.documentElement.setAttribute("lang", "pt-BR");
    });
    expect(image.getAttribute("src")).not.toContain("on-dark");
  });
});
