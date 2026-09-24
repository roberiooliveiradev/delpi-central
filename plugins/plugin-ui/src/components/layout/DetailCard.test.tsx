import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { DetailCard, detailCardRichBemClasses } from "./DetailCard";

afterEach(() => {
  cleanup();
});

describe("DetailCard", () => {
  it("titleHint usa wrap no título sem botão ?", () => {
    const classNames = detailCardRichBemClasses("cm");
    const { container } = render(
      <DetailCard
        title="Worklist"
        titleHint="Itens da minha fila."
        classNames={classNames}
        labels={{ titleHelpAriaLabel: (title) => `Ajuda: ${title}` }}
      >
        <p>Conteúdo</p>
      </DetailCard>,
    );

    expect(screen.getByText("Worklist")).toBeTruthy();
    expect(container.querySelector("button.delpi-ui-help-tooltip__trigger")).toBeNull();
    fireEvent.mouseEnter(container.querySelector(".delpi-ui-help-tooltip")!);
    expect(screen.getByRole("tooltip", { hidden: true }).textContent).toBe("Itens da minha fila.");
  });

  it("sem titleHint não monta HelpTooltip", () => {
    const classNames = detailCardRichBemClasses("cm");
    const { container } = render(
      <DetailCard
        title="Detalhe"
        classNames={classNames}
        labels={{ titleHelpAriaLabel: (title) => `Ajuda: ${title}` }}
      >
        <p>Conteúdo</p>
      </DetailCard>,
    );
    expect(container.querySelector(".delpi-ui-help-tooltip")).toBeNull();
    expect(screen.getByText("Detalhe")).toBeTruthy();
  });
});
