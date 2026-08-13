import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  InteractiveDataCard,
  interactiveDataCardBemClasses,
} from "./InteractiveDataCard";

afterEach(cleanup);

const classNames = interactiveDataCardBemClasses("cm");

describe("InteractiveDataCard", () => {
  it("renderiza campos com tones e dual-class sem ativação", () => {
    const { container } = render(
      <InteractiveDataCard
        classNames={classNames}
        ariaLabel="Cliente ACME"
        fields={[
          { id: "name", label: "Cliente", value: "ACME", valueTone: "title" },
          { id: "open", label: "Em aberto", value: "R$ 10", valueTone: "value" },
          { id: "city", label: "Cidade", value: "Joinville", present: false },
        ]}
        openHint="Abrir"
      />,
    );

    expect(screen.getByRole("article", { name: "Cliente ACME" })).toBeTruthy();
    expect(screen.getByText("ACME")).toBeTruthy();
    expect(screen.queryByText("Joinville")).toBeNull();
    expect(container.querySelector(".cm-interactive-data-card")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-interactive-data-card")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-interactive-data-card--interactive")).toBeNull();
  });

  it("mantém openHint longo no span com classe open-hint (clamp via CSS)", () => {
    const longHint =
      "Clique na linha (ou na proposta) abre o detalhe do documento. Controles internos com destino diferente não propagam o clique.";
    const { container } = render(
      <InteractiveDataCard
        classNames={classNames}
        ariaLabel="Proposta"
        onActivate={() => undefined}
        openHint={longHint}
        fields={[{ id: "ov", label: "OV", value: "OV1" }]}
      />,
    );

    const hint = container.querySelector(".cm-interactive-data-card__open-hint");
    expect(hint?.textContent).toBe(longHint);
    expect(hint?.classList.contains("delpi-ui-interactive-data-card__open-hint")).toBe(true);
  });

  it("ativa com clique e teclado quando onActivate é informado", () => {
    const onActivate = vi.fn();
    render(
      <InteractiveDataCard
        classNames={classNames}
        ariaLabel="Linha 1"
        onActivate={onActivate}
        fields={[{ id: "pedido", label: "Pedido", value: "OV-1" }]}
      />,
    );

    const card = screen.getByRole("button", { name: "Linha 1" });
    fireEvent.click(card);
    fireEvent.keyDown(card, { key: "Enter" });
    expect(onActivate).toHaveBeenCalledTimes(2);
  });
});
