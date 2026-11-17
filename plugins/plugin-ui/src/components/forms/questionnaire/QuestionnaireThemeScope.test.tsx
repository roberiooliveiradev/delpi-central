import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  QuestionnaireThemeScope,
  useQuestionnaireColorScheme,
} from "./QuestionnaireThemeScope";

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

function SchemeProbe() {
  const { scheme, toggle, userChosen, canToggle } =
    useQuestionnaireColorScheme();
  return (
    <button type="button" data-testid="probe" onClick={toggle}>
      {scheme}:{String(userChosen)}:{String(canToggle)}
    </button>
  );
}

describe("QuestionnaireThemeScope", () => {
  it("aplica data-color-scheme do aparelho e as classes dual (prefixo + delpi-ui-form-root)", () => {
    installMatchMedia(true);
    const { container } = render(
      <QuestionnaireThemeScope prefix="puc">conteúdo</QuestionnaireThemeScope>,
    );
    const root = container.firstElementChild!;
    expect(root.className).toContain("puc-form-root");
    expect(root.className).toContain("delpi-ui-form-root");
    expect(root.getAttribute("data-color-scheme")).toBe("dark");
  });

  it("resolve light com aparelho claro e mescla className", () => {
    installMatchMedia(false);
    const { container } = render(
      <QuestionnaireThemeScope className="extra">x</QuestionnaireThemeScope>,
    );
    const root = container.firstElementChild!;
    expect(root.getAttribute("data-color-scheme")).toBe("light");
    expect(root.className).toContain("extra");
  });

  it("colorScheme fixo ignora o aparelho", () => {
    installMatchMedia(true);
    const { container } = render(
      <QuestionnaireThemeScope colorScheme="light">x</QuestionnaireThemeScope>,
    );
    expect(container.firstElementChild!.getAttribute("data-color-scheme")).toBe(
      "light",
    );
  });

  it("contexto expõe scheme/userChosen e toggle() muda o data-color-scheme", () => {
    installMatchMedia(false);
    const { container } = render(
      <QuestionnaireThemeScope>
        <SchemeProbe />
      </QuestionnaireThemeScope>,
    );
    const probe = screen.getByTestId("probe");
    expect(probe.textContent).toBe("light:false:true");

    fireEvent.click(probe);

    expect(probe.textContent).toBe("dark:true:true");
    expect(container.firstElementChild!.getAttribute("data-color-scheme")).toBe(
      "dark",
    );
  });

  it("canToggle=false com esquema fixo e toggle() não faz nada", () => {
    installMatchMedia(false);
    render(
      <QuestionnaireThemeScope colorScheme="dark">
        <SchemeProbe />
      </QuestionnaireThemeScope>,
    );
    const probe = screen.getByTestId("probe");
    expect(probe.textContent).toBe("dark:false:false");

    fireEvent.click(probe);

    // esquema fixo permanece dark; toggle é no-op
    expect(probe.textContent).toBe("dark:false:false");
  });
});
