import { describe, expect, it } from "vitest";

import {
  isExplicitChatAgentActive,
  resolveChatModePresentation,
  resolveComposerContextBar,
  resolveEffectiveChatAgentId,
  resolveEffectiveProjectId,
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

  it("oculta barra de contexto no chat comum até o usuário escolher agente", () => {
    expect(resolveComposerContextBar({})).toEqual({ items: [] });

    expect(
      resolveComposerContextBar({
        contextAgentId: "agent-a",
      }),
    ).toEqual({
      items: [{ kind: "agent", id: "agent-a" }],
    });
  });

  it("permite combinar agente e projeto na barra de contexto", () => {
    expect(
      resolveComposerContextBar({
        contextAgentId: "agent-a",
        contextProjectId: "project-b",
      }),
    ).toEqual({
      items: [
        { kind: "agent", id: "agent-a" },
        { kind: "project", id: "project-b" },
      ],
    });
  });

  it("oculta agente da página e mostra só overrides na rota de agente", () => {
    expect(
      resolveComposerContextBar({
        pageAgentId: "agent-page",
        contextAgentId: "agent-page",
      }),
    ).toEqual({ items: [] });

    expect(
      resolveComposerContextBar({
        pageAgentId: "agent-page",
        contextAgentId: "agent-other",
        contextProjectId: "project-x",
      }),
    ).toEqual({
      items: [
        { kind: "agent", id: "agent-other" },
        { kind: "project", id: "project-x" },
      ],
    });
  });

  it("mostra agente de contexto no projeto sem repetir o projeto na barra", () => {
    expect(
      resolveComposerContextBar({
        pageProjectId: "project-a",
        contextAgentId: "agent-a",
      }),
    ).toEqual({
      items: [{ kind: "agent", id: "agent-a" }],
    });

    expect(
      resolveComposerContextBar({
        pageProjectId: "project-a",
        contextProjectId: "project-b",
      }),
    ).toEqual({
      items: [{ kind: "project", id: "project-b" }],
    });
  });

  it("prioriza overlay do composer quando difere da página", () => {
    expect(
      resolveEffectiveChatAgentId({
        pageAgentId: "agent-page",
        contextAgentId: "agent-other",
      }),
    ).toBe("agent-other");

    expect(
      resolveEffectiveProjectId({
        pageProjectId: "project-page",
        contextProjectId: "project-other",
      }),
    ).toBe("project-other");
  });
});
