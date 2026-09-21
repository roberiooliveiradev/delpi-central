import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const dir = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(join(dir, "MyTasksPage.tsx"), "utf8");

describe("MyTasksPage", () => {
  it("usa o chrome compartilhado da fila, sem busca no hero nem store local", () => {
    expect(source).toMatch(/TaskWorklistSection/);
    expect(source).toMatch(/TaskSearchField/);
    expect(source).toMatch(/TaskEmptyState/);
    expect(source).toMatch(/TaskEditorFrame/);
    expect(source).toMatch(/TaskItemsTable/);
    expect(source).toMatch(/Buscar tarefas/);
    expect(source).toMatch(/Nenhuma tarefa pendente no momento/);
    expect(source).not.toMatch(/Buscar na lista/);
    expect(source).not.toMatch(/from ["']@delpi\/commercial/);
    expect(source).not.toMatch(/INSERT INTO/);
    expect(source).not.toMatch(/pendingAtas/);
  });
});
