import type { Rnc8dReportPayload, TeamMember } from "../types/rnc8d";

function normalizedTeamMembers(members: TeamMember[] | undefined): TeamMember[] | undefined {
  if (!members?.length) {
    return undefined;
  }

  const filtered = members
    .map((member) => ({
      ...member,
      member_name: member.member_name?.trim() ?? "",
      department: member.department?.trim() || undefined,
    }))
    .filter((member) => member.member_name.length > 0);

  return filtered.length ? filtered : undefined;
}

/** Remove equipe vazia antes do PUT /rnc-8d (evita 422 por member_name min_length). */
export function sanitizeRnc8dReportPayload(payload: Rnc8dReportPayload): Rnc8dReportPayload {
  const team_members = normalizedTeamMembers(payload.team_members);
  const { team_members: _drop, ...rest } = payload;

  if (team_members) {
    return { ...rest, team_members };
  }

  return rest;
}

export function buildActivateRnc8dPayload(
  payload: Rnc8dReportPayload,
): Pick<Rnc8dReportPayload, "template_payload"> {
  return {
    template_payload: payload.template_payload,
  };
}
