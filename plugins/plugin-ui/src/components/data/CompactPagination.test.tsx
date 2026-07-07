import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CompactPagination, compactPaginationBemClasses } from "./CompactPagination";

afterEach(() => {
  cleanup();
});

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

  it("layout grouped renderiza seletor de página quando configurado", () => {
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

  it("layout flat omite seletor de tamanho de página", () => {
    render(
      <CompactPagination
        page={1}
        pageSize={20}
        total={50}
        onPageChange={vi.fn()}
        layout="flat"
        classNames={classNames}
        labels={{
          info: ({ page, totalPages, total }) =>
            `Página ${page} de ${totalPages} · ${total} registro(s)`,
          previous: "Anterior",
          next: "Próxima",
          navigationAriaLabel: "Paginação",
        }}
      />,
    );

    expect(screen.queryByRole("combobox")).toBeNull();
    expect(screen.getByText("Página 1 de 3 · 50 registro(s)")).toBeTruthy();
  });
});
