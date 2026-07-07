import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ModalShell, modalShellBemClasses } from "./ModalShell";

describe("ModalShell", () => {
  it("não renderiza quando fechado", () => {
    const { container } = render(
      <ModalShell
        open={false}
        title="Confirmar"
        onClose={vi.fn()}
        classNames={modalShellBemClasses("pac")}
      >
        <p>Conteúdo</p>
      </ModalShell>,
    );

    expect(container.innerHTML).toBe("");
  });

  it("renderiza título e corpo quando aberto", () => {
    render(
      <ModalShell open title="Confirmar exclusão" onClose={vi.fn()} classNames={modalShellBemClasses("pac")}>
        <p>Mensagem</p>
      </ModalShell>,
    );

    expect(screen.getByRole("dialog", { name: "Confirmar exclusão" })).toBeTruthy();
    expect(screen.getByText("Mensagem")).toBeTruthy();
  });
});
