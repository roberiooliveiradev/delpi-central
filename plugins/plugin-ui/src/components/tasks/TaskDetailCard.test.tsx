import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { TaskCardList } from "./TaskCardList";
import { TaskDetailCard } from "./TaskDetailCard";
import type { TaskItemPresentation } from "./taskPresentation";

afterEach(() => {
  cleanup();
});

const manual: TaskItemPresentation = {
  id: "task:1",
  title: "Validar fluxo",
  description: "Revisar o fluxo de aprovação completo.",
  sourceLabel: "Tarefa",
  statusLabel: "Pendente",
  statusTone: "info",
  assigneeLabel: "Maria",
  dueDateLabel: "25/09/2026",
  contextLabel: "PROC-001",
  actions: { canEdit: true, canComplete: true, canCancel: true },
};

const signature: TaskItemPresentation = {
  id: "meeting_minute_signature:ata-1",
  title: "Assinar ata",
  sourceLabel: "Ata",
  statusLabel: "Pendente",
  actions: { canOpen: true },
};

const overdue: TaskItemPresentation = {
  ...manual,
  id: "task:2",
  overdue: true,
};

const completed: TaskItemPresentation = {
  ...manual,
  id: "task:3",
  statusLabel: "Concluída",
  statusTone: "success",
};

describe("TaskDetailCard", () => {
  it("renderiza título, descrição, status e campos padrão", () => {
    render(<TaskDetailCard item={manual} />);
    expect(screen.getByText("Validar fluxo")).toBeTruthy();
    expect(screen.getByText("Revisar o fluxo de aprovação completo.")).toBeTruthy();
    expect(screen.getByText("Pendente")).toBeTruthy();
    expect(screen.getByText("Prazo")).toBeTruthy();
    expect(screen.getByText("25/09/2026")).toBeTruthy();
    expect(screen.getByText("Responsável")).toBeTruthy();
    expect(screen.getByText("Maria")).toBeTruthy();
    expect(screen.getByText("Origem")).toBeTruthy();
    expect(screen.getByText("Contexto")).toBeTruthy();
    expect(screen.getByText("PROC-001")).toBeTruthy();
  });

  it("aciona callbacks conforme flags do descriptor", () => {
    const onEdit = vi.fn();
    const onComplete = vi.fn();
    const onCancel = vi.fn();
    render(
      <TaskDetailCard
        item={manual}
        onEdit={onEdit}
        onComplete={onComplete}
        onCancel={onCancel}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Editar" }));
    fireEvent.click(screen.getByRole("button", { name: "Concluir" }));
    fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(onEdit).toHaveBeenCalledWith(manual);
    expect(onComplete).toHaveBeenCalledWith(manual);
    expect(onCancel).toHaveBeenCalledWith(manual);
  });

  it("assinatura mostra Abrir sem ações manuais", () => {
    const onOpen = vi.fn();
    render(<TaskDetailCard item={signature} onOpen={onOpen} />);
    fireEvent.click(screen.getByRole("button", { name: "Abrir" }));
    expect(onOpen).toHaveBeenCalledWith(signature);
    expect(screen.queryByRole("button", { name: "Editar" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Concluir" })).toBeNull();
  });

  it("vencida usa variante danger no badge", () => {
    const { container } = render(<TaskDetailCard item={overdue} />);
    const badge = container.querySelector(".delpi-ui-status-badge--danger");
    expect(badge).toBeTruthy();
    expect(badge?.textContent).toContain("vencida");
  });

  it("concluída em readOnly não mostra ações", () => {
    render(
      <TaskDetailCard item={completed} readOnly onEdit={vi.fn()} onComplete={vi.fn()} />,
    );
    expect(screen.queryByRole("button")).toBeNull();
    expect(screen.getByText("Concluída")).toBeTruthy();
  });

  it("omite descrição ausente sem quebrar", () => {
    render(<TaskDetailCard item={signature} />);
    expect(screen.getByText("Assinar ata")).toBeTruthy();
  });

  it("aceita campos extras e corpo customizado", () => {
    render(
      <TaskDetailCard
        item={manual}
        fields={[{ label: "Prioridade", value: "Alta" }]}
        description={<div data-testid="custom-body">markdown</div>}
      />,
    );
    expect(screen.getByText("Prioridade")).toBeTruthy();
    expect(screen.getByTestId("custom-body")).toBeTruthy();
    // custom description substitui o texto simples
    expect(screen.queryByText("Revisar o fluxo de aprovação completo.")).toBeNull();
  });

  it("includeDefaultFields=false usa apenas os campos do portal", () => {
    render(
      <TaskDetailCard
        item={manual}
        includeDefaultFields={false}
        fields={[{ label: "Prioridade", value: "Alta" }]}
      />,
    );
    expect(screen.getByText("Prioridade")).toBeTruthy();
    expect(screen.queryByText("Responsável")).toBeNull();
  });

  it("prefixo de classe mantém classes do portal e do kit", () => {
    const { container } = render(
      <TaskDetailCard item={manual} classNamePrefix="cm" />,
    );
    expect(container.querySelector(".cm-task-detail-card")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-task-detail-card")).toBeTruthy();
    expect(container.querySelector(".cm-status-badge")).toBeTruthy();
  });
});

describe("TaskCardList", () => {
  it("renderiza lista semântica acessível", () => {
    render(
      <TaskCardList>
        <TaskDetailCard item={manual} />
        <TaskDetailCard item={signature} />
      </TaskCardList>,
    );
    const list = screen.getByRole("list");
    expect(list).toBeTruthy();
    expect(screen.getByText("Validar fluxo")).toBeTruthy();
    expect(screen.getByText("Assinar ata")).toBeTruthy();
  });
});
