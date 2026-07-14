import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { FormatPaneShell } from "./FormatPaneShell";

afterEach(() => {
  cleanup();
});

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

  it("envolve abas com help tooltip quando há hint", () => {
    const { container } = render(
      <FormatPaneShell
        title="Camadas"
        tabs={[
          { id: "element", label: "Elemento", hint: "Propriedades do elemento." },
          { id: "layers", label: "Camadas", hint: "Ordem e pilha visual." },
        ]}
        activeTabId="layers"
      >
        <p>Corpo</p>
      </FormatPaneShell>,
    );
    const tabs = screen.getAllByRole("tab");
    expect(tabs.map((tab) => tab.textContent)).toEqual(["Elemento", "Camadas"]);
    expect(container.querySelectorAll(".delpi-ui-help-tooltip").length).toBe(2);
  });

  it("renderiza ícone na aba quando informado", () => {
    function DummyIcon(props: { size?: number; className?: string }) {
      return <svg data-testid="tab-icon" width={props.size} height={props.size} className={props.className} />;
    }

    render(
      <FormatPaneShell
        title="Definir Forma"
        tabs={[{ id: "element", label: "Elemento", icon: DummyIcon as never }]}
        activeTabId="element"
      >
        <p>Corpo</p>
      </FormatPaneShell>,
    );

    expect(screen.getByTestId("tab-icon")).toBeTruthy();
    expect(screen.getByRole("tab", { name: /Elemento/ })).toBeTruthy();
  });
});
