import type { ChatRoute } from "./chatRoutes";

export type ChatSidebarView = "chat" | "agents" | "projects";

export function getChatSidebarViewForRoute(route: ChatRoute): ChatSidebarView {
  switch (route.kind) {
    case "agents":
    case "agent-config":
    case "agent-skills":
    case "agent-actions":
      return "agents";
    case "projects":
      return "projects";
    default:
      return "chat";
  }
}

export function getInitialAgentEditRequest(route: ChatRoute | undefined) {
  if (route?.kind !== "agent-config") {
    return null;
  }

  return {
    id: route.agentId,
    requestKey: 0,
  };
}

export function getInitialActiveAgentPageId(route: ChatRoute | undefined): string | null {
  if (route?.kind === "agent" || route?.kind === "agent-session") {
    return route.agentId;
  }

  return null;
}

export function getInitialSelectedProjectId(route: ChatRoute | undefined): string | null {
  if (
    route?.kind === "project" ||
    route?.kind === "project-session" ||
    route?.kind === "project-config"
  ) {
    return route.projectId;
  }

  return null;
}

export function routeNeedsWorkspaceData(route: ChatRoute): boolean {
  switch (route.kind) {
    case "agent":
    case "agent-session":
    case "agent-config":
    case "agent-skills":
    case "agent-actions":
    case "project":
    case "project-session":
    case "project-config":
      return true;
    default:
      return false;
  }
}
