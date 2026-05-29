import { describe, expect, it } from "vitest";

import type { ChatSource } from "../../data/api/chatTypes";

import { filterVisibleChatSources, isGeneralChatSource } from "./chatSourcesFilter";

describe("chatSourcesFilter", () => {
  it("trata fontes da base global como gerais", () => {
    expect(
      isGeneralChatSource({
        scope: "global",
        title: "Política",
      }),
    ).toBe(true);

    expect(
      isGeneralChatSource({
        sourceType: "admin_upload",
        title: "Documento corporativo",
      }),
    ).toBe(true);
  });

  it("oculta fontes globais e memória do agente", () => {
    expect(
      isGeneralChatSource({
        scope: "agent_source",
        title: "Manual do agente",
        agentKey: "rh",
      }),
    ).toBe(true);
  });

  it("mantém fontes do projeto e da sessão visíveis", () => {
    const sources: ChatSource[] = [
      { scope: "global", title: "Base global" },
      { scope: "agent_source", title: "Manual do agente", agentKey: "rh" },
      { scope: "project_source", title: "Briefing", projectId: "p1" },
      { scope: "session_source", title: "Anexo", sessionId: "s1" },
    ];

    expect(filterVisibleChatSources(sources)).toEqual([
      { scope: "project_source", title: "Briefing", projectId: "p1" },
      { scope: "session_source", title: "Anexo", sessionId: "s1" },
    ]);
  });
});
