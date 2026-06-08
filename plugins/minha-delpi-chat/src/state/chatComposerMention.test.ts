import { describe, expect, it } from "vitest";

import {
  applyComposerMentionSelection,
  detectActiveComposerMention,
  filterComposerMentionCandidates,
  formatComposerMentionToken,
  listComposerMentionCandidates,
  mergeMentionedContextIds,
  resolveMentionedContextIds,
} from "./chatComposerMention";

const candidates = listComposerMentionCandidates({
  agents: [{ id: "agent-a", name: "Agente Minha DELPI" }],
  projects: [
    { id: "project-a", name: "novo" },
    { id: "project-b", name: "outro" },
  ],
});

describe("chatComposerMention", () => {
  it("detecta menção ativa com @query", () => {
    const value = "listar @age";

    expect(detectActiveComposerMention(value, value.length)).toEqual({
      start: 7,
      query: "age",
    });
  });

  it("detecta menção ativa dentro de colchetes", () => {
    const value = "pergunta @[Agent";

    expect(detectActiveComposerMention(value, value.length)).toEqual({
      start: 9,
      query: "Agent",
    });
  });

  it("filtra candidatos por query", () => {
    expect(filterComposerMentionCandidates(candidates, "delpi").map((item) => item.name)).toEqual([
      "Agente Minha DELPI",
    ]);
  });

  it("insere token @[Nome] ao selecionar", () => {
    const result = applyComposerMentionSelection({
      value: "consulta @de",
      cursor: 12,
      mentionStart: 9,
      candidate: candidates[0],
    });

    expect(result.value).toBe("consulta @[Agente Minha DELPI] ");
    expect(result.cursor).toBe(result.value.length);
    expect(formatComposerMentionToken("Agente Minha DELPI")).toBe("@[Agente Minha DELPI] ");
  });

  it("resolve ids citados no texto", () => {
    expect(
      resolveMentionedContextIds(
        "@[Agente Minha DELPI] listar LMPs em @[novo]",
        candidates,
      ),
    ).toEqual({
      agentIds: ["agent-a"],
      projectIds: ["project-a"],
    });
  });

  it("combina menções com overlay do composer", () => {
    expect(
      mergeMentionedContextIds({
        overlayAgentIds: ["agent-overlay"],
        mentionAgentIds: ["agent-a"],
        overlayProjectIds: ["project-overlay"],
        mentionProjectIds: ["project-b"],
      }),
    ).toEqual({
      agentIds: ["agent-overlay", "agent-a"],
      projectIds: ["project-overlay", "project-b"],
    });
  });
});
