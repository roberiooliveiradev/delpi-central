import { describe, expect, it } from "vitest";

import { agentPrimaryLabel, agentSecondaryLabel, agentStatusBadge } from "./agentDisplay";

const UUID = "f9c225b-0414-40d3-a462-040889719b83";

describe("agentDisplay", () => {
  it("usa nome legível quando não é UUID", () => {
    const agent = {
      id: UUID,
      name: "Assistente vendas",
      description: null,
      category: null,
      visibility: "private",
      enabled: true,
      hasSpecialization: true,
      specialization: null,
    };

    expect(agentPrimaryLabel(agent)).toBe("Assistente vendas");
    expect(agentSecondaryLabel(agent)).toBe(UUID);
  });

  it("evita ID técnico truncado como título principal", () => {
    const truncatedId = "f9c225b-0414-40d3-a462-040889719b83";
    const agent = {
      id: truncatedId,
      name: truncatedId,
      description: null,
      category: null,
      visibility: "private",
      enabled: true,
      hasSpecialization: true,
      specialization: {
        enabled: true,
        presetKey: "",
        label: "Admin execução",
        domain: "",
        knowledgeDomains: [],
        knowledgeNamespaces: [],
        knowledgeCategories: [],
        knowledgeTags: [],
        guidelineCategories: [],
        allowedTools: [],
        includeGlobalKnowledge: true,
      },
    };

    expect(agentPrimaryLabel(agent)).toBe("Admin execução");
    expect(agentSecondaryLabel(agent)).toBe(truncatedId);
  });

  it("define badge de status por agente", () => {
    expect(
      agentStatusBadge({
        id: UUID,
        name: "X",
        description: null,
        category: null,
        visibility: "private",
        enabled: false,
        hasSpecialization: false,
        specialization: null,
      }).label,
    ).toBe("Inativo");

    expect(
      agentStatusBadge({
        id: UUID,
        name: "X",
        description: null,
        category: null,
        visibility: "private",
        enabled: true,
        hasSpecialization: true,
        specialization: null,
      }).label,
    ).toBe("Especializado");
  });
});
