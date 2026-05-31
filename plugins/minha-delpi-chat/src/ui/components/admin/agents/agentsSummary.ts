import type { AdminSpecializedAgent } from "../../../../data/api/adminTypes";

export type AgentCatalogFilter = "all" | "enabled" | "disabled" | "specialized";

export type AgentsSummary = {
  total: number;
  enabled: number;
  disabled: number;
  withSpecialization: number;
};

export function computeAgentsSummary(agents: AdminSpecializedAgent[]): AgentsSummary {
  let enabled = 0;
  let withSpecialization = 0;

  for (const agent of agents) {
    if (agent.enabled) {
      enabled += 1;
    }

    if (agent.hasSpecialization) {
      withSpecialization += 1;
    }
  }

  return {
    total: agents.length,
    enabled,
    disabled: agents.length - enabled,
    withSpecialization,
  };
}

export function filterAgentsByCatalog(
  agents: AdminSpecializedAgent[],
  filter: AgentCatalogFilter,
): AdminSpecializedAgent[] {
  switch (filter) {
    case "enabled":
      return agents.filter((agent) => agent.enabled);
    case "disabled":
      return agents.filter((agent) => !agent.enabled);
    case "specialized":
      return agents.filter((agent) => agent.hasSpecialization);
    default:
      return agents;
  }
}
