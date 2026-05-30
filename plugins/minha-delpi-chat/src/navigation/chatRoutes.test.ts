import { describe, expect, it } from "vitest";

import {
  buildChatAgentHref,
  buildChatAgentSessionHref,
  buildChatSessionHrefForSession,
  findAgentByRouteId,
  isChatAgentRouteId,
  normalizeAgentRouteId,
  parseChatRoute,
  withCanonicalAgentRouteId,
} from "./chatRoutes";

const AGENTS = [
  {
    id: "b185b233-b06a-4d23-8450-6ac3c0f7428d",
  },
];

describe("chatRoutes agents", () => {
  it("parseia rota de agente por uuid", () => {
    expect(
      parseChatRoute(
        "/apps/minha-delpi-chat/agentes/b185b233-b06a-4d23-8450-6ac3c0f7428d",
      ),
    ).toEqual({
      kind: "agent",
      agentId: "b185b233-b06a-4d23-8450-6ac3c0f7428d",
    });
  });

  it("parseia rota de agente com conversa", () => {
    expect(
      parseChatRoute(
        "/apps/minha-delpi-chat/agentes/b185b233-b06a-4d23-8450-6ac3c0f7428d/conversas/sessao-1",
      ),
    ).toEqual({
      kind: "agent-session",
      agentId: "b185b233-b06a-4d23-8450-6ac3c0f7428d",
      sessionId: "sessao-1",
    });
  });

  it("monta href com uuid", () => {
    expect(buildChatAgentHref("b185b233-b06a-4d23-8450-6ac3c0f7428d")).toBe(
      "/apps/minha-delpi-chat/agentes/b185b233-b06a-4d23-8450-6ac3c0f7428d",
    );
  });

  it("monta href de conversa do agente", () => {
    expect(
      buildChatAgentSessionHref(
        "b185b233-b06a-4d23-8450-6ac3c0f7428d",
        "sessao-1",
      ),
    ).toBe(
      "/apps/minha-delpi-chat/agentes/b185b233-b06a-4d23-8450-6ac3c0f7428d/conversas/sessao-1",
    );
  });

  it("rejeita agentId inválido ao montar href", () => {
    expect(buildChatAgentHref(undefined)).toBe("/apps/minha-delpi-chat/agentes");
    expect(buildChatAgentHref("undefined")).toBe("/apps/minha-delpi-chat/agentes");
  });

  it("monta href de sessão priorizando agente", () => {
    expect(
      buildChatSessionHrefForSession({
        id: "sessao-1",
        agent_id: "b185b233-b06a-4d23-8450-6ac3c0f7428d",
        project_id: null,
      }),
    ).toBe(
      "/apps/minha-delpi-chat/agentes/b185b233-b06a-4d23-8450-6ac3c0f7428d/conversas/sessao-1",
    );
  });

  it("resolve agente apenas por uuid", () => {
    expect(
      findAgentByRouteId(AGENTS, "b185b233-b06a-4d23-8450-6ac3c0f7428d")?.id,
    ).toBe("b185b233-b06a-4d23-8450-6ac3c0f7428d");
    expect(findAgentByRouteId(AGENTS, "minha-delpi-chat")).toBeUndefined();
  });

  it("canonicaliza rota com uuid", () => {
    expect(
      withCanonicalAgentRouteId(
        { kind: "agent-config", agentId: "legacy-slug" },
        AGENTS[0].id,
      ),
    ).toEqual({
      kind: "agent-config",
      agentId: AGENTS[0].id,
    });
  });

  it("identifica uuid na rota", () => {
    expect(isChatAgentRouteId("b185b233-b06a-4d23-8450-6ac3c0f7428d")).toBe(true);
    expect(isChatAgentRouteId("minha-delpi-chat")).toBe(false);
    expect(normalizeAgentRouteId("undefined")).toBeNull();
  });
});
