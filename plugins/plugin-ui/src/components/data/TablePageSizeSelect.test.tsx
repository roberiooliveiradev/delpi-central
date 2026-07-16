import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { TablePageSizeSelect, paginationBemClasses } from "./Pagination";
import { TABLE_PAGE_SIZE_OPTIONS } from "../../utils/paginationPages";

const classNames = paginationBemClasses("test").tablePageSize;

afterEach(() => {
  cleanup();
});

describe("TablePageSizeSelect", () => {
  it("usa SelectControl do kit em vez de <select> nativo", () => {
    const onChange = vi.fn();
    const { container } = render(
      <TablePageSizeSelect
        pageSize={20}
        pageSizeOptions={TABLE_PAGE_SIZE_OPTIONS}
        onPageSizeChange={onChange}
        classNames={classNames}
        labels={{ label: "Itens por página", selectAriaLabel: "Quantidade de itens por página" }}
      />,
    );

    expect(container.querySelector("select")).toBeNull();
    expect(container.querySelector(".delpi-ui-toolbar-select")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Quantidade de itens por página" })).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Quantidade de itens por página" }));
    fireEvent.click(screen.getByRole("button", { name: "50" }));
    expect(onChange).toHaveBeenCalledWith(50);
  });
});
