export const CHAT_BASE_PATH = "/apps/minha-delpi-chat";

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export type ChatRoute =
  | { kind: "home" }
  | { kind: "session"; sessionId: string }
  | { kind: "project"; projectId: string }
  | { kind: "project-config"; projectId: string }
  | { kind: "agent"; agentId: string }
  | { kind: "agent-session"; agentId: string; sessionId: string }
  | { kind: "agent-config"; agentId: string }
  | { kind: "agent-skills"; agentId: string }
  | { kind: "agent-actions"; agentId: string; providerKey?: string }
  | { kind: "agents" }
  | { kind: "projects" }
  | { kind: "admin" }
  | { kind: "admin-agent"; agentId: string };

export function isChatAgentRouteId(value: string): boolean {
  return UUID_RE.test(value.trim());
}

export function normalizeAgentRouteId(value: string | null | undefined): string | null {
  const normalized = String(value ?? "").trim();

  if (!normalized || normalized === "undefined" || !isChatAgentRouteId(normalized)) {
    return null;
  }

  return normalized;
}

export function findAgentByRouteId<
  T extends { id: string },
>(agents: T[], routeId: string): T | undefined {
  const normalized = routeId.trim();

  if (!isChatAgentRouteId(normalized)) {
    return undefined;
  }

  return agents.find((agent) => agent.id === normalized);
}

export function withCanonicalAgentRouteId(route: ChatRoute, agentId: string): ChatRoute {
  switch (route.kind) {
    case "agent":
      return { kind: "agent", agentId };
    case "agent-session":
      return { ...route, agentId };
    case "agent-config":
      return { kind: "agent-config", agentId };
    case "agent-skills":
      return { kind: "agent-skills", agentId };
    case "agent-actions":
      return { ...route, agentId };
    default:
      return route;
  }
}

function normalizeBasePath(pathname: string) {
  if (!pathname.startsWith(CHAT_BASE_PATH)) {
    return null;
  }

  return pathname.slice(CHAT_BASE_PATH.length).replace(/^\/+/, "");
}

export function parseChatRoute(pathname?: string | null): ChatRoute {
  if (!pathname?.startsWith(CHAT_BASE_PATH)) {
    return { kind: "home" };
  }

  const rest = normalizeBasePath(pathname);

  if (!rest) {
    return { kind: "home" };
  }

  const segments = rest.split("/").filter(Boolean);
  const [section, ...sectionSegments] = segments;

  switch (section) {
    case "conversas": {
      const sessionId = sectionSegments[0];

      return sessionId
        ? { kind: "session", sessionId: decodeURIComponent(sessionId) }
        : { kind: "home" };
    }
    case "projetos": {
      if (sectionSegments.length === 0) {
        return { kind: "projects" };
      }

      const projectId = decodeURIComponent(sectionSegments[0]);

      if (sectionSegments[1] === "configurar") {
        return { kind: "project-config", projectId };
      }

      return { kind: "project", projectId };
    }
    case "agentes": {
      if (sectionSegments.length === 0) {
        return { kind: "agents" };
      }

      const agentId = decodeURIComponent(sectionSegments[0]);

      if (sectionSegments[1] === "conversas") {
        const sessionId = sectionSegments[2];

        if (sessionId) {
          return {
            kind: "agent-session",
            agentId,
            sessionId: decodeURIComponent(sessionId),
          };
        }

        return { kind: "agent", agentId };
      }

      if (sectionSegments[1] === "configurar") {
        if (sectionSegments[2] === "skills") {
          return { kind: "agent-skills", agentId };
        }

        if (sectionSegments[2] === "actions") {
          const providerKey = sectionSegments[3]
            ? decodeURIComponent(sectionSegments[3])
            : undefined;

          return { kind: "agent-actions", agentId, providerKey };
        }

        return { kind: "agent-config", agentId };
      }

      return { kind: "agent", agentId };
    }
    case "admin": {
      if (sectionSegments[0] === "agentes" && sectionSegments[1]) {
        return {
          kind: "admin-agent",
          agentId: decodeURIComponent(sectionSegments[1]),
        };
      }

      return { kind: "admin" };
    }
    default:
      return { kind: "home" };
  }
}

