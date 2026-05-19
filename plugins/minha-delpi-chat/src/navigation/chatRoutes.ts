export const CHAT_BASE_PATH = "/apps/minha-delpi-chat";

export type ChatRoute =
  | { kind: "home" }
  | { kind: "session"; sessionId: string }
  | { kind: "project"; projectId: string }
  | { kind: "agent"; agentKey: string }
  | { kind: "agents" }
  | { kind: "admin" };

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

  const [section, rawId] = rest.split("/");
  const id = rawId ? decodeURIComponent(rawId) : "";

  switch (section) {
    case "conversas":
      return id ? { kind: "session", sessionId: id } : { kind: "home" };
    case "projetos":
      return id ? { kind: "project", projectId: id } : { kind: "home" };
    case "agentes":
      return id ? { kind: "agent", agentKey: id } : { kind: "agents" };
    case "admin":
      return { kind: "admin" };
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
    case "agent":
      return `${CHAT_BASE_PATH}/agentes/${encodeURIComponent(route.agentKey)}`;
    case "agents":
      return `${CHAT_BASE_PATH}/agentes`;
    case "admin":
      return `${CHAT_BASE_PATH}/admin`;
  }
}

export function buildChatSessionHref(sessionId: string) {
  return buildChatHref({ kind: "session", sessionId });
}

export function buildChatProjectHref(projectId: string) {
  return buildChatHref({ kind: "project", projectId });
}

export function buildChatAgentHref(agentKey: string) {
  return buildChatHref({ kind: "agent", agentKey });
}
