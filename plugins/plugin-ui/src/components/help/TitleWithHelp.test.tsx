import { cleanup, render, screen } from "@testing-library/react";
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
    render(
      <TitleWithHelp
        title="Suas ações"
        hint="Fila pessoal"
        classNames={titleWithHelpPacClasses("pac")}
        labels={LABELS}
      />,
    );

    expect(screen.getByText("Suas ações")).toBeTruthy();
    expect(screen.getByLabelText("Ajuda: Suas ações")).toBeTruthy();
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
