import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import {
  TableHeaderCell,
  TableHeaderContent,
  tableHeaderCellPacClasses,
  tableHeaderContentTransformometroClasses,
} from "./TableHeaderCell";

const LABELS = {
  hintAriaLabel: (label: string) => `Ajuda: ${label}`,
};

afterEach(() => {
  cleanup();
});

describe("TableHeaderCell", () => {
  it("renderiza th com label simples", () => {
    render(
      <table>
        <thead>
          <tr>
            <TableHeaderCell
              label="Código"
              classNames={tableHeaderCellPacClasses("pac")}
              labels={LABELS}
            />
          </tr>
        </thead>
      </table>,
    );

    const cell = screen.getByRole("columnheader", { name: "Código" });
    expect(cell.tagName).toBe("TH");
    expect(cell.getAttribute("scope")).toBe("col");
  });

  it("renderiza FieldLabel quando hint presente", () => {
    const { container } = render(
      <table>
        <thead>
          <tr>
            <TableHeaderCell
              label="Status"
              hint="Situação da ação"
              classNames={tableHeaderCellPacClasses("pac")}
              labels={LABELS}
            />
          </tr>
        </thead>
      </table>,
    );

    expect(container.querySelector(".pac-field__label-row")).toBeTruthy();
    expect(screen.getByText("Status")).toBeTruthy();
  });
});

describe("TableHeaderContent", () => {
  it("renderiza label com ícone de ajuda", () => {
    render(
      <TableHeaderContent
        label="Recurso"
        hint="Nome do recurso"
        classNames={tableHeaderContentTransformometroClasses("ds")}
        labels={LABELS}
        hintPresentation="icon"
      />,
    );

    expect(screen.getByText("Recurso")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Ajuda: Recurso" })).toBeTruthy();
    expect(document.querySelector(".ds-table__header-cell")).toBeTruthy();
  });
});
