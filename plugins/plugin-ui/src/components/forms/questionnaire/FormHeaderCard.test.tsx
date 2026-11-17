import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { FormHeaderCard } from "./FormHeaderCard";

const base = {
  logo: <span data-testid="logo" />,
  title: "Título",
};

afterEach(cleanup);

describe("FormHeaderCard", () => {
  it("renderiza top (logo + meta + ação), título, subtítulo, etapa e progresso", () => {
    const { container } = render(
      <FormHeaderCard
        {...base}
        prefix="puc"
        meta="Responda até 31/12/2026"
        headerAction={<button type="button">tema</button>}
        subtitle="Respondendo por Empresa X"
        step={{ label: "Etapa 1 de 3 · Avaliação", progressLabel: "3 de 12" }}
        progress={{ done: 3, total: 12, ariaLabel: "Progresso" }}
      />,
    );
    const card = container.firstElementChild!;

    expect(
      card.querySelector(".delpi-ui-form-header__meta")!.textContent,
    ).toBe("Responda até 31/12/2026");
    expect(
      card.querySelector(".delpi-ui-form-header__title")!.textContent,
    ).toBe("Título");
    expect(
      card.querySelector(".delpi-ui-form-header__subtitle")!.textContent,
    ).toBe("Respondendo por Empresa X");
    expect(card.querySelector(".delpi-ui-form-header__divider")).toBeTruthy();
    expect(
      card.querySelector(".delpi-ui-form-header__step-label")!.textContent,
    ).toBe("Etapa 1 de 3 · Avaliação");
    expect(
      card.querySelector(".delpi-ui-form-header__step-progress")!.textContent,
    ).toBe("3 de 12");

    const bar = screen.getByRole("progressbar");
    expect(bar.getAttribute("aria-valuenow")).toBe("25");
    // texto do progresso aparece uma única vez (na linha da etapa)
    expect(
      card.querySelectorAll(".delpi-ui-form-progress__label").length,
    ).toBe(0);
  });

  it("headerAction fica no cluster à direita (__end) mesmo sem meta", () => {
    const { container } = render(
      <FormHeaderCard
        {...base}
        headerAction={<button type="button">tema</button>}
      />,
    );
    const card = container.firstElementChild!;
    const end = card.querySelector(".delpi-ui-form-header__end")!;
    expect(end).toBeTruthy();
    expect(end.querySelector("button")).toBeTruthy();
    expect(end.querySelector(".delpi-ui-form-header__meta")).toBeNull();
  });

  it("omite meta, subtítulo, divisor, etapa e progresso ausentes", () => {
    const { container } = render(<FormHeaderCard {...base} />);
    const card = container.firstElementChild!;
    expect(card.querySelector(".delpi-ui-form-header__meta")).toBeNull();
    expect(card.querySelector(".delpi-ui-form-header__subtitle")).toBeNull();
    expect(card.querySelector(".delpi-ui-form-header__divider")).toBeNull();
    expect(card.querySelector(".delpi-ui-form-header__step")).toBeNull();
    expect(card.querySelector("[role='progressbar']")).toBeNull();
  });
});
