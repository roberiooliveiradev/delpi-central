import type { AdminSpecializedAgent } from "../../../../data/api/adminTypes";

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

/** IDs técnicos exibidos como nome (inclui UUIDs truncados no catálogo). */
function looksLikeTechnicalId(value: string): boolean {
  if (!value) {
    return false;
  }

  if (UUID_RE.test(value)) {
    return true;
  }

  return /^[0-9a-f]{6,8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value);
}

export function agentPrimaryLabel(agent: AdminSpecializedAgent): string {
  const name = String(agent.name || "").trim();
  const specLabel = String(agent.specialization?.label || "").trim();

  if (name && !looksLikeTechnicalId(name)) {
    return name;
  }

  if (specLabel) {
    return specLabel;
  }

  if (name) {
    return name;
  }

  return `Agente ${agent.id.slice(0, 8)}`;
}

export function agentSecondaryLabel(agent: AdminSpecializedAgent): string {
  const primary = agentPrimaryLabel(agent);
  const name = String(agent.name || "").trim();

  if (name && name !== primary) {
    return name;
  }

  return agent.id;
}

export type AgentStatusBadge = {
  label: string;
  tone: "success" | "muted" | "accent";
};

export function agentStatusBadge(agent: AdminSpecializedAgent): AgentStatusBadge {
  if (!agent.enabled) {
    return { label: "Inativo", tone: "muted" };
  }

  if (agent.hasSpecialization) {
    return { label: "Especializado", tone: "accent" };
  }

  return { label: "Ativo", tone: "success" };
}
