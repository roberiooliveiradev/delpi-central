import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { TaskItemsTable } from "./TaskItemsTable";
import type { TaskItemPresentation } from "./taskPresentation";

afterEach(() => {
  cleanup();
});

const manual: TaskItemPresentation = {
  id: "task:1",
  title: "Validar fluxo",
  sourceLabel: "Tarefa",
  statusLabel: "Pendente",
  dueDateLabel: "25/09/2026",
  actions: { canEdit: true, canComplete: true, canCancel: true },
};

const signature: TaskItemPresentation = {
  id: "meeting_minute_signature:ata-1",
  title: "Assinar ata",
  sourceLabel: "Ata",
  statusLabel: "Pendente",
  actions: { canOpen: true },
};

describe("TaskItemsTable", () => {
  it("mantém as ações conforme o descriptor, sem regra de domínio", () => {
    const onOpen = vi.fn();
    const onComplete = vi.fn();
    render(
      <TaskItemsTable
        items={[manual, signature]}
        onOpen={onOpen}
        onComplete={onComplete}
      />,
    );
    expect(screen.getByText("Validar fluxo")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Abrir" }));
    expect(onOpen).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole("button", { name: "Concluir" }));
    expect(onComplete).toHaveBeenCalledTimes(1);
    expect(screen.queryAllByRole("button", { name: "Abrir" })).toHaveLength(1);
  });

  it("mostra empty state acessível", () => {
    render(<TaskItemsTable items={[]} />);
    expect(screen.getByText("Nenhuma tarefa pendente no momento.")).toBeTruthy();
  });
});
