import type { DelpiContactArea } from "./contactRoles";
import type { Rnc8dReportPayload, TeamMember } from "../types/rnc8d";
import { emptyRnc8dPayload } from "../types/rnc8d";
import { syncLegacyAttentionFields } from "./contactRoles";
import { normalizeRnc8dQuantityFields } from "./rnc8dQuantityFields";
import type { Rnc8dSharedIdentification } from "../constants/rnc8dSharedFields";

const VALID_DELPI_CONTACT_AREAS = new Set<DelpiContactArea>([
  "comercial",
  "qualidade",
  "pcp",
  "engenharia",
  "outro",
]);

function trimOptional(value: string | undefined | null): string | undefined {
  const trimmed = value?.trim();
  return trimmed || undefined;
}

/** API rejeita string vazia em campos com pattern (ex.: delpi_contact_area → 422). */
function sanitizeDelpiContactArea(value: string | undefined): string | undefined {
  const trimmed = value?.trim();
  if (!trimmed || !VALID_DELPI_CONTACT_AREAS.has(trimmed as DelpiContactArea)) {
    return undefined;
  }
  return trimmed as DelpiContactArea;
}

function sanitizeRnc8dOptionalStrings(payload: Rnc8dReportPayload): Rnc8dReportPayload {
  return {
    ...payload,
    client_nc_registry: trimOptional(payload.client_nc_registry),
    customer_name: trimOptional(payload.customer_name),
    customer_contact: trimOptional(payload.customer_contact),
    customer_contact_email: trimOptional(payload.customer_contact_email),
    customer_contact_phone: trimOptional(payload.customer_contact_phone),
    delpi_contact_name: trimOptional(payload.delpi_contact_name),
    delpi_contact_area: sanitizeDelpiContactArea(payload.delpi_contact_area),
    delpi_sales_rep: trimOptional(payload.delpi_sales_rep),
    delpi_quality_contact: trimOptional(payload.delpi_quality_contact),
    product_code: trimOptional(payload.product_code),
    product_description: trimOptional(payload.product_description),
    batch_number: trimOptional(payload.batch_number),
    reported_problem: trimOptional(payload.reported_problem),
  };
}

function normalizedTeamMembers(members: TeamMember[] | undefined): TeamMember[] | undefined {
  if (!members?.length) {
    return undefined;
  }

  const filtered = members
    .map((member, index) => ({
      member_name: member.member_name?.trim() ?? "",
      department: member.department?.trim() || undefined,
      member_user_id: member.member_user_id?.trim() || undefined,
      is_leader: member.is_leader ?? false,
      sort_order: member.sort_order ?? index,
    }))
    .filter((member) => member.member_name.length > 0);

  return filtered.length ? filtered : undefined;
}

/** Remove equipe vazia antes do PUT /rnc-8d (evita 422 por member_name min_length). */
export function sanitizeRnc8dReportPayload(payload: Rnc8dReportPayload): Rnc8dReportPayload {
  const team_members = normalizedTeamMembers(payload.team_members);
  const rest = sanitizeRnc8dOptionalStrings(syncLegacyAttentionFields({ ...payload }));
  delete rest.team_members;
  const template_payload = rest.template_payload
    ? normalizeRnc8dQuantityFields(rest.template_payload)
    : rest.template_payload;

  if (team_members) {
    return { ...rest, template_payload, team_members };
  }

  return { ...rest, template_payload };
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
