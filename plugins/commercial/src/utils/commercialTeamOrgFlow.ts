import type {
  OrgMembershipFlowModelEdge,
  OrgMembershipFlowModelNode,
} from "@delpi/plugin-ui/index";

export type CommercialTeamOrgGroupRef = {
  id: string;
  name: string;
  active?: boolean;
};

export type CommercialTeamOrgPerson = {
  user_id: string;
  name: string;
  email?: string | null;
  groups: readonly CommercialTeamOrgGroupRef[];
};

export type CommercialGroupsOrgFlowModel = {
  nodes: OrgMembershipFlowModelNode[];
  edges: OrgMembershipFlowModelEdge[];
};

/**
 * Modelo grupo → pessoa para `OrgMembershipFlow` na Equipe (sem nós portfolio).
 */
export function buildCommercialGroupsOrgFlowModel(input: {
  people: readonly CommercialTeamOrgPerson[];
}): CommercialGroupsOrgFlowModel {
  const nodes: OrgMembershipFlowModelNode[] = [];
  const edges: OrgMembershipFlowModelEdge[] = [];
  const nodeIds = new Set<string>();

  const ensurePerson = (person: CommercialTeamOrgPerson) => {
    const personNodeId = `person:${person.user_id}`;
    if (nodeIds.has(personNodeId)) return personNodeId;
    nodeIds.add(personNodeId);
    const title = (person.name || "").trim() || person.user_id;
    const email = (person.email || "").trim();
    nodes.push({
      id: personNodeId,
      kind: "person",
      entityId: person.user_id,
      title,
      subtitle: email || undefined,
    });
    return personNodeId;
  };

  const ensureGroup = (group: CommercialTeamOrgGroupRef) => {
    const groupNodeId = `group:${group.id}`;
    if (nodeIds.has(groupNodeId)) return groupNodeId;
    nodeIds.add(groupNodeId);
    nodes.push({
      id: groupNodeId,
      kind: "group",
      entityId: group.id,
      title: group.name,
      tone: group.active === false ? "muted" : "neutral",
    });
    return groupNodeId;
  };

  for (const person of peopleSorted(input.people)) {
    const personNodeId = ensurePerson(person);
    const memberships = [...person.groups].sort((a, b) =>
      a.name.localeCompare(b.name, "pt-BR"),
    );
    if (memberships.length === 0) continue;
    for (const group of memberships) {
      const groupNodeId = ensureGroup(group);
      edges.push({
        id: `edge:${group.id}:${person.user_id}`,
        source: groupNodeId,
        target: personNodeId,
      });
    }
  }

  return { nodes, edges };
}

function peopleSorted(
  people: readonly CommercialTeamOrgPerson[],
): CommercialTeamOrgPerson[] {
  return [...people].sort((a, b) => {
    const an = (a.name || a.user_id).localeCompare(b.name || b.user_id, "pt-BR");
    return an;
  });
}
