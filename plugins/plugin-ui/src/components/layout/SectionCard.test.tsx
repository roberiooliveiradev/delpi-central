import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SectionCard, sectionCardPacBemClasses } from "./SectionCard";

afterEach(() => {
  cleanup();
});

const labels = {
  titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
  expandAriaLabel: (title: string) => `Expandir ${title}`,
  collapseAriaLabel: (title: string) => `Recolher ${title}`,
};

describe("SectionCard fill", () => {
  it("envolve o corpo e preenche a altura do pai", () => {
    const { container } = render(
      <SectionCard
        title="Meus chamados"
        fill
        classNames={sectionCardPacBemClasses("cm")}
        labels={labels}
      >
        <p>Tabela</p>
      </SectionCard>,
    );

    expect(container.querySelector(".delpi-ui-section-card--fill")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-section-card__body")?.textContent).toContain("Tabela");
  });

  it("não envolve o corpo quando a seção não preenche nem recolhe", () => {
    const { container } = render(
      <SectionCard
        title="Meus chamados"
        classNames={sectionCardPacBemClasses("cm")}
        labels={labels}
      >
        <p>Tabela</p>
      </SectionCard>,
    );

    expect(container.querySelector(".delpi-ui-section-card--fill")).toBeNull();
    expect(container.querySelector(".delpi-ui-section-card__body")).toBeNull();
  });
});

describe("SectionCard collapsible", () => {
  it("recolhe e expande o corpo", () => {
    const onOpenChange = vi.fn();
    render(
      <SectionCard
        title="Nova tarefa"
        classNames={sectionCardPacBemClasses("cm")}
        labels={labels}
        collapsible
        defaultOpen
        onOpenChange={onOpenChange}
      >
        <p>Conteúdo do formulário</p>
      </SectionCard>,
    );

    expect(screen.getByText("Conteúdo do formulário")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Recolher Nova tarefa" }));
    expect(onOpenChange).toHaveBeenCalledWith(false);
    expect(screen.queryByText("Conteúdo do formulário")).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "Expandir Nova tarefa" }));
    expect(onOpenChange).toHaveBeenCalledWith(true);
    expect(screen.getByText("Conteúdo do formulário")).toBeTruthy();
  });

  it("mantém o subtítulo visível quando recolhido", () => {
    render(
      <SectionCard
        title="Contexto"
        subtitle="Pedido 002573"
        classNames={sectionCardPacBemClasses("cm")}
        labels={labels}
        collapsible
        defaultOpen={false}
      >
        <p>Sobre</p>
      </SectionCard>,
    );

    expect(screen.getByText("Pedido 002573")).toBeTruthy();
    expect(screen.queryByText("Sobre")).toBeNull();
  });
});
