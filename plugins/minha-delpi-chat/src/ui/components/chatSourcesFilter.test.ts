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
        agentId: "b185b233-b06a-4d23-8450-6ac3c0f7428d",
      }),
    ).toBe(true);
  });

  it("mantém fontes do projeto e da sessão visíveis", () => {
    const sources: ChatSource[] = [
      { scope: "global", title: "Base global" },
      {
        scope: "agent_source",
        title: "Manual do agente",
        agentId: "b185b233-b06a-4d23-8450-6ac3c0f7428d",
      },
      { scope: "project_source", title: "Briefing", projectId: "p1" },
      { scope: "session_source", title: "Anexo", sessionId: "s1" },
    ];

    expect(filterVisibleChatSources(sources)).toEqual([
      { scope: "project_source", title: "Briefing", projectId: "p1" },
      { scope: "session_source", title: "Anexo", sessionId: "s1" },
    ]);
  });

  it("mantém fontes web_search visíveis", () => {
    const sources: ChatSource[] = [
      {
        scope: "web_search",
        title: "Tyco International",
        sourceRef: "https://pt.wikipedia.org/wiki/Tyco_International",
        sourceType: "web",
      },
    ];

    expect(filterVisibleChatSources(sources)).toEqual(sources);
  });
});
