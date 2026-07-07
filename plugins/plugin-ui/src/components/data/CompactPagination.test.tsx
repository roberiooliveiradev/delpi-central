import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { CompactPagination, compactPaginationBemClasses } from "./CompactPagination";

describe("CompactPagination", () => {
  const classNames = compactPaginationBemClasses("ie");
  const labels = {
    info: ({ page, totalPages, total }: { page: number; totalPages: number; total: number }) =>
      `Página ${page} de ${totalPages} · ${total} registro(s)`,
    pageSizeLabel: "Itens por página",
    previous: "Anterior",
    next: "Próxima",
    navigationAriaLabel: "Paginação",
  };

  it("renderiza info, seletor de página e botões", () => {
    render(
      <CompactPagination
        page={2}
        pageSize={25}
        total={100}
        totalPages={4}
        pageSizeOptions={[10, 25, 50]}
        onPageChange={vi.fn()}
        onPageSizeChange={vi.fn()}
        classNames={classNames}
        labels={labels}
      />,
    );

    expect(screen.getByText("Página 2 de 4 · 100 registro(s)")).toBeTruthy();
    expect(screen.getByText("Itens por página")).toBeTruthy();
    expect(screen.getByRole("combobox")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Anterior" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Próxima" })).toBeTruthy();
  });

  it("retorna null quando total é zero", () => {
    const { container } = render(
      <CompactPagination
        page={1}
        pageSize={25}
        total={0}
        totalPages={1}
        pageSizeOptions={[25]}
        onPageChange={vi.fn()}
        onPageSizeChange={vi.fn()}
        classNames={classNames}
        labels={labels}
      />,
    );

    expect(container.firstChild).toBeNull();
  });
});
