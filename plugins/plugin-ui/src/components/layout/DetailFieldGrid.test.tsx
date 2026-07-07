import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import {
  DetailFieldGrid,
  detailFieldGridBemClasses,
} from "./DetailFieldGrid";

const LABELS = {
  emptyMessage: "Sem dados.",
  fieldHelpAriaLabel: (label: string) => `Ajuda: ${label}`,
};

afterEach(() => {
  cleanup();
});

describe("DetailFieldGrid", () => {
  it("renderiza campos com classes BEM", () => {
    const { container } = render(
      <DetailFieldGrid
        fields={[
          { label: "Código", value: "123" },
          { label: "Descrição", value: "Produto A", wide: true },
        ]}
        classNames={detailFieldGridBemClasses("dp")}
        labels={{ fieldHelpAriaLabel: LABELS.fieldHelpAriaLabel }}
      />,
    );

    expect(screen.getByText("Código")).toBeTruthy();
    expect(screen.getByText("123")).toBeTruthy();
    expect(container.querySelector(".dp-detail-grid__item--wide")).toBeTruthy();
  });

  it("exibe mensagem vazia quando configurada", () => {
    render(
      <DetailFieldGrid
        fields={[]}
        classNames={detailFieldGridBemClasses("dc")}
        labels={LABELS}
      />,
    );

    expect(screen.getByText("Sem dados.")).toBeTruthy();
  });

  it("aplica fallback de valor quando informado", () => {
    render(
      <DetailFieldGrid
        fields={[{ label: "Observação", value: null }]}
        classNames={detailFieldGridBemClasses("dp")}
        labels={{ fieldHelpAriaLabel: LABELS.fieldHelpAriaLabel }}
        valueFallback="—"
      />,
    );

    expect(screen.getByText("—")).toBeTruthy();
  });

  it("renderiza hint no rótulo", () => {
    render(
      <DetailFieldGrid
        fields={[{ label: "Meta", hint: "Explicação", value: "90%" }]}
        classNames={detailFieldGridBemClasses("lmps")}
        labels={LABELS}
      />,
    );

    expect(screen.getByLabelText("Ajuda: Meta")).toBeTruthy();
  });
});
