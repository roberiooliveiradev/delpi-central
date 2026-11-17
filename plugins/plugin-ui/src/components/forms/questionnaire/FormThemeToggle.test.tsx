import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { FormThemeToggle } from "./FormThemeToggle";
import { QuestionnaireThemeScope } from "./QuestionnaireThemeScope";

const originalMatchMedia = window.matchMedia;

function installMatchMedia(initialDark: boolean) {
  const mql = {
    matches: initialDark,
    media: "(prefers-color-scheme: dark)",
    onchange: null,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    addListener: vi.fn(),
    removeListener: vi.fn(),
    dispatchEvent: () => true,
  };
  Object.defineProperty(window, "matchMedia", {
    configurable: true,
    writable: true,
    value: vi.fn(() => mql),
  });
}

afterEach(() => {
  cleanup();
  Object.defineProperty(window, "matchMedia", {
    configurable: true,
    writable: true,
    value: originalMatchMedia,
  });
});

describe("FormThemeToggle", () => {
  it("alterna o tema do escopo, trocando ícone e aria-pressed", () => {
    installMatchMedia(false);
    const { container } = render(
      <QuestionnaireThemeScope>
        <FormThemeToggle ariaLabel="Alternar tema" />
      </QuestionnaireThemeScope>,
    );
    const button = screen.getByRole("button", { name: "Alternar tema" });
    expect(button.getAttribute("aria-pressed")).toBe("false");
    expect(button.querySelector("svg")!.className.baseVal).toContain("moon");

    fireEvent.click(button);

    expect(button.getAttribute("aria-pressed")).toBe("true");
    expect(button.querySelector("svg")!.className.baseVal).toContain("sun");
    expect(
      container.firstElementChild!.getAttribute("data-color-scheme"),
    ).toBe("dark");
  });

  it("não renderiza quando o escopo tem esquema fixo", () => {
    installMatchMedia(false);
    render(
      <QuestionnaireThemeScope colorScheme="light">
        <FormThemeToggle ariaLabel="Alternar tema" />
      </QuestionnaireThemeScope>,
    );
    expect(
      screen.queryByRole("button", { name: "Alternar tema" }),
    ).toBeNull();
  });
});
