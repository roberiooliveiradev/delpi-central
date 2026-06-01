import { describe, expect, it } from "vitest";

import {
  getChatSidebarViewForRoute,
  getInitialActiveAgentPageId,
  getInitialAgentEditRequest,
  getInitialSelectedProjectId,
  routeNeedsWorkspaceData,
} from "./chatRouteInitialState";

const AGENT_ID = "b185b233-b06a-4d23-8450-6ac3c0f7428d";
const PROJECT_ID = "c285c233-b06a-4d23-8450-6ac3c0f7428e";

describe("chatRouteInitialState", () => {
  it("inicializa builder de agente a partir da rota configurar", () => {
    const route = { kind: "agent-config" as const, agentId: AGENT_ID };

    expect(getChatSidebarViewForRoute(route)).toBe("agents");
    expect(getInitialAgentEditRequest(route)).toEqual({
      id: AGENT_ID,
      requestKey: 0,
    });
    expect(routeNeedsWorkspaceData(route)).toBe(true);
  });

  it("inicializa lista de projetos e projeto selecionado", () => {
    expect(getChatSidebarViewForRoute({ kind: "projects" })).toBe("projects");
    expect(
      getInitialSelectedProjectId({
        kind: "project-config",
        projectId: PROJECT_ID,
      }),
    ).toBe(PROJECT_ID);
  });

  it("inicializa chat do agente sem abrir builder", () => {
    const route = { kind: "agent" as const, agentId: AGENT_ID };

    expect(getChatSidebarViewForRoute(route)).toBe("chat");
    expect(getInitialActiveAgentPageId(route)).toBe(AGENT_ID);
    expect(getInitialAgentEditRequest(route)).toBeNull();
  });
});
