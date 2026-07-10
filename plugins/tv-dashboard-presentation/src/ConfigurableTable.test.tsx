import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { ConfigurableTable } from "./ConfigurableTable";
import { mergeComunicadoTableOptions } from "./comunicadoTableOptions";

afterEach(() => {
  cleanup();
});

describe("ConfigurableTable", () => {
  const columns = [
    { key: "name", label: "Produto" },
    { key: "value", label: "Valor" },
  ];

  it("renderiza cabeçalho e células", () => {
    render(
      <ConfigurableTable
        columns={columns}
        rows={[
          { name: "Item A", value: 1200 },
          { name: "Item B", value: 3400 },
        ]}
      />,
    );
    expect(screen.getByText("Produto")).toBeTruthy();
    expect(screen.getByText("Item A")).toBeTruthy();
    expect(screen.getByRole("table")).toBeTruthy();
  });

  it("renderiza título quando habilitado", () => {
    render(
      <ConfigurableTable
        columns={columns}
        rows={[{ name: "Item A", value: 100 }]}
        options={{ showTitle: true, title: "Top produtos" }}
      />,
    );
    expect(screen.getByText("Top produtos")).toBeTruthy();
  });

  it("oculta cabeçalho quando desabilitado", () => {
    render(
      <ConfigurableTable
        columns={columns}
        rows={[{ name: "Item A", value: 100 }]}
        options={{ showHeader: false }}
      />,
    );
    expect(screen.queryByRole("columnheader")).toBeNull();
    expect(screen.getByText("Item A")).toBeTruthy();
  });

  it("mostra estado vazio sem linhas", () => {
    render(<ConfigurableTable columns={columns} rows={[]} />);
    expect(screen.getByText("Sem linhas")).toBeTruthy();
  });
});

describe("mergeComunicadoTableOptions", () => {
  it("aplica defaults do preset banded", () => {
    const merged = mergeComunicadoTableOptions(undefined, "banded");
    expect(merged.zebraStripe).toBe(true);
  });

  it("aplica defaults do preset minimal", () => {
    const merged = mergeComunicadoTableOptions(undefined, "minimal");
    expect(merged.showBorders).toBe(false);
  });
});
