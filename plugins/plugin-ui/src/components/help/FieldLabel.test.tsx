import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { FieldLabel } from "./FieldLabel";

afterEach(() => {
  cleanup();
});

describe("FieldLabel", () => {
  it("renderiza label com texto", () => {
    render(<FieldLabel label="Período" />);
    expect(screen.getByText("Período")).toBeTruthy();
  });

  it("associa htmlFor ao label", () => {
    render(<FieldLabel label="Título" htmlFor="titulo" />);
    const label = screen.getByText("Título").closest("label");
    expect(label?.getAttribute("for")).toBe("titulo");
  });

  it("liga hint ao próprio texto do rótulo, sem botão de ícone ?", () => {
    const { container } = render(<FieldLabel label="Duração" hint="Tempo em segundos." />);
    const labelText = screen.getByText("Duração");
    expect(labelText.className).toContain("delpi-ui-field-label__text");
    expect(labelText.getAttribute("aria-describedby")).toBeTruthy();
    expect(labelText.getAttribute("tabindex")).toBe("0");
    expect(container.querySelector(".delpi-ui-help-tooltip__trigger--icon")).toBeNull();
    expect(screen.queryByRole("button", { name: /Ajuda:/ })).toBeNull();
  });

  it("mostra ícone decorativo sem alterar o texto do rótulo", () => {
    render(<FieldLabel label="Categoria" icon={<span data-testid="field-icon" />} />);
    expect(screen.getByText("Categoria")).toBeTruthy();
    expect(screen.getByTestId("field-icon").closest(".delpi-ui-field-label__icon")).toBeTruthy();
  });

  it("irmão: hint continua no texto quando há ícone decorativo", () => {
    const { container } = render(
      <FieldLabel label="Urgência" hint="Prioridade do chamado." icon={<span data-testid="urgency-icon" />} />,
    );
    expect(screen.getByText("Urgência").className).toContain("delpi-ui-field-label__text");
    expect(screen.getByTestId("urgency-icon")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-help-tooltip__trigger--icon")).toBeNull();
  });

  it("negativo: sem hint não cria balão no texto", () => {
    render(<FieldLabel label="Título" />);
    expect(screen.getByText("Título").getAttribute("aria-describedby")).toBeNull();
  });

  it("negativo: sem ícone não cria o marcador decorativo", () => {
    const { container } = render(<FieldLabel label="Título" />);
    expect(container.querySelector(".delpi-ui-field-label__icon")).toBeNull();
  });

  it("preserva className do MFE e mantém a classe canônica delpi-ui-field-label", () => {
    render(<FieldLabel label="Buscar" className="tm-field__label" />);
    const root = screen.getByText("Buscar").closest(".tm-field__label");
    expect(root?.className).toContain("tm-field__label");
    expect(root?.className).toContain("delpi-ui-field-label");
  });

  it("foco no texto do rótulo abre o balão de ajuda", () => {
    render(<FieldLabel label="Modelo" hint="Preenche com um modelo." />);
    fireEvent.focus(screen.getByText("Modelo"));
    expect(screen.getByRole("tooltip", { hidden: true }).textContent).toContain(
      "Preenche com um modelo.",
    );
  });
});
