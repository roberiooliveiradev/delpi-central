import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ActionButton } from "./ActionButton";
import { BackLink } from "./BackLink";

afterEach(() => {
  cleanup();
});

describe("ActionButton", () => {
  it("renderiza variante primary e dispara onClick", () => {
    const onClick = vi.fn();
    const { container } = render(
      <ActionButton variant="primary" onClick={onClick}>
        Salvar
      </ActionButton>,
    );

    const button = screen.getByRole("button", { name: "Salvar" });
    fireEvent.click(button);

    expect(onClick).toHaveBeenCalledTimes(1);
    expect(container.querySelector(".delpi-ui-action-btn--primary")).toBeTruthy();
  });

  it("repassa aria-expanded no botão", () => {
    render(
      <ActionButton variant="ghost" aria-label="Contexto" aria-expanded>
        Ctx
      </ActionButton>,
    );
    expect(screen.getByRole("button", { name: "Contexto" }).getAttribute("aria-expanded")).toBe(
      "true",
    );
  });

  it("desabilitado não dispara onClick e aceita className extra", () => {
    const onClick = vi.fn();
    const { container } = render(
      <ActionButton disabled onClick={onClick} className="cipa-extra">
        Recusar
      </ActionButton>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Recusar" }));

    expect(onClick).not.toHaveBeenCalled();
    expect(container.querySelector(".delpi-ui-action-btn.cipa-extra")).toBeTruthy();
  });

  it("com href renderiza anchor real e left-click chama onClick", () => {
    const onClick = vi.fn();
    render(
      <ActionButton
        href="/apps/commercial/open-orders/01/1/01/op/OP1"
        title="Abrir página da OP OP1"
        onClick={onClick}
      >
        Abrir página da OP
      </ActionButton>,
    );

    const link = screen.getByRole("link", { name: "Abrir página da OP OP1" });
    expect(link.getAttribute("href")).toBe(
      "/apps/commercial/open-orders/01/1/01/op/OP1",
    );
    fireEvent.click(link);
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("com href e Ctrl+click não chama onClick (navegação nativa)", () => {
    const onClick = vi.fn();
    render(
      <ActionButton
        href="/apps/commercial/customers/1/01"
        title="Abrir conta"
        onClick={onClick}
      >
        Abrir conta
      </ActionButton>,
    );

    fireEvent.click(screen.getByRole("link", { name: "Abrir conta" }), {
      ctrlKey: true,
    });
    expect(onClick).not.toHaveBeenCalled();
  });
});

describe("BackLink", () => {
  it("renderiza seta e dispara onClick", () => {
    const onClick = vi.fn();
    const { container } = render(<BackLink onClick={onClick}>Voltar para atas</BackLink>);

    fireEvent.click(screen.getByRole("button", { name: /Voltar para atas/ }));

    expect(onClick).toHaveBeenCalledTimes(1);
    expect(container.querySelector(".delpi-ui-back-link__arrow")).toBeTruthy();
  });

  it("aplica variante destacada sem alterar o padrão", () => {
    const { container, rerender } = render(
      <BackLink variant="prominent" onClick={() => undefined}>
        Voltar
      </BackLink>,
    );

    expect(container.firstElementChild?.className).toContain(
      "delpi-ui-back-link--prominent",
    );

    rerender(<BackLink onClick={() => undefined}>Voltar</BackLink>);
    expect(container.firstElementChild?.className).not.toContain(
      "delpi-ui-back-link--prominent",
    );
  });

  it("usa anchor real quando recebe href", () => {
    render(<BackLink href="/apps/commercial/customers">Minha carteira</BackLink>);

    expect(
      screen.getByRole("link", { name: /Minha carteira/ }).getAttribute("href"),
    ).toBe("/apps/commercial/customers");
  });
});
