import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const dir = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(join(dir, "MyTasksPage.tsx"), "utf8");

describe("MyTasksPage", () => {
  it("usa o chrome compartilhado da fila, sem busca no hero nem store local", () => {
    expect(source).toMatch(/TaskWorkspacePage/);
    expect(source).toMatch(/TaskSearchField/);
    expect(source).toMatch(/TaskEmptyState/);
    expect(source).toMatch(/TaskEditorFrame/);
    expect(source).toMatch(/TaskDetailCard/);
    expect(source).toMatch(/TaskCardList/);
    expect(source).not.toMatch(/TaskItemsTable/);
    expect(source).toMatch(/Buscar tarefas/);
    expect(source).toMatch(/Nenhuma tarefa pendente no momento/);
    expect(source).not.toMatch(/Buscar na lista/);
  });

  it("expõe os contextos Recebidas e Atribuídas por mim com nomes resolvidos", () => {
    expect(source).toMatch(/Recebidas/);
    expect(source).toMatch(/Atribuídas por mim/);
    expect(source).toMatch(/useDirectoryUserLabels/);
    expect(source).toMatch(/Você não possui tarefas atribuídas a outras pessoas/);
    expect(source).toMatch(/scope/);
    expect(source).toMatch(/created_at_label/);
    expect(source).not.toMatch(/from ["']@delpi\/commercial/);
    expect(source).not.toMatch(/INSERT INTO/);
    expect(source).not.toMatch(/pendingAtas/);
  });
});
