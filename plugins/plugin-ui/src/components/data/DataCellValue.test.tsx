import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { DataCellValue } from "./DataCellValue";

afterEach(cleanup);

describe("DataCellValue", () => {
  it("identifica null de forma visual e acessível", () => {
    render(<DataCellValue value={null} />);
    const cell = screen.getByLabelText("Valor nulo");
    expect(cell.textContent).toBe("null");
    expect(cell.getAttribute("data-cell-kind")).toBe("null");
  });

  it("expõe mensagem do erro estruturado em tooltip", () => {
    render(<DataCellValue value={{ error: { message: "Falha no cast" } }} />);
    const cell = screen.getByLabelText("Erro: Falha no cast");
    expect(cell.textContent).toBe("error");
    expect(cell.getAttribute("title")).toBe("Falha no cast");
  });

  it("distingue propriedade ausente", () => {
    render(<DataCellValue value={undefined} present={false} />);
    expect(screen.getByLabelText("Campo ausente").textContent).toBe("ausente");
  });
});