export function buildChatHref(route: ChatRoute): string {
  switch (route.kind) {
    case "home":
      return CHAT_BASE_PATH;
    case "session":
      return `${CHAT_BASE_PATH}/conversas/${encodeURIComponent(route.sessionId)}`;
    case "project":
      return `${CHAT_BASE_PATH}/projetos/${encodeURIComponent(route.projectId)}`;
    case "project-config":
      return `${CHAT_BASE_PATH}/projetos/${encodeURIComponent(route.projectId)}/configurar`;
    case "agent":
      return `${CHAT_BASE_PATH}/agentes/${encodeURIComponent(route.agentId)}`;
    case "agent-session":
      return `${CHAT_BASE_PATH}/agentes/${encodeURIComponent(route.agentId)}/conversas/${encodeURIComponent(route.sessionId)}`;
    case "agent-config":
      return `${CHAT_BASE_PATH}/agentes/${encodeURIComponent(route.agentId)}/configurar`;
    case "agent-skills":
      return `${CHAT_BASE_PATH}/agentes/${encodeURIComponent(route.agentId)}/configurar/skills`;
    case "agent-actions":
      return route.providerKey
        ? `${CHAT_BASE_PATH}/agentes/${encodeURIComponent(route.agentId)}/configurar/actions/${encodeURIComponent(route.providerKey)}`
        : `${CHAT_BASE_PATH}/agentes/${encodeURIComponent(route.agentId)}/configurar/actions`;
    case "agents":
      return `${CHAT_BASE_PATH}/agentes`;
    case "projects":
      return `${CHAT_BASE_PATH}/projetos`;
    case "admin":
      return `${CHAT_BASE_PATH}/admin`;
    case "admin-agent":
      return `${CHAT_BASE_PATH}/admin/agentes/${encodeURIComponent(route.agentId)}`;
  }
}

export function buildChatSessionHref(sessionId: string) {
  return buildChatHref({ kind: "session", sessionId });
}

export function buildChatProjectHref(projectId: string) {
  return buildChatHref({ kind: "project", projectId });
}

export function buildChatProjectConfigHref(projectId: string) {
  return buildChatHref({ kind: "project-config", projectId });
}

export function buildChatAgentHref(agentId: string | null | undefined) {
  const normalized = normalizeAgentRouteId(agentId);

  if (!normalized) {
    return buildChatHref({ kind: "agents" });
  }

  return buildChatHref({ kind: "agent", agentId: normalized });
}

export function buildChatAgentSessionHref(
  agentId: string | null | undefined,
  sessionId: string,
) {
  const normalizedAgentId = normalizeAgentRouteId(agentId);
  const normalizedSessionId = String(sessionId ?? "").trim();

  if (!normalizedAgentId || !normalizedSessionId) {
    return normalizedSessionId
      ? buildChatSessionHref(normalizedSessionId)
      : buildChatHref({ kind: "home" });
  }

  return buildChatHref({
    kind: "agent-session",
    agentId: normalizedAgentId,
    sessionId: normalizedSessionId,
  });
}

export function buildChatSessionHrefForSession(session: {
  id: string;
  agent_id?: string | null;
  project_id?: string | null;
}) {
  if (session.agent_id) {
    return buildChatAgentSessionHref(session.agent_id, session.id);
  }

  if (session.project_id) {
    return buildChatProjectHref(session.project_id);
  }

  return buildChatSessionHref(session.id);
}

export function buildChatAgentConfigHref(agentId: string) {
  return buildChatHref({ kind: "agent-config", agentId });
}

export function buildChatAgentSkillsHref(agentId: string) {
  return buildChatHref({ kind: "agent-skills", agentId });
}

export function buildChatAgentActionsHref(agentId: string, providerKey?: string | null) {
  return buildChatHref({
    kind: "agent-actions",
    agentId,
    providerKey: providerKey?.trim() || undefined,
  });
}

export function buildChatAdminAgentHref(agentId: string) {
  return buildChatHref({ kind: "admin-agent", agentId });
}
