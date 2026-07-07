import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import {
  ReadOnlyField,
  readOnlyFieldKaizenBemClasses,
  readOnlyFieldPacBemClasses,
} from "./ReadOnlyField";

const LABELS = {
  emptyDisplay: "—",
  fieldHelpAriaLabel: (label: string) => `Ajuda: ${label}`,
};

afterEach(() => {
  cleanup();
});

describe("ReadOnlyField", () => {
  it("renderiza valor kaizen com hint", () => {
    render(
      <ReadOnlyField
        label="Setor"
        hint="Setor responsável"
        value="Produção"
        classNames={readOnlyFieldKaizenBemClasses("kz")}
        labels={LABELS}
      />,
    );

    expect(screen.getByText("Setor")).toBeTruthy();
    expect(screen.getByText("Produção")).toBeTruthy();
    expect(screen.getByLabelText("Ajuda: Setor")).toBeTruthy();
  });

  it("exibe traço quando valor vazio (kaizen)", () => {
    render(
      <ReadOnlyField
        label="Observação"
        value=""
        classNames={readOnlyFieldKaizenBemClasses("kz")}
        labels={LABELS}
      />,
    );

    expect(screen.getByText("—")).toBeTruthy();
  });

  it("renderiza aparência ficha PAC com FieldLabel", () => {
    render(
      <ReadOnlyField
        label="Cliente"
        value="ACME"
        appearance="ficha"
        labelMode="fieldLabel"
        classNames={readOnlyFieldPacBemClasses("pac")}
        labels={LABELS}
      />,
    );

    expect(screen.getByText("Cliente")).toBeTruthy();
    expect(screen.getByText("ACME")).toBeTruthy();
  });

  it("aplica classe muted para vazio no PAC", () => {
    const { container } = render(
      <ReadOnlyField
        label="Loja"
        value={null}
        appearance="ficha"
        labelMode="fieldLabel"
        classNames={readOnlyFieldPacBemClasses("pac")}
        labels={LABELS}
      />,
    );

    expect(container.querySelector(".pac-muted")).toBeTruthy();
  });
});
