import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { FormatPaneShell } from "./FormatPaneShell";

describe("FormatPaneShell", () => {
  it("renderiza título, abas e dispara onClose", () => {
    const onClose = vi.fn();
    const onTabChange = vi.fn();

    render(
      <FormatPaneShell
        title="Definir elemento"
        onClose={onClose}
        tabs={[
          { id: "element", label: "Elemento" },
          { id: "data", label: "Dados" },
        ]}
        activeTabId="element"
        onTabChange={onTabChange}
      >
        <p>Conteúdo</p>
      </FormatPaneShell>,
    );

    expect(screen.getByRole("heading", { name: "Definir elemento" })).toBeTruthy();
    expect(screen.getByText("Conteúdo")).toBeTruthy();

    fireEvent.click(screen.getByRole("tab", { name: "Dados" }));
    expect(onTabChange).toHaveBeenCalledWith("data");

    fireEvent.click(screen.getByRole("button", { name: "Fechar painel" }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
