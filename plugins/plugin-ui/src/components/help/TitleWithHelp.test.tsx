import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { TitleWithHelp, titleWithHelpPacClasses } from "./TitleWithHelp";

const LABELS = {
  titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
};

afterEach(() => {
  cleanup();
});

describe("TitleWithHelp", () => {
  it("renderiza título com balão de ajuda", () => {
    const { container } = render(
      <TitleWithHelp
        title="Suas ações"
        hint="Fila pessoal"
        classNames={titleWithHelpPacClasses("pac")}
        labels={LABELS}
      />,
    );

    expect(screen.getByText("Suas ações")).toBeTruthy();
    const wrap = container.querySelector(".delpi-ui-help-tooltip--wrap");
    expect(wrap).toBeTruthy();
    fireEvent.mouseEnter(wrap!);
    expect(screen.getByRole("tooltip", { hidden: true }).textContent).toBe("Fila pessoal");
  });

  it("omite balão quando hint ausente", () => {
    render(
      <TitleWithHelp
        title="Resumo"
        classNames={titleWithHelpPacClasses("pac")}
        labels={LABELS}
      />,
    );

    expect(screen.getByText("Resumo")).toBeTruthy();
    expect(screen.queryByRole("button")).toBeNull();
  });
});
