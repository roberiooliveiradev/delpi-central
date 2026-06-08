import { describe, expect, it } from "vitest";

import {
  isExplicitChatAgentActive,
  resolveChatModePresentation,
  resolveExplicitChatAgentId,
} from "./chatAgentActivation";

describe("chatAgentActivation", () => {
  it("prioriza rota de agente sobre contexto do composer", () => {
    expect(
      resolveExplicitChatAgentId({
        activeAgentPageId: "agent-route",
        contextAgentId: "agent-context",
      }),
    ).toBe("agent-route");
  });

  it("retorna null quando nenhum agente foi escolhido", () => {
    expect(resolveExplicitChatAgentId({})).toBeNull();
    expect(isExplicitChatAgentActive(null)).toBe(false);
  });

  it("diferencia chat comum de agente ativo nos rótulos", () => {
    expect(
      resolveChatModePresentation({
        explicitAgentActive: false,
        projectName: null,
        agentName: null,
      }),
    ).toEqual({
      mode: "common",
      label: "Minha DELPI Chat",
      subtitle: "Chat comum (sem agente)",
    });

    expect(
      resolveChatModePresentation({
        explicitAgentActive: true,
        agentName: "Agente Minha DELPI",
        projectName: "Qualidade",
      }),
    ).toEqual({
      mode: "agent",
      label: "Agente Minha DELPI",
      subtitle: "Projeto Qualidade · agente ativo",
    });
  });
});
