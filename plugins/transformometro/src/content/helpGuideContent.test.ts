import { describe, expect, it } from "vitest";

import type { ProductGuideHelpTopic } from "../data/api/transformometroProductGuideApi";
import {
  HELP_LOADING_NOTE,
  HELP_SECTION_TOPICS,
  HELP_UNAVAILABLE_NOTE,
  indexTopicsById,
  mergeManualWithGuides,
} from "./helpGuideContent";
import { USER_MANUAL_CONTENT } from "./userManualContent";

const tasksGuide: ProductGuideHelpTopic = {
  id: "tasks",
  title: "Minhas tarefas",
  summary: "Tarefas são pendências atribuídas a pessoas.",
  purpose: "Acompanhar o que falta fazer.",
  use_when: ["Quando há trabalho atribuído."],
  how_to_use: ["Abra Minhas tarefas.", "Use Nova tarefa para criar."],
  quality_rules: ["Tarefa sem responsável não aparece na fila certa."],
  common_mistakes: ["Confundir tarefa com ata."],
  related_topics: ["meeting_minutes", "interaction_room"],
};

const branchGuide: ProductGuideHelpTopic = {
  id: "branch",
  title: "Unidades (filiais)",
  summary: "Unidades são as filiais da organização.",
};

const topics = indexTopicsById([tasksGuide, branchGuide]);

describe("helpGuideContent — projeção do Product Guide no Portal", () => {
  it("mapeia seções do manual para topics do registry", () => {
    expect(HELP_SECTION_TOPICS["my-tasks"]).toEqual(["tasks"]);
    expect(HELP_SECTION_TOPICS.interaction).toEqual(["interaction_room"]);
    expect(HELP_SECTION_TOPICS["revision-diagnostic"]).toEqual(["diagnostic"]);
    expect(HELP_SECTION_TOPICS.settings).toEqual(["branch", "department", "shared_resources"]);
  });

  it("deriva intro e bullets do guide, preservando links locais", () => {
    const merged = mergeManualWithGuides(USER_MANUAL_CONTENT.sections, topics);
    const tasks = merged.find((s) => s.id === "my-tasks")!;
    expect(tasks.intro).toContain("Tarefas são pendências atribuídas a pessoas.");
    expect(tasks.bullets).toEqual([
      "Abra Minhas tarefas.",
      "Use Nova tarefa para criar.",
      "Tarefa sem responsável não aparece na fila certa.",
    ]);
    // links (navegação) nunca são substituídos
    expect(tasks.links?.length).toBeGreaterThan(0);
  });

  it("não vaza campos internos — o help view já vem filtrado do backend", () => {
    const merged = mergeManualWithGuides(USER_MANUAL_CONTENT.sections, topics);
    const text = JSON.stringify(merged);
    for (const internal of ["capability_refs", "contract_refs", "source_refs", "agent_guidance"]) {
      expect(text).not.toContain(internal);
    }
  });

  it("preserva bullets UI-specific locais depois dos derivados", () => {
    const merged = mergeManualWithGuides(USER_MANUAL_CONTENT.sections, topics);
    const home = merged.find((s) => s.id === "home")!;
    expect(home.bullets?.some((b) => /Favoritos/.test(b))).toBe(true);
  });

  it("renderiza estado de loading controlado", () => {
    const merged = mergeManualWithGuides(USER_MANUAL_CONTENT.sections, null, { loading: true });
    const tasks = merged.find((s) => s.id === "my-tasks")!;
    expect(tasks.intro).toBe(HELP_LOADING_NOTE);
    const teo = merged.find((s) => s.id === "teo")!;
    expect(teo.intro).toMatch(/ChatGPT/); // não mapeada passa intacta
  });

  it("renderiza estado de indisponibilidade sem quebrar navegação", () => {
    const merged = mergeManualWithGuides(USER_MANUAL_CONTENT.sections, null);
    const tasks = merged.find((s) => s.id === "my-tasks")!;
    expect(tasks.intro).toBe(HELP_UNAVAILABLE_NOTE);
    expect(tasks.links?.length).toBeGreaterThan(0); // navegação continua
    // seções não mapeadas permanecem intactas
    const admin = merged.find((s) => s.id === "administration")!;
    expect(admin.intro).toMatch(/Administração/);
  });

  it("seções multi-topic projetam resumo de cada guide", () => {
    const merged = mergeManualWithGuides(USER_MANUAL_CONTENT.sections, topics);
    const settings = merged.find((s) => s.id === "settings")!;
    // branch resolve, department/shared_resources ausentes do stub — ainda projeta
    expect(settings.bullets?.some((b) => /Unidades/.test(b))).toBe(true);
  });
});
