import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { TaskEditorFrame } from "./TaskEditorFrame";

afterEach(() => {
  cleanup();
});

describe("TaskEditorFrame", () => {
  it("mostra o resumo e dispara o write só no botão primário", () => {
    const onPrimary = vi.fn();
    const onClose = vi.fn();
    render(
      <TaskEditorFrame
        title="Nova tarefa"
        primaryLabel="Criar tarefa"
        onPrimary={onPrimary}
        onClose={onClose}
        reviewRows={[
          { label: "Título", value: "Validar fluxo" },
          { label: "Responsável", value: "Eu" },
        ]}
      >
        <label>
          Título
          <input defaultValue="Validar fluxo" />
        </label>
      </TaskEditorFrame>,
    );
    expect(screen.getByText("Revise antes de gravar")).toBeTruthy();
    expect(screen.getByText("Validar fluxo")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Criar tarefa" }));
    expect(onPrimary).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(onClose).toHaveBeenCalled();
  });
});
