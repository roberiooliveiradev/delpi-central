import type { PlanIdentificationFormState } from "../components/PlanProblemSection";
import type { FiveWhysForm } from "./fiveWhys";
import { serializeFiveWhysForm } from "./fiveWhys";
import type { IshikawaCausesForm } from "./ishikawaCauses";
import { serializeIshikawaCausesForm } from "./ishikawaCauses";
import type { Rnc8dReportPayload, Rnc8dTemplatePayload, TeamMember } from "../types/rnc8d";
import { emptyRnc8dPayload } from "../types/rnc8d";
import { sanitizeRnc8dReportPayload } from "./rnc8dPayload";

export type PlanDirtySection =
  | "status"
  | "identification"
  | "rnc8d-material"
  | "rnc8d-nc"
  | "rnc8d-team"
  | "rnc8d-containment"
  | "rnc8d-effectiveness-8d"
  | "rnc8d-preventive"
  | "rnc8d-closure"
  | "five-whys"
  | "ishikawa"
  | "effectiveness-pac";

export const PLAN_DIRTY_SECTION_LABELS: Record<PlanDirtySection, string> = {
  status: "Status do plano",
  identification: "Problema / identificação",
  "rnc8d-material": "Material e nota fiscal",
  "rnc8d-nc": "Descrição da não conformidade",
  "rnc8d-team": "Equipe de análise",
  "rnc8d-containment": "Ação de contenção",
  "rnc8d-effectiveness-8d": "Verificação da eficácia (8D)",
  "rnc8d-preventive": "Ação preventiva e documentos",
  "rnc8d-closure": "Fechamento do relatório 8D",
  "five-whys": "5 Porquês",
  ishikawa: "Ishikawa (6M)",
  "effectiveness-pac": "Registro de eficácia (PAC)",
};

export type PlanDetailSnapshot = {
  status: string;
  identification: PlanIdentificationFormState;
  rnc8dForm: Rnc8dReportPayload;
  fiveWhysForm: FiveWhysForm;
  ishikawaCausesForm: IshikawaCausesForm;
  ishikawaNotes: string;
  effectivenessStatus: string;
  effectivenessNotes: string;
};

const RNC8D_MATERIAL_PAYLOAD_KEYS = [
  "contact_phone",
  "purchase_order",
  "invoice_number",
  "invoice_date",
  "defective_quantity",
  "defective_quantity_unit",
  "client_batch",
  "batch_quantity",
  "batch_quantity_unit",
  "disposition",
  "rejected_quantity",
  "rejected_quantity_unit",
  "return_by",
] as const satisfies readonly (keyof Rnc8dTemplatePayload)[];

const RNC8D_CONTACT_ROLE_KEYS = [
  "customer_contact",
  "customer_contact_email",
  "customer_contact_phone",
  "delpi_contact_name",
  "delpi_contact_area",
  "delpi_sales_rep",
  "delpi_quality_contact",
] as const;

function stableJson(value: unknown): string {
  return JSON.stringify(value);
}

function normalizedTeamMembers(members: TeamMember[] | undefined): TeamMember[] {
  return (members ?? [])
    .map((member) => ({
      member_name: member.member_name?.trim() ?? "",
      member_user_id: member.member_user_id?.trim() || null,
      department: member.department?.trim() || undefined,
      is_leader: Boolean(member.is_leader),
      sort_order: member.sort_order ?? 0,
    }))
    .filter((member) => member.member_name.length > 0);
}

function pickMaterialSlice(form: Rnc8dReportPayload) {
  const payload = form.template_payload ?? emptyRnc8dPayload();
  const slice: Record<string, unknown> = {};
  for (const key of RNC8D_CONTACT_ROLE_KEYS) {
    slice[key] = form[key] ?? "";
  }
  for (const key of RNC8D_MATERIAL_PAYLOAD_KEYS) {
    slice[key] = payload[key] ?? "";
  }
  return slice;
}

