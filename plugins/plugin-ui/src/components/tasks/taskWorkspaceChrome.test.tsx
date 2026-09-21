import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { TaskEmptyState } from "./TaskEmptyState";
import { TaskSearchField } from "./TaskSearchField";
import { TaskWorklistSection } from "./TaskWorklistSection";

const css = readFileSync(join(dirname(fileURLToPath(import.meta.url)), "../../styles/task-workspace.css"), "utf8");

afterEach(() => {
  cleanup();
});

describe("shared task worklist chrome", () => {
  it("coloca busca e ações na seção, sem filtrar", () => {
    render(
      <TaskWorklistSection
        title="Fila"
        actions={<button type="button">Nova tarefa</button>}
        search={<TaskSearchField value="" onChange={() => undefined} />}
      >
        <p>conteúdo</p>
      </TaskWorklistSection>,
    );
    expect(screen.getByRole("heading", { name: "Fila" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Nova tarefa" })).toBeTruthy();
    expect(screen.getByRole("searchbox", { name: "Buscar tarefas" })).toBeTruthy();
    expect(screen.getByText("conteúdo")).toBeTruthy();
  });

  it("limpa a busca com Escape sem consultar API", () => {
    const onChange = vi.fn();
    render(<TaskSearchField value="ata" onChange={onChange} />);
    fireEvent.keyDown(screen.getByRole("searchbox"), { key: "Escape" });
    expect(onChange).toHaveBeenCalledWith("");
  });

  it("mostra empty com título e CTA no mesmo chrome", () => {
    render(
      <TaskEmptyState title="Nenhuma em atrasadas" message="A fila deste recorte está vazia.">
        <button type="button">Nova tarefa</button>
      </TaskEmptyState>,
    );
    expect(screen.getByRole("heading", { name: "Nenhuma em atrasadas" })).toBeTruthy();
    expect(screen.getByText("A fila deste recorte está vazia.")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Nova tarefa" }).closest(".delpi-ui-task-empty__action")).toBeTruthy();
  });

  it("mantém o rodapé do editor em altura de conteúdo no CSS compartilhado", () => {
    expect(css).toContain("display: flex;");
    expect(css).toContain("flex-direction: column;");
    expect(css).toContain("height: auto;");
    expect(css).toContain("min-height: 44px;");
    expect(css).not.toContain("height: 40px !important");
  });
});
