import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DataPrepareFormulaBar } from "./DataPrepareFormulaBar";

afterEach(cleanup);

describe("DataPrepareFormulaBar M", () => {
  it("não interpreta M no browser; Enter envia texto e Escape descarta", () => {
    const apply = vi.fn();
    render(
      <DataPrepareFormulaBar
        stepName="Filtrado"
        formula="Table.SelectRows(Fonte, each [oee] > 80)"
        diagnostics={[]}
        onApply={apply}
      />,
    );
    const input = screen.getByRole("textbox", { name: "Expressão M da etapa" });
    fireEvent.change(input, { target: { value: "Table.Skip(Fonte, 2)" } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(apply).toHaveBeenCalledWith("Table.Skip(Fonte, 2)");
    fireEvent.change(input, { target: { value: "inválida" } });
    fireEvent.keyDown(input, { key: "Escape" });
    expect((input as HTMLInputElement).value).toBe(
      "Table.SelectRows(Fonte, each [oee] > 80)",
    );
  });

  it("expõe diagnóstico com código, linha e coluna", () => {
    render(
      <DataPrepareFormulaBar
        stepName="X"
        formula="?"
        diagnostics={[
          {
            code: "m.syntax",
            severity: "error",
            message: "Expressão inválida.",
            range: {
              startLine: 3,
              startColumn: 7,
              endLine: 3,
              endColumn: 8,
              startOffset: 20,
              endOffset: 21,
            },
          },
        ]}
        onApply={() => undefined}
      />,
    );
    expect(screen.getByRole("alert").textContent).toContain(
      "m.syntax — linha 3, coluna 7",
    );
    expect(
      screen.getByRole("textbox", { name: "Expressão M da etapa" }).getAttribute(
        "aria-invalid",
      ),
    ).toBe("true");
  });
});
