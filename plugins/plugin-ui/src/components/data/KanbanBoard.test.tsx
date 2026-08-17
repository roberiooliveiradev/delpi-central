import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { KanbanBoard, kanbanBoardBemClasses } from "./KanbanBoard";

afterEach(() => {
  cleanup();
});

describe("KanbanBoard", () => {
  it("renderiza colunas e dual-class delpi-ui", () => {
    const classNames = kanbanBoardBemClasses("cm");
    const { container } = render(
      <KanbanBoard
        classNames={classNames}
        ariaLabel="Board demo"
        columns={[
          {
            id: "upcoming",
            title: "Próximos",
            count: 2,
            empty: "Nenhum próximo",
          },
          {
            id: "ready_to_invoice",
            title: "Pronto",
            count: 1,
            children: <div className={classNames.card}>Card A</div>,
          },
        ]}
      />,
    );

    expect(screen.getByLabelText("Board demo")).toBeTruthy();
    expect(screen.getByText("Próximos")).toBeTruthy();
    expect(screen.getByText("Nenhum próximo")).toBeTruthy();
    expect(screen.getByText("Card A")).toBeTruthy();
    expect(container.querySelector(".cm-kanban-board")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-kanban-board")).toBeTruthy();
    expect(container.querySelector('[data-kanban-column="ready_to_invoice"]')).toBeTruthy();
  });
});
