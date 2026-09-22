import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { Pagination, paginationBemClasses } from "./Pagination";

afterEach(() => {
  cleanup();
});

describe("Pagination", () => {
  const classNames = paginationBemClasses("ie").pagination;
  const labels = {
    navigationAriaLabel: "Paginação",
    pagesAriaLabel: "Páginas",
    previous: "Anterior",
    next: "Próxima",
    info: ({
      rangeStart,
      rangeEnd,
      total,
      page,
      totalPages,
    }: {
      rangeStart: number;
      rangeEnd: number;
      total: number;
      page: number;
      totalPages: number;
    }) => `Exibindo ${rangeStart}–${rangeEnd} de ${total} · Página ${page} de ${totalPages}`,
    jumpLabel: "Ir para",
    jumpInputAriaLabel: "Ir para página",
    jumpError: () => "Página inválida.",
  };

  it("renderiza setas com aria-label e mantém páginas / Ir para", () => {
    render(
      <Pagination
        page={1}
        pageSize={20}
        total={26}
        onPageChange={vi.fn()}
        classNames={classNames}
        labels={labels}
      />,
    );

    const previous = screen.getByRole("button", { name: "Anterior" });
    const next = screen.getByRole("button", { name: "Próxima" });
    expect(previous.querySelector("svg")).toBeTruthy();
    expect(next.querySelector("svg")).toBeTruthy();
    expect(previous.textContent?.trim()).toBe("");
    expect(screen.getByRole("button", { name: "1" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "2" })).toBeTruthy();
    expect(screen.getByLabelText("Ir para página")).toBeTruthy();
    expect(screen.getByText("Exibindo 1–20 de 26 · Página 1 de 2")).toBeTruthy();
  });
});
