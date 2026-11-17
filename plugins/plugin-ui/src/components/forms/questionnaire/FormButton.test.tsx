import { cleanup, fireEvent, render } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { FormButton } from "./FormButton";

afterEach(cleanup);

describe("FormButton", () => {
  it("primary é o padrão e aplica as classes de escopo + variante", () => {
    const { getByRole } = render(<FormButton>Enviar</FormButton>);
    const button = getByRole("button", { name: "Enviar" });
    expect(button.className).toContain("delpi-ui-action-btn");
    expect(button.className).toContain("delpi-ui-action-btn--primary");
    expect(button.className).toContain("delpi-ui-form-button");
    expect(button.className).toContain("delpi-ui-form-button--primary");
  });

  it("secondary mapeia para a variante default do ActionButton", () => {
    const { getByRole } = render(
      <FormButton variant="secondary">Voltar</FormButton>,
    );
    const button = getByRole("button", { name: "Voltar" });
    expect(button.className).not.toContain("delpi-ui-action-btn--primary");
    expect(button.className).toContain("delpi-ui-form-button--secondary");
  });

  it("busy mostra busyLabel, não dispara onClick e mantém o foco (softDisabled)", () => {
    const onClick = vi.fn();
    const { getByRole } = render(
      <FormButton busy busyLabel="Enviando…" onClick={onClick}>
        Enviar
      </FormButton>,
    );
    const button = getByRole("button", { name: "Enviando…" });
    // Soft: sem o atributo disabled nativo → continua focável.
    expect(button).not.toHaveProperty("disabled", true);
    expect(button.getAttribute("aria-disabled")).toBe("true");
    button.focus();
    fireEvent.click(button);
    expect(onClick).not.toHaveBeenCalled();
    expect(document.activeElement).toBe(button);
  });

  it("não busy dispara onClick normalmente", () => {
    const onClick = vi.fn();
    const { getByRole } = render(
      <FormButton onClick={onClick}>Avançar</FormButton>,
    );
    fireEvent.click(getByRole("button", { name: "Avançar" }));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("fullWidth adiciona a classe --full", () => {
    const { getByRole } = render(<FormButton fullWidth>Ir</FormButton>);
    expect(getByRole("button", { name: "Ir" }).className).toContain(
      "delpi-ui-form-button--full",
    );
  });
});
