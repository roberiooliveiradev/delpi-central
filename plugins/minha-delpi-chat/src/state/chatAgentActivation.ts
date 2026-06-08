import type { ChatAgent } from "../data/api/chatTypes";

/**
 * Ativação explícita de agente no MFE — não herdar default de projeto nem agente de plataforma.
 *
 * Chat comum: nenhum agentId enviado à API até o usuário escolher no composer ou abrir rota de agente.
 */

export type ChatAgentActivationInput = {
  /** Agente escolhido no menu "+" do composer */
  contextAgentId?: string | null;
  /** Página/rota dedicada a um agente */
  activeAgentPageId?: string | null;
};

function normalizeId(value: string | null | undefined): string | null {
  const normalized = String(value ?? "").trim();
  return normalized || null;
}

function normalizeAgentId(value: string | null | undefined): string | null {
  return normalizeId(value);
}

/** ID do agente que o usuário ativou explicitamente neste turno (composer ou rota). */
export function resolveExplicitChatAgentId(
  input: ChatAgentActivationInput,
): string | null {
  return (
    normalizeAgentId(input.activeAgentPageId) ??
    normalizeAgentId(input.contextAgentId)
  );
}

/** Agente efetivo do turno — overlay do composer prevalece quando difere da página. */
export function resolveEffectiveChatAgentId(input: {
  pageAgentId?: string | null;
  contextAgentId?: string | null;
}): string | null {
  const pageAgentId = normalizeAgentId(input.pageAgentId);
  const contextAgentId = normalizeAgentId(input.contextAgentId);

  if (contextAgentId && pageAgentId && contextAgentId !== pageAgentId) {
    return contextAgentId;
  }

  return pageAgentId ?? contextAgentId;
}

/** Projeto efetivo do turno — overlay do composer prevalece quando difere da página. */
export function resolveEffectiveProjectId(input: {
  pageProjectId?: string | null;
  contextProjectId?: string | null;
}): string | null {
  const pageProjectId = normalizeId(input.pageProjectId);
  const contextProjectId = normalizeId(input.contextProjectId);

  if (contextProjectId && pageProjectId && contextProjectId !== pageProjectId) {
    return contextProjectId;
  }

  return pageProjectId ?? contextProjectId;
}

export function isExplicitChatAgentActive(agentId: string | null | undefined): boolean {
  return Boolean(normalizeAgentId(agentId));
}

function isSystemOfficialAgent(agent: ChatAgent): boolean {
  return agent.visibility === "system" || agent.access_role === "system";
}

/** Agente preferido ao disparar consulta operacional a partir do chat comum. */
export function resolvePreferredOperationalAgent(agents: ChatAgent[]): string | null {
  const enabled = agents.filter((agent) => agent.enabled !== false);

  if (enabled.length === 0) {
    return null;
  }

  const official = enabled.find((agent) => isSystemOfficialAgent(agent));

  if (official?.id) {
    return official.id;
  }

  const delpi = enabled.find((agent) => /minha\s*delpi/i.test(String(agent.name ?? "")));

  if (delpi?.id) {
    return delpi.id;
  }

  return enabled[0]?.id ?? null;
}

export type ChatModePresentation = {
  mode: "agent" | "common";
  label: string;
  subtitle: string;
};

export type ComposerContextBarItemKind = "agent" | "project";

export type ComposerContextBarItem = {
  kind: ComposerContextBarItemKind;
  id: string;
};

export type ComposerContextBarInput = {
  /** Agente da rota/página dedicada */
  pageAgentId?: string | null;
  /** Projeto da rota/página dedicada */
  pageProjectId?: string | null;
  /** Agente escolhido no menu + do composer */
  contextAgentId?: string | null;
  /** Projeto escolhido no menu + sem sair da página atual */
  contextProjectId?: string | null;
  /** Agente efetivo do turno (overlay, página ou sessão). */
  effectiveAgentId?: string | null;
  /** Projeto efetivo do turno (overlay, página ou sessão). */
  effectiveProjectId?: string | null;
};

export type ComposerContextBar = {
  items: ComposerContextBarItem[];
};

/**
 * Barra de contexto no composer: chips de agente e/ou projeto quando o usuário
 * adiciona contexto explícito que difere da superfície atual.
 */
export function resolveComposerContextBar(
  input: ComposerContextBarInput,
): ComposerContextBar {
  const pageAgentId = normalizeAgentId(input.pageAgentId);
  const pageProjectId = normalizeId(input.pageProjectId);
  const contextAgentId = normalizeAgentId(input.contextAgentId);
  const contextProjectId = normalizeId(input.contextProjectId);
  const effectiveAgentId =
    normalizeAgentId(input.effectiveAgentId) ?? contextAgentId;
  const effectiveProjectId =
    normalizeId(input.effectiveProjectId) ?? contextProjectId;
  const items: ComposerContextBarItem[] = [];

  if (effectiveAgentId && (!pageAgentId || effectiveAgentId !== pageAgentId)) {
    items.push({ kind: "agent", id: effectiveAgentId });
  }

  if (
    effectiveProjectId &&
    (!pageProjectId || effectiveProjectId !== pageProjectId)
  ) {
    items.push({ kind: "project", id: effectiveProjectId });
  }

  return { items };
}

type ChatModePresentationInput = {
  agentName?: string | null;
  projectName?: string | null;
  explicitAgentActive: boolean;
};

/** Rótulos de topbar/composer — fonte única para «Chat comum» vs agente. */
export function resolveChatModePresentation(
  input: ChatModePresentationInput,
): ChatModePresentation {
  const agentName = String(input.agentName ?? "").trim();

  if (input.explicitAgentActive && agentName) {
    if (input.projectName) {
      return {
        mode: "agent",
        label: agentName,
        subtitle: `Projeto ${input.projectName} · agente ativo`,
      };
    }

    return {
      mode: "agent",
      label: agentName,
      subtitle: "Agente ativo nesta conversa",
    };
  }

  if (input.projectName) {
    return {
      mode: "common",
      label: input.projectName,
      subtitle: "Chat comum do projeto (sem agente)",
    };
  }

  return {
    mode: "common",
    label: "Minha DELPI Chat",
    subtitle: "Chat comum (sem agente)",
  };
}