function pickNcSlice(form: Rnc8dReportPayload) {
  const payload = form.template_payload ?? emptyRnc8dPayload();
  const nc = payload.nc_description ?? {};
  return {
    characteristic: nc.characteristic ?? "",
    specified: nc.specified ?? "",
    observations: nc.observations ?? payload.observations ?? "",
  };
}

function pickContainmentSlice(form: Rnc8dReportPayload) {
  const payload = form.template_payload ?? emptyRnc8dPayload();
  return payload.containment ?? [];
}

function pickEffectiveness8dSlice(form: Rnc8dReportPayload) {
  const payload = form.template_payload ?? emptyRnc8dPayload();
  return payload.effectiveness ?? {};
}

function pickPreventiveSlice(form: Rnc8dReportPayload) {
  const payload = form.template_payload ?? emptyRnc8dPayload();
  return {
    preventive: payload.preventive ?? {},
    documentation_updates: payload.documentation_updates ?? [],
  };
}

function pickClosureSlice(form: Rnc8dReportPayload) {
  const payload = form.template_payload ?? emptyRnc8dPayload();
  return payload.client_closure_note ?? "";
}

export function snapshotRnc8dForm(form: Rnc8dReportPayload): Rnc8dReportPayload {
  return sanitizeRnc8dReportPayload(form);
}

export function computePlanDirtySections(
  snapshot: PlanDetailSnapshot | null,
  current: PlanDetailSnapshot,
  options: { showRnc8dFlow: boolean },
): PlanDirtySection[] {
  if (!snapshot) {
    return [];
  }

  const dirty: PlanDirtySection[] = [];

  if (current.status !== snapshot.status) {
    dirty.push("status");
  }

  if (stableJson(current.identification) !== stableJson(snapshot.identification)) {
    dirty.push("identification");
  }

  if (options.showRnc8dFlow) {
    if (stableJson(pickMaterialSlice(current.rnc8dForm)) !== stableJson(pickMaterialSlice(snapshot.rnc8dForm))) {
      dirty.push("rnc8d-material");
    }
    if (stableJson(pickNcSlice(current.rnc8dForm)) !== stableJson(pickNcSlice(snapshot.rnc8dForm))) {
      dirty.push("rnc8d-nc");
    }
    if (
      stableJson(normalizedTeamMembers(current.rnc8dForm.team_members))
      !== stableJson(normalizedTeamMembers(snapshot.rnc8dForm.team_members))
    ) {
      dirty.push("rnc8d-team");
    }
    if (
      stableJson(pickContainmentSlice(current.rnc8dForm))
      !== stableJson(pickContainmentSlice(snapshot.rnc8dForm))
    ) {
      dirty.push("rnc8d-containment");
    }
    if (
      stableJson(pickEffectiveness8dSlice(current.rnc8dForm))
      !== stableJson(pickEffectiveness8dSlice(snapshot.rnc8dForm))
    ) {
      dirty.push("rnc8d-effectiveness-8d");
    }
    if (
      stableJson(pickPreventiveSlice(current.rnc8dForm))
      !== stableJson(pickPreventiveSlice(snapshot.rnc8dForm))
    ) {
      dirty.push("rnc8d-preventive");
    }
    if (pickClosureSlice(current.rnc8dForm) !== pickClosureSlice(snapshot.rnc8dForm)) {
      dirty.push("rnc8d-closure");
    }
  }

  if (
    stableJson(serializeFiveWhysForm(current.fiveWhysForm))
    !== stableJson(serializeFiveWhysForm(snapshot.fiveWhysForm))
  ) {
    dirty.push("five-whys");
  }

  if (
    stableJson(serializeIshikawaCausesForm(current.ishikawaCausesForm, current.ishikawaNotes))
    !== stableJson(
      serializeIshikawaCausesForm(snapshot.ishikawaCausesForm, snapshot.ishikawaNotes),
    )
  ) {
    dirty.push("ishikawa");
  }

  if (
    current.effectivenessStatus !== snapshot.effectivenessStatus
    || current.effectivenessNotes !== snapshot.effectivenessNotes
  ) {
    dirty.push("effectiveness-pac");
  }

  return dirty;
}

