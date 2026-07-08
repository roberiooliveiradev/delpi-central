import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { formFieldShellKaizenClasses } from "./FormFieldShell";
import { NativeTextField } from "./NativeFormFields";

afterEach(() => {
  cleanup();
});

describe("NativeTextField", () => {
  it("renderiza shell kaizen com input nativo", () => {
    const { container } = render(
      <NativeTextField
        id="kz-title"
        label="Título"
        hint="Nome da melhoria"
        value="Teste"
        onChange={() => undefined}
        classNames={formFieldShellKaizenClasses("kz")}
      />,
    );

    expect(container.querySelector(".kz-field")).toBeTruthy();
    expect(screen.getByLabelText("Título")).toBeTruthy();
    expect(screen.getByDisplayValue("Teste")).toBeTruthy();
  });

  it("aplica span wide", () => {
    const { container } = render(
      <NativeTextField
        id="kz-desc"
        label="Descrição"
        span
        value=""
        onChange={() => undefined}
        classNames={formFieldShellKaizenClasses("kz")}
      />,
    );

    expect(container.querySelector(".kz-span-2")).toBeTruthy();
  });

  it("aceita type datetime-local", () => {
    render(
      <NativeTextField
        id="ca-start"
        label="Início"
        type="datetime-local"
        value="2026-07-08T10:00"
        onChange={() => undefined}
        classNames={formFieldShellKaizenClasses("ca")}
      />,
    );

    const input = screen.getByLabelText("Início");
    expect(input.getAttribute("type")).toBe("datetime-local");
    expect(screen.getByDisplayValue("2026-07-08T10:00")).toBeTruthy();
  });
});
