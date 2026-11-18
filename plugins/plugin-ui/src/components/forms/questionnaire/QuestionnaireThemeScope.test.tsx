import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
} from "@testing-library/react";
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

function installMatchMediaQueries({ dark = false, reduce = false } = {}) {
  const listeners: Array<(event: { matches: boolean }) => void> = [];
  const makeMql = (media: string) => ({
    matches: media.includes("color-scheme") ? dark : reduce,
    media,
    onchange: null,
    addEventListener: vi.fn(
      (_type: string, cb: (event: { matches: boolean }) => void) =>
        listeners.push(cb),
    ),
    removeEventListener: vi.fn(),
    addListener: vi.fn(),
    removeListener: vi.fn(),
    dispatchEvent: () => true,
  });
  Object.defineProperty(window, "matchMedia", {
    configurable: true,
    writable: true,
    value: vi.fn(makeMql),
  });
  return {
    emitDeviceChange(matches: boolean) {
      listeners.forEach((cb) => cb({ matches }));
    },
  };
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

  it("R26: sem data-theme-transition no carregamento (nem no escuro)", () => {
    installMatchMediaQueries({ dark: true });
    const { container } = render(
      <QuestionnaireThemeScope>x</QuestionnaireThemeScope>,
    );
    const root = container.firstElementChild!;
    expect(root.getAttribute("data-color-scheme")).toBe("dark");
    expect(root.hasAttribute("data-theme-transition")).toBe(false);
  });

  it("R26: toggle liga data-theme-transition durante ~220 ms e remove depois", () => {
    vi.useFakeTimers();
    try {
      installMatchMediaQueries({ dark: false });
      const { container } = render(
        <QuestionnaireThemeScope>
          <SchemeProbe />
        </QuestionnaireThemeScope>,
      );
      const root = container.firstElementChild!;
      expect(root.hasAttribute("data-theme-transition")).toBe(false);
      fireEvent.click(screen.getByTestId("probe"));
      expect(root.getAttribute("data-color-scheme")).toBe("dark");
      expect(root.hasAttribute("data-theme-transition")).toBe(true);
      act(() => vi.advanceTimersByTime(250));
      expect(root.hasAttribute("data-theme-transition")).toBe(false);
    } finally {
      vi.useRealTimers();
    }
  });

  it("R26: mudança do aparelho também liga data-theme-transition", () => {
    const env = installMatchMediaQueries({ dark: false });
    const { container } = render(
      <QuestionnaireThemeScope>x</QuestionnaireThemeScope>,
    );
    const root = container.firstElementChild!;
    act(() => env.emitDeviceChange(true));
    expect(root.getAttribute("data-color-scheme")).toBe("dark");
    expect(root.hasAttribute("data-theme-transition")).toBe(true);
  });

  it("R26: prefers-reduced-motion faz troca imediata sem atributo", () => {
    installMatchMediaQueries({ dark: false, reduce: true });
    const { container } = render(
      <QuestionnaireThemeScope>
        <SchemeProbe />
      </QuestionnaireThemeScope>,
    );
    const root = container.firstElementChild!;
    fireEvent.click(screen.getByTestId("probe"));
    expect(root.getAttribute("data-color-scheme")).toBe("dark");
    expect(root.hasAttribute("data-theme-transition")).toBe(false);
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
