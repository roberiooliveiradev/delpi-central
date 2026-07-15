import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StateBoxPanel, stateBoxBemClasses } from "./StateBoxPanel";

describe("StateBoxPanel", () => {
  const classNames = stateBoxBemClasses("pc");

  it("renderiza título, mensagem e ícone", () => {
    render(
      <StateBoxPanel
        variant="empty"
        title="Nenhum registro"
        message="Ajuste os filtros."
        icon={<span data-testid="icon">!</span>}
        classNames={classNames}
      />,
    );

    expect(screen.getByText("Nenhum registro")).toBeTruthy();
    expect(screen.getByText("Ajuste os filtros.")).toBeTruthy();
    expect(screen.getByTestId("icon")).toBeTruthy();
    expect(document.querySelector(".pc-state-box--empty")).toBeTruthy();
    expect(document.querySelector(".delpi-ui-state-box--empty")).toBeTruthy();
    expect(document.querySelector(".delpi-ui-card")).toBeTruthy();
    expect(document.querySelector(".delpi-ui-state-box__icon")).toBeTruthy();
  });
});
