import type { ActionPlanDetail, PlanAction } from "../types/actionPlan";
import type { PlanEvidence } from "../types/rnc8d";
import { hasFilledWhysTrack } from "./fiveWhys";

export type Rnc8dDiscipline = {
  id: string;
  label: string;
  complete: boolean;
  hint: string;
};

export type Rnc8dDisciplineProgress = {
  disciplines: Rnc8dDiscipline[];
  percentComplete: number;
};

function hasText(value: string | null | undefined): boolean {
  return Boolean(value && value.trim());
}

function actionsByType(actions: PlanAction[], actionType: string): PlanAction[] {
  return actions.filter((action) => action.action_type === actionType);
}

export function computeRnc8dDisciplineProgress(detail: ActionPlanDetail): Rnc8dDisciplineProgress {
  const plan = detail.plan;
  const payload = plan.template_payload ?? {};
  const team = detail.team_members ?? [];
  const actions = detail.actions ?? [];
  const fiveWhys = detail.five_whys;
  const ishikawa = detail.ishikawa;

  const disciplines: Rnc8dDiscipline[] = [
    {
      id: "D0",
      label: "Planejamento",
      complete:
        hasText(plan.client_nc_registry) &&
        team.some((member) => hasText(member.member_name)),
      hint: "Registro NC do cliente e equipe inicial.",
    },
    {
      id: "D1",
      label: "Equipe",
      complete: team.some((member) => member.is_leader && hasText(member.member_name)),
      hint: "Líder da equipe nomeado.",
    },
    {
      id: "D2",
      label: "Descrição NC",
      complete:
        hasText(plan.reported_problem) &&
        (hasText(payload.nc_description?.characteristic) ||
          hasText(payload.nc_description?.specified) ||
          hasText(plan.product_code)),
      hint: "Problema relatado e descrição técnica.",
    },
    {
      id: "D3",
      label: "Contenção",
      complete:
        (payload.containment ?? []).some((row) => hasText(row.action_plan)) ||
        actionsByType(actions, "containment").length > 0,
      hint: "Plano de contenção nas três áreas ou ação de contenção.",
    },
    {
      id: "D4",
      label: "Causa raiz",
      complete:
        hasText(fiveWhys?.root_cause) ||
        hasFilledWhysTrack(fiveWhys?.occurrence_whys) ||
        hasFilledWhysTrack(fiveWhys?.detection_whys) ||
        Boolean(
          ishikawa &&
            (hasText(ishikawa.notes) ||
              [
                ishikawa.machine,
                ishikawa.method_process,
                ishikawa.material,
                ishikawa.manpower,
                ishikawa.measurement,
                ishikawa.environment,
              ].some((value) => Array.isArray(value) && value.some((item) => hasText(item)))),
        ),
      hint: "Porquês ou Ishikawa preenchidos.",
    },
    {
      id: "D5",
      label: "Ações corretivas",
      complete: actionsByType(actions, "corrective").length > 0,
      hint: "Pelo menos uma ação corretiva.",
    },
    {
      id: "D6",
      label: "Implementação",
      complete:
        actions.length > 0 &&
        actions.every((action) => action.status === "completed" || action.status === "cancelled"),
      hint: "Todas as ações concluídas ou canceladas.",
    },
    {
      id: "D7",
      label: "Preventiva",
      complete:
        actionsByType(actions, "preventive").length > 0 ||
        hasText(payload.preventive?.how_avoid_future),
      hint: "Ação preventiva ou seção preventiva do 8D.",
    },
    {
      id: "D8",
      label: "Eficácia",
      complete:
        hasText(plan.effectiveness_status) &&
        plan.effectiveness_status !== "pending" &&
        (hasText(payload.effectiveness?.resolved_how) || hasText(plan.effectiveness_notes)),
      hint: "Revisão de eficácia registrada.",
    },
  ];

  const completeCount = disciplines.filter((item) => item.complete).length;
  const percentComplete = Math.round((completeCount / disciplines.length) * 100);

  return { disciplines, percentComplete };
}

export function listActionsMissingRequiredEvidence(
  actions: PlanAction[],
  evidences: PlanEvidence[],
): PlanAction[] {
  const linkedActionIds = new Set(
    evidences.map((item) => item.action_id).filter((id): id is string => Boolean(id)),
  );

  return actions.filter(
    (action) => action.evidence_required && !linkedActionIds.has(action.id),
  );
}
