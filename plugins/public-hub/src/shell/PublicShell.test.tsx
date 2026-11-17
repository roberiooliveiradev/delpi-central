/**
 * Chrome `bare` do shell público (§14.6.6): sem `pub-stage`, sem
 * `ThemeToggle`, sem logo do shell. Demais modos inalterados.
 */
import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

// Registro real puxa todas as apps (e seus imports remotos); o teste de
// chrome só precisa de um registro vazio e mutável.
vi.mock("./registry.ts", () => ({ publicRegistry: {} }));
// O pin de viewport é só para kiosk (TV) e resolve o pacote de apresentação
// via remote — sem efeito no que este teste cobre.
vi.mock("./useKioskVisualViewportPin.ts", () => ({
  useKioskVisualViewportPin: () => {},
}));

import { PublicShell } from "./PublicShell.tsx";
import { publicRegistry } from "./registry.ts";
import type { PublicPageDefinition } from "./types.ts";

const TEST_APP = "test-shell-chrome";

function register(page: PublicPageDefinition) {
  publicRegistry[TEST_APP] = { p: page };
  window.history.pushState({}, "", `/p/${TEST_APP}/p/tok-teste`);
}

afterEach(() => {
  delete publicRegistry[TEST_APP];
  window.history.pushState({}, "", "/");
});

function page(chrome: PublicPageDefinition["chrome"]): PublicPageDefinition {
  return {
    chrome,
    load: async () => ({ ok: true }),
    render: () => <div data-testid="page-content">conteúdo da página</div>,
  };
}

describe("chrome bare", () => {
  it("renderiza só a página — sem stage, toggle de tema nem logo do shell", async () => {
    register(page("bare"));
    const { container } = render(<PublicShell />);
    await screen.findByTestId("page-content");
    expect(container.querySelector(".pub-stage")).toBeNull();
    expect(container.querySelector(".pub-theme-toggle")).toBeNull();
    expect(container.querySelector(".pub-logo")).toBeNull();
    expect(container.querySelector(".pub-content")).toBeNull();
  });
});

describe("demais chromes inalterados", () => {
  it("default mantém stage, logo e toggle de tema", async () => {
    register(page("default"));
    const { container } = render(<PublicShell />);
    await screen.findByTestId("page-content");
    expect(container.querySelector(".pub-stage")).not.toBeNull();
    expect(container.querySelector(".pub-theme-toggle")).not.toBeNull();
    expect(container.querySelector(".pub-logo")).not.toBeNull();
  });

  it("fullpage mantém stage e toggle de tema", async () => {
    register(page("fullpage"));
    const { container } = render(<PublicShell />);
    await screen.findByTestId("page-content");
    expect(
      container.querySelector(".pub-stage--fullpage"),
    ).not.toBeNull();
    expect(container.querySelector(".pub-theme-toggle")).not.toBeNull();
  });
});
