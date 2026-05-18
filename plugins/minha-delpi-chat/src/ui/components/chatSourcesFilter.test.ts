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
  });

  it("mantém fontes de agente, projeto e sessão visíveis", () => {
    const sources: ChatSource[] = [
      { scope: "global", title: "Base global" },
      { scope: "agent_source", title: "Manual do agente" },
      { scope: "project_source", title: "Briefing" },
      { scope: "session_source", title: "Anexo" },
    ];

    expect(filterVisibleChatSources(sources)).toEqual([
      { scope: "agent_source", title: "Manual do agente" },
      { scope: "project_source", title: "Briefing" },
      { scope: "session_source", title: "Anexo" },
    ]);
  });
});
