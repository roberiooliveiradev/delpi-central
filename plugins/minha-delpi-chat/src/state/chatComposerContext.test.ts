import { describe, expect, it } from "vitest";

import {
  buildComposerTurnPayload,
  buildTurnContextMetadata,
  formatComposerPlaceholderParts,
  resolveUserMessageTurnContextChips,
  MAX_COMPOSER_AGENTS,
  MAX_COMPOSER_PROJECTS,
  resolveComposerContextBarFromLists,
  resolveEffectiveAgentIds,
  resolveEffectiveProjectIds,
  toggleContextId,
} from "./chatComposerContext";

describe("chatComposerContext", () => {
  it("alterna projetos sem duplicar até o limite", () => {
    let ids = toggleContextId([], "p1", MAX_COMPOSER_PROJECTS);
    ids = toggleContextId(ids, "p2", MAX_COMPOSER_PROJECTS);

    expect(ids).toEqual(["p1", "p2"]);

    ids = toggleContextId(ids, "p1", MAX_COMPOSER_PROJECTS);

    expect(ids).toEqual(["p2"]);
  });

  it("inclui agente persistido na sessão quando não há página dedicada", () => {
    expect(
      resolveEffectiveAgentIds({
        sessionAgentId: "session-agent",
        contextAgentIds: ["overlay-agent"],
      }),
    ).toEqual(["session-agent", "overlay-agent"]);
  });

  it("monta payload explícito com chatMode agent", () => {
    expect(
      buildComposerTurnPayload({
        effectiveAgentIds: ["agent-a"],
        effectiveProjectIds: ["project-a", "project-b"],
      }),
    ).toEqual({
      agentId: "agent-a",
      agentIds: ["agent-a"],
      projectId: "project-a",
      projectIds: ["project-a", "project-b"],
      chatMode: "agent",
    });
  });

  it("combina página e overlays em ids efetivos", () => {
    expect(
      resolveEffectiveProjectIds({
        pageProjectId: "page",
        contextProjectIds: ["ctx-a", "ctx-b"],
      }),
    ).toEqual(["page", "ctx-a", "ctx-b"]);

    expect(
      resolveEffectiveAgentIds({
        pageAgentId: null,
        contextAgentIds: ["agent-a", "agent-b"],
      }),
    ).toEqual(["agent-a", "agent-b"]);
  });

  it("exibe chips para cada overlay distinto da página", () => {
    expect(
      resolveComposerContextBarFromLists({
        contextAgentIds: ["agent-a"],
        contextProjectIds: ["project-b", "project-c"],
      }),
    ).toEqual([
      { kind: "agent", id: "agent-a" },
      { kind: "project", id: "project-b" },
      { kind: "project", id: "project-c" },
    ]);
  });

  it("resolve chips de contexto no card da pergunta", () => {
    expect(
      resolveUserMessageTurnContextChips(
        buildTurnContextMetadata({
          agents: [
            { id: "agent-a", name: "Agente Minha DELPI" },
            { id: "agent-b", name: "Agente B" },
          ],
          projects: [{ id: "project-a", name: "novo" }],
        }),
      ),
    ).toEqual([
      { kind: "agent", id: "agent-a", name: "Agente Minha DELPI" },
      { kind: "agent", id: "agent-b", name: "Agente B" },
      { kind: "project", id: "project-a", name: "novo" },
    ]);
  });

  it("formata placeholder para múltiplos projetos e agentes", () => {
    expect(
      formatComposerPlaceholderParts({
        projectNames: ["novo", "teste 2"],
        agentNames: ["Agente Minha DELPI"],
      }),
    ).toBe("Pergunte sobre 2 projetos com Agente Minha DELPI");
  });
});
