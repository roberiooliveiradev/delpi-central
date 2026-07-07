import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { TableHeaderCell, tableHeaderCellPacClasses } from "./TableHeaderCell";

afterEach(() => {
  cleanup();
});

describe("TableHeaderCell", () => {
  it("renderiza th com label simples", () => {
    render(
      <table>
        <thead>
          <tr>
            <TableHeaderCell label="Código" classNames={tableHeaderCellPacClasses("pac")} />
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
            />
          </tr>
        </thead>
      </table>,
    );

    expect(container.querySelector(".pac-field__label-row")).toBeTruthy();
    expect(screen.getByText("Status")).toBeTruthy();
  });
});
