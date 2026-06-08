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

function normalizeAgentId(value: string | null | undefined): string | null {
  const normalized = String(value ?? "").trim();
  return normalized || null;
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

export function isExplicitChatAgentActive(agentId: string | null | undefined): boolean {
  return Boolean(normalizeAgentId(agentId));
}

export type ChatModePresentation = {
  mode: "agent" | "common";
  label: string;
  subtitle: string;
};

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
