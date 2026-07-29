import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { TableColumnsMultiSelect } from "./TableColumnsMultiSelect";

afterEach(() => {
  cleanup();
});

describe("TableColumnsMultiSelect selection", () => {
  it("checkbox só altera visibilidade; clique no texto seleciona a coluna", () => {
    const onChange = vi.fn();
    const onSelectColumn = vi.fn();
    render(
      <TableColumnsMultiSelect
        idPrefix="td-col"
        options={[
          { key: "a", label: "Produto" },
          { key: "b", label: "Qtd" },
        ]}
        onChange={onChange}
        onSelectColumn={onSelectColumn}
      />,
    );

    fireEvent.click(screen.getByRole("checkbox", { name: /Exibir coluna Produto/i }));
    expect(onChange).toHaveBeenCalled();
    expect(onSelectColumn).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Produto" }));
    expect(onSelectColumn).toHaveBeenCalledWith("a");
  });
});