export function buildPlanDetailSnapshot(snapshot: PlanDetailSnapshot): PlanDetailSnapshot {
  return {
    status: snapshot.status,
    identification: { ...snapshot.identification },
    rnc8dForm: snapshotRnc8dForm(snapshot.rnc8dForm),
    fiveWhysForm: {
      occurrence: snapshot.fiveWhysForm.occurrence.map((step) => ({ ...step })),
      detection: snapshot.fiveWhysForm.detection.map((step) => ({ ...step })),
      root_cause: snapshot.fiveWhysForm.root_cause,
      confidence_level: snapshot.fiveWhysForm.confidence_level,
    },
    ishikawaCausesForm: { ...snapshot.ishikawaCausesForm },
    ishikawaNotes: snapshot.ishikawaNotes,
    effectivenessStatus: snapshot.effectivenessStatus,
    effectivenessNotes: snapshot.effectivenessNotes,
  };
}

export function isPlanSectionDirty(
  dirtySections: PlanDirtySection[],
  section: PlanDirtySection,
): boolean {
  return dirtySections.includes(section);
}

export function hasAnyRnc8dDirtySection(sections: PlanDirtySection[]): boolean {
  return sections.some((section) => section.startsWith("rnc8d-"));
}

/** Chaves de edição na UI (podem agrupar mais de um bloco dirty). */
export type PlanSectionEditKey =
  | PlanDirtySection
  | "problem"
  | "evidences"
  | "actions";

export function revertRnc8dFormSection(
  current: Rnc8dReportPayload,
  snapshot: Rnc8dReportPayload,
  section:
    | "rnc8d-material"
    | "rnc8d-nc"
    | "rnc8d-team"
    | "rnc8d-containment"
    | "rnc8d-effectiveness-8d"
    | "rnc8d-preventive"
    | "rnc8d-closure",
): Rnc8dReportPayload {
  const snapPayload = snapshot.template_payload ?? emptyRnc8dPayload();
  const currentPayload = current.template_payload ?? emptyRnc8dPayload();
  const nextPayload: Rnc8dTemplatePayload = { ...currentPayload };

  switch (section) {
    case "rnc8d-material": {
      const next = { ...current, template_payload: nextPayload };
      for (const key of RNC8D_CONTACT_ROLE_KEYS) {
        (next as Record<string, unknown>)[key] = snapshot[key] ?? "";
      }
      for (const key of RNC8D_MATERIAL_PAYLOAD_KEYS) {
        (nextPayload as Record<string, unknown>)[key] = snapPayload[key] ?? "";
      }
      return next;
    }
    case "rnc8d-nc":
      nextPayload.nc_description = { ...(snapPayload.nc_description ?? {}) };
      nextPayload.observations = snapPayload.observations ?? "";
      return { ...current, template_payload: nextPayload };
    case "rnc8d-team":
      return {
        ...current,
        team_members: (snapshot.team_members ?? []).map((member) => ({ ...member })),
      };
    case "rnc8d-containment":
      nextPayload.containment = (snapPayload.containment ?? []).map((row) => ({ ...row }));
      return { ...current, template_payload: nextPayload };
    case "rnc8d-effectiveness-8d":
      nextPayload.effectiveness = { ...(snapPayload.effectiveness ?? {}) };
      return { ...current, template_payload: nextPayload };
    case "rnc8d-preventive":
      nextPayload.preventive = { ...(snapPayload.preventive ?? {}) };
      nextPayload.documentation_updates = (snapPayload.documentation_updates ?? []).map(
        (row) => ({ ...row }),
      );
      return { ...current, template_payload: nextPayload };
    case "rnc8d-closure":
      nextPayload.client_closure_note = snapPayload.client_closure_note ?? "";
      return { ...current, template_payload: nextPayload };
    default:
      return current;
  }
}

export function cloneFiveWhysForm(form: FiveWhysForm): FiveWhysForm {
  return {
    occurrence: form.occurrence.map((step) => ({ ...step })),
    detection: form.detection.map((step) => ({ ...step })),
    root_cause: form.root_cause,
    confidence_level: form.confidence_level,
  };
}
