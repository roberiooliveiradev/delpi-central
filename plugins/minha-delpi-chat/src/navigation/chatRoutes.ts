export const CHAT_BASE_PATH = "/apps/minha-delpi-chat";

export type ChatRoute =
  | { kind: "home" }
  | { kind: "session"; sessionId: string }
  | { kind: "project"; projectId: string }
  | { kind: "project-config"; projectId: string }
  | { kind: "agent"; agentKey: string }
  | { kind: "agent-config"; agentKey: string }
  | { kind: "agent-skills"; agentKey: string }
  | { kind: "agent-actions"; agentKey: string; providerKey?: string }
  | { kind: "agents" }
  | { kind: "projects" }
  | { kind: "admin" }
  | { kind: "admin-agent"; agentId: string };

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

      const agentKey = decodeURIComponent(sectionSegments[0]);

      if (sectionSegments[1] === "configurar") {
        if (sectionSegments[2] === "skills") {
          return { kind: "agent-skills", agentKey };
        }

        if (sectionSegments[2] === "actions") {
          const providerKey = sectionSegments[3]
            ? decodeURIComponent(sectionSegments[3])
            : undefined;

          return { kind: "agent-actions", agentKey, providerKey };
        }

        return { kind: "agent-config", agentKey };
      }

      return { kind: "agent", agentKey };
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
      return `${CHAT_BASE_PATH}/agentes/${encodeURIComponent(route.agentKey)}`;
    case "agent-config":
      return `${CHAT_BASE_PATH}/agentes/${encodeURIComponent(route.agentKey)}/configurar`;
    case "agent-skills":
      return `${CHAT_BASE_PATH}/agentes/${encodeURIComponent(route.agentKey)}/configurar/skills`;
    case "agent-actions":
      return route.providerKey
        ? `${CHAT_BASE_PATH}/agentes/${encodeURIComponent(route.agentKey)}/configurar/actions/${encodeURIComponent(route.providerKey)}`
        : `${CHAT_BASE_PATH}/agentes/${encodeURIComponent(route.agentKey)}/configurar/actions`;
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

export function buildChatAgentHref(agentKey: string) {
  return buildChatHref({ kind: "agent", agentKey });
}

export function buildChatAgentConfigHref(agentKey: string) {
  return buildChatHref({ kind: "agent-config", agentKey });
}

export function buildChatAgentSkillsHref(agentKey: string) {
  return buildChatHref({ kind: "agent-skills", agentKey });
}

export function buildChatAgentActionsHref(agentKey: string, providerKey?: string | null) {
  return buildChatHref({
    kind: "agent-actions",
    agentKey,
    providerKey: providerKey?.trim() || undefined,
  });
}

export function buildChatAdminAgentHref(agentId: string) {
  return buildChatHref({ kind: "admin-agent", agentId });
}
