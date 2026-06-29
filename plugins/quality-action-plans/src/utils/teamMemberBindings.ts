import type { PlanAction } from "../types/actionPlan";
import type { Rnc8dReportPayload, TeamMember } from "../types/rnc8d";
import { emptyRnc8dPayload } from "../types/rnc8d";

export type TeamMemberBinding = {
  block: string;
  detail: string;
};

function normalizeName(value: string | null | undefined): string {
  return value?.trim() ?? "";
}

function matchesMemberName(reference: string | null | undefined, memberName: string): boolean {
  const ref = normalizeName(reference);
  const name = normalizeName(memberName);
  return Boolean(ref && name && ref === name);
}

function matchesMemberUserId(
  reference: string | null | undefined,
  memberUserId: string | null | undefined,
): boolean {
  const ref = normalizeName(reference);
  const id = normalizeName(memberUserId);
  return Boolean(ref && id && ref === id);
}

export function findTeamMemberBindings(
  member: TeamMember,
  context: {
    rnc8dForm: Rnc8dReportPayload;
    actions?: PlanAction[];
  },
): TeamMemberBinding[] {
  const bindings: TeamMemberBinding[] = [];
  const name = normalizeName(member.member_name);
  const userId = member.member_user_id ?? null;

  if (!name && !userId) {
    return bindings;
  }

  const payload = context.rnc8dForm.template_payload ?? emptyRnc8dPayload();
  const containment = payload.containment ?? [];

  containment.forEach((row, index) => {
    if (matchesMemberName(row.responsible, name)) {
      bindings.push({
        block: "Contenção (8D)",
        detail: `Linha ${index + 1} — responsável`,
      });
    }
  });

  const effectiveness = payload.effectiveness ?? {};
  if (matchesMemberName(effectiveness.verification_responsible, name)) {
    bindings.push({
      block: "Eficácia da ação corretiva (8D)",
      detail: "Responsável pela verificação",
    });
  }

  const preventive = payload.preventive ?? {};
  if (matchesMemberName(preventive.evaluation_responsible, name)) {
    bindings.push({
      block: "Ação preventiva (8D)",
      detail: "Responsável pela avaliação",
    });
  }

  (payload.documentation_updates ?? []).forEach((row, index) => {
    if (matchesMemberName(row.responsible, name)) {
      bindings.push({
        block: "Documentação (8D)",
        detail: `Linha ${index + 1} — responsável`,
      });
    }
  });

  for (const action of context.actions ?? []) {
    if (matchesMemberName(action.responsible_name, name)) {
      bindings.push({
        block: "Ações corretivas",
        detail: action.description.trim().slice(0, 60) || "Ação sem descrição",
      });
    } else if (matchesMemberUserId(action.responsible_user_id, userId)) {
      bindings.push({
        block: "Ações corretivas",
        detail: action.description.trim().slice(0, 60) || "Ação vinculada por usuário Delpi",
      });
    }
  }

  return bindings;
}

export function formatTeamMemberBindingMessage(
  memberName: string,
  bindings: TeamMemberBinding[],
): string {
  const label = memberName.trim() || "este membro";
  const lines = bindings.map((item) => `• ${item.block}: ${item.detail}`);
  return (
    `Não é possível remover ${label} — há vínculos em outros blocos:\n\n`
    + `${lines.join("\n")}\n\n`
    + "Remova ou altere as referências antes de excluir o membro."
  );
}
