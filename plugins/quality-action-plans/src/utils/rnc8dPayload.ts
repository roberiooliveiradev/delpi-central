import type { Rnc8dReportPayload, TeamMember } from "../types/rnc8d";
import { emptyRnc8dPayload } from "../types/rnc8d";
import type { Rnc8dSharedIdentification } from "../constants/rnc8dSharedFields";

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
  const rest = { ...payload };
  delete rest.team_members;

  if (team_members) {
    return { ...rest, team_members };
  }

  return rest;
}

/** Replica identificação do painel Problema no payload do relatório 8D (export/PDF). */
export function mergeSharedIdentificationIntoRnc8d(
  payload: Rnc8dReportPayload,
  shared: Rnc8dSharedIdentification,
): Rnc8dReportPayload {
  const template = payload.template_payload ?? emptyRnc8dPayload();
  const nc = template.nc_description ?? {};
  const reported = shared.reported_problem?.trim() || undefined;

  return {
    ...payload,
    client_nc_registry: shared.client_nc_registry?.trim() || undefined,
    customer_name: shared.customer_name?.trim() || undefined,
    product_code: shared.product_code?.trim() || undefined,
    product_description: shared.product_description?.trim() || undefined,
    batch_number: shared.batch_number?.trim() || undefined,
    reported_problem: reported,
    template_payload: {
      ...template,
      nc_description: {
        ...nc,
        verified: reported ?? nc.verified,
      },
    },
  };
}

export function buildActivateRnc8dPayload(
  payload: Rnc8dReportPayload,
): Pick<Rnc8dReportPayload, "template_payload"> {
  return {
    template_payload: payload.template_payload,
  };
}
