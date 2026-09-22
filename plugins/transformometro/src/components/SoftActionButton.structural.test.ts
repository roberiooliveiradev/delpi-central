import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");

describe("SoftActionButton — Process Workspace CTAs", () => {
  it("define primitive soft com tokens DS", () => {
    const soft = readFileSync(join(root, "components/SoftActionButton.tsx"), "utf8");
    const css = readFileSync(join(root, "index.css"), "utf8");
    expect(soft).toMatch(/ds-soft-btn/);
    expect(css).toMatch(/\.dashboard-transformometro \.ds-soft-btn\{/);
    expect(css).toMatch(/color-mix\(in srgb, var\(--ds-accent/);
  });

  it("Visão Geral atalhos usam SoftActionButton com ícones", () => {
    const page = readFileSync(join(root, "ui/pages/ProcessDetailPage.tsx"), "utf8");
    expect(page).toMatch(/SoftActionButton/);
    expect(page).toMatch(/icon=\{GitBranch\}/);
    expect(page).toMatch(/icon=\{FileText\}/);
    expect(page).toMatch(/icon=\{History\}/);
    expect(page).not.toMatch(/className="ds-link" onClick=\{\(\) => onNavigate\(buildProcessoSectionHref/);
  });

  it("Tarefas e Sala usam SoftActionButton", () => {
    const tasks = readFileSync(join(root, "ui/processes/ProcessRelatedTasksSection.tsx"), "utf8");
    const sala = readFileSync(join(root, "ui/processes/ProcessInteractionRoomSection.tsx"), "utf8");
    expect(tasks).toMatch(/SoftActionButton/);
    expect(tasks).toMatch(/Abrir Minhas tarefas/);
    expect(sala).toMatch(/SoftActionButton/);
    expect(sala).toMatch(/Abrir Sala de interação/);
    expect(sala).toMatch(/Ver tarefas relacionadas/);
  });

  it("EditableSectionCard Editar usa softActionBtnClass", () => {
    const card = readFileSync(join(root, "components/ui/EditableSectionCard.tsx"), "utf8");
    expect(card).toMatch(/softActionBtnClass/);
  });
});
