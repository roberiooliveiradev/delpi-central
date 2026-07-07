import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { TablePaginationNav, tablePaginationNavBemClasses } from "./TablePaginationNav";

describe("TablePaginationNav", () => {
  it("renderiza navegação prev/info/next", () => {
    render(
      <TablePaginationNav
        page={2}
        pageSize={10}
        total={25}
        onPageChange={vi.fn()}
        classNames={tablePaginationNavBemClasses("dm")}
        labels={{
          previous: "Anterior",
          next: "Próxima",
          navigationAriaLabel: "Paginação",
          infoBeforeCurrent: "Página ",
          infoAfterCurrent: (totalPages) => ` de ${totalPages}`,
        }}
      />,
    );

    expect(screen.getByRole("navigation", { name: "Paginação" })).toBeTruthy();
    expect(screen.getByText("2")).toBeTruthy();
    expect(screen.getByText(/ de 3/)).toBeTruthy();
  });
});
