import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { TextField, textFieldPacClasses } from "./TextField";

afterEach(() => {
  cleanup();
});

describe("TextField", () => {
  it("renderiza label, hint e valor", () => {
    render(
      <TextField
        label="Cliente"
        hint="Nome do cliente"
        value="ACME"
        onChange={() => undefined}
        classNames={textFieldPacClasses("pac")}
      />,
    );

    expect(screen.getByText("Cliente")).toBeTruthy();
    expect(screen.getByDisplayValue("ACME")).toBeTruthy();
    expect(document.querySelector(".delpi-ui-field-label__text")).toBeTruthy();
  });

  it("aplica modificador full width e required", () => {
    const { container } = render(
      <TextField
        label="Descrição"
        value=""
        required
        fullWidth
        onChange={() => undefined}
        classNames={textFieldPacClasses("pac")}
      />,
    );

    expect(container.querySelector(".pac-field--full")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-field__required")).toBeTruthy();
    expect(screen.getByText("*")).toBeTruthy();
    const label = container.querySelector(".delpi-ui-field__label");
    expect(label?.textContent?.replace(/\s+/g, " ").trim()).toBe("Descrição *");
  });

  it("propaga onChange", () => {
    const onChange = vi.fn();
    render(
      <TextField
        label="Busca"
        value=""
        type="search"
        onChange={onChange}
        classNames={textFieldPacClasses("pac")}
      />,
    );

    fireEvent.change(screen.getByRole("searchbox"), { target: { value: "foo" } });
    expect(onChange).toHaveBeenCalledWith("foo");
  });

  it("esconde label visualmente com hideLabel e mantém acessível", () => {
    render(
      <TextField
        label="Filtrar por palavra-chave"
        value=""
        hideLabel
        placeholder="Filtrar por palavra-chave"
        onChange={() => undefined}
        classNames={textFieldPacClasses("pac")}
      />,
    );
    const label = document.querySelector(".delpi-ui-field__label--sr-only");
    expect(label).toBeTruthy();
    expect(screen.getByPlaceholderText("Filtrar por palavra-chave")).toBeTruthy();
  });
});
