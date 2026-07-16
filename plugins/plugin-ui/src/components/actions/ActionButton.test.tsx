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
});

describe("BackLink", () => {
  it("renderiza seta e dispara onClick", () => {
    const onClick = vi.fn();
    const { container } = render(<BackLink onClick={onClick}>Voltar para atas</BackLink>);

    fireEvent.click(screen.getByRole("button", { name: /Voltar para atas/ }));

    expect(onClick).toHaveBeenCalledTimes(1);
    expect(container.querySelector(".delpi-ui-back-link__arrow")).toBeTruthy();
  });
});
