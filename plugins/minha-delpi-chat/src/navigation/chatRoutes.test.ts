import { describe, expect, it } from "vitest";

import {
  buildChatAgentHref,
  findAgentByRouteId,
  isChatAgentRouteId,
  parseChatRoute,
  withCanonicalAgentRouteId,
} from "./chatRoutes";

const AGENTS = [
  {
    id: "b185b233-b06a-4d23-8450-6ac3c0f7428d",
    key: "minha-delpi-chat",
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

  it("monta href com uuid", () => {
    expect(buildChatAgentHref("b185b233-b06a-4d23-8450-6ac3c0f7428d")).toBe(
      "/apps/minha-delpi-chat/agentes/b185b233-b06a-4d23-8450-6ac3c0f7428d",
    );
  });

  it("resolve agente por uuid ou slug legado", () => {
    expect(
      findAgentByRouteId(AGENTS, "b185b233-b06a-4d23-8450-6ac3c0f7428d")?.key,
    ).toBe("minha-delpi-chat");
    expect(findAgentByRouteId(AGENTS, "minha-delpi-chat")?.id).toBe(
      "b185b233-b06a-4d23-8450-6ac3c0f7428d",
    );
  });

  it("canonicaliza rota com uuid", () => {
    expect(
      withCanonicalAgentRouteId(
        { kind: "agent-config", agentId: "minha-delpi-chat" },
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
  });
});
