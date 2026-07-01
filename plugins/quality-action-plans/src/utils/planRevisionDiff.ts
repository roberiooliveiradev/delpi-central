import {
  EFFECTIVENESS_STATUSES,
  PLAN_STATUSES,
  actionTypeLabel,
} from "../constants/actionPlans";
import type {
  ActionPlanDetail,
  FiveWhysAnalysis,
  IshikawaAnalysis,
  PlanAction,
} from "../types/actionPlan";

export type RevisionDiffRow = {
  label: string;
  current: string;
  revision: string;
  changed: boolean;
};

export type RevisionDiffSection = {
  key: string;
  title: string;
  rows: RevisionDiffRow[];
};

type RevisionDiffPlan = ActionPlanDetail["plan"];

const PLAN_DIFF_FIELDS: Array<{ key: keyof RevisionDiffPlan | string; label: string }> = [
  { key: "title", label: "Título" },
  { key: "status", label: "Status" },
  { key: "severity", label: "Severidade" },
  { key: "branch_code", label: "Filial" },
  { key: "product_code", label: "Produto" },
  { key: "customer_name", label: "Cliente" },
  { key: "reported_problem", label: "Problema relatado" },
  { key: "department", label: "Departamento" },
  { key: "failure_mode", label: "Modo de falha" },
  { key: "problem_category", label: "Categoria" },
  { key: "batch_number", label: "Lote" },
  { key: "root_cause_category", label: "Categoria de causa raiz" },
];

const EFFECTIVENESS_DIFF_FIELDS: Array<{ key: keyof RevisionDiffPlan | string; label: string }> = [
  { key: "effectiveness_status", label: "Status de eficácia" },
  { key: "effectiveness_notes", label: "Notas de eficácia" },
  { key: "effectiveness_proposed_status", label: "Eficácia proposta" },
  { key: "effectiveness_approval_status", label: "Aprovação de eficácia" },
];

const ISHIKAWA_FIELDS: Array<{ key: keyof IshikawaAnalysis; label: string }> = [
  { key: "machine", label: "Máquina" },
  { key: "method_process", label: "Método / processo" },
  { key: "material", label: "Material" },
  { key: "manpower", label: "Mão de obra" },
  { key: "measurement", label: "Medição" },
  { key: "environment", label: "Meio ambiente" },
  { key: "notes", label: "Observações" },
];

function formatPlanValue(key: string, value: unknown): string {
  if (value == null || value === "") {
    return "—";
  }
  if (key === "status") {
    const match = PLAN_STATUSES.find((item) => item.value === value);
    return match?.label ?? String(value);
  }
  if (key === "effectiveness_status" || key === "effectiveness_proposed_status") {
    const match = EFFECTIVENESS_STATUSES.find((item) => item.value === value);
    return match?.label ?? String(value);
  }
  if (Array.isArray(value)) {
    return value.length ? value.join(", ") : "—";
  }
  return String(value);
}

function formatStringList(value: unknown): string {
  if (value == null || value === "") {
    return "—";
  }
  if (Array.isArray(value)) {
    const items = value.map((item) => String(item).trim()).filter(Boolean);
    return items.length ? items.join("; ") : "—";
  }
  return String(value);
}

function formatWhysSteps(value: unknown): string {
  if (!Array.isArray(value) || value.length === 0) {
    return "—";
  }
  return value
    .map((step, index) => {
      if (typeof step === "string") {
        return `${index + 1}. ${step.trim() || "—"}`;
      }
      if (step && typeof step === "object") {
        const record = step as { question?: string; answer?: string };
        const answer = (record.answer || record.question || "").trim();
        return `${index + 1}. ${answer || "—"}`;
      }
      return `${index + 1}. —`;
    })
    .join(" · ");
}

function shortActionId(actionId: string): string {
  return actionId.slice(0, 8);
}

function normalizeActions(actions: unknown): PlanAction[] {
  if (!Array.isArray(actions)) {
    return [];
  }
  return actions
    .filter((item): item is PlanAction => Boolean(item && typeof item === "object" && item.id))
    .slice()
    .sort((left, right) => String(left.id).localeCompare(String(right.id)));
}

function buildFieldDiffRows(
  current: Record<string, unknown>,
  revision: Record<string, unknown>,
  fields: Array<{ key: string; label: string }>,
): RevisionDiffRow[] {
  return fields
    .map(({ key, label }) => {
      const currentValue = formatPlanValue(key, current[key]);
      const revisionValue = formatPlanValue(key, revision[key]);
      return {
        label,
        current: currentValue,
        revision: revisionValue,
        changed: currentValue !== revisionValue,
      };
    })
    .filter((row) => row.changed);
}

export function buildRevisionPlanDiff(
  current: Pick<
    RevisionDiffPlan,
    "title" | "status" | "severity" | "product_code" | "customer_name"
  > & {
    reported_problem?: string | null;
  },
  snapshotPlan: Record<string, unknown> | null | undefined,
): RevisionDiffRow[] {
  const snapshot = snapshotPlan ?? {};
  return buildFieldDiffRows(current as Record<string, unknown>, snapshot, PLAN_DIFF_FIELDS);
}

function buildIshikawaDiff(
  current: IshikawaAnalysis | null | undefined,
  revision: unknown,
): RevisionDiffRow[] {
  const snapshot = (revision && typeof revision === "object" ? revision : {}) as IshikawaAnalysis;
  return ISHIKAWA_FIELDS.map(({ key, label }) => {
    const currentValue = formatStringList(current?.[key]);
    const revisionValue = formatStringList(snapshot[key]);
    return {
      label,
      current: currentValue,
      revision: revisionValue,
      changed: currentValue !== revisionValue,
    };
  }).filter((row) => row.changed);
}

function buildFiveWhysDiff(
  current: FiveWhysAnalysis | null | undefined,
  revision: unknown,
): RevisionDiffRow[] {
  const snapshot = (revision && typeof revision === "object" ? revision : {}) as FiveWhysAnalysis;
  const rows: RevisionDiffRow[] = [
    {
      label: "Porquês (ocorrência)",
      current: formatWhysSteps(current?.occurrence_whys),
      revision: formatWhysSteps(snapshot.occurrence_whys),
      changed: false,
    },
    {
      label: "Porquês (detecção)",
      current: formatWhysSteps(current?.detection_whys),
      revision: formatWhysSteps(snapshot.detection_whys),
      changed: false,
    },
    {
      label: "Causa raiz",
      current: formatPlanValue("root_cause", current?.root_cause),
      revision: formatPlanValue("root_cause", snapshot.root_cause),
      changed: false,
    },
    {
      label: "Confiança",
      current: formatPlanValue("confidence_level", current?.confidence_level),
      revision: formatPlanValue("confidence_level", snapshot.confidence_level),
      changed: false,
    },
  ];
  return rows
    .map((row) => ({ ...row, changed: row.current !== row.revision }))
    .filter((row) => row.changed);
}

function buildActionsDiff(current: PlanAction[], revision: unknown): RevisionDiffRow[] {
  const revisionActions = normalizeActions(revision);
  const rows: RevisionDiffRow[] = [];

  if (current.length !== revisionActions.length) {
    rows.push({
      label: "Quantidade de ações",
      current: String(current.length),
      revision: String(revisionActions.length),
      changed: true,
    });
  }

  const currentById = new Map(current.map((action) => [action.id, action]));
  const revisionById = new Map(revisionActions.map((action) => [action.id, action]));
  const actionIds = new Set([...currentById.keys(), ...revisionById.keys()]);

  for (const actionId of [...actionIds].sort()) {
    const currentAction = currentById.get(actionId);
    const revisionAction = revisionById.get(actionId);
    const prefix = `Ação ${shortActionId(actionId)}`;

    if (!currentAction && revisionAction) {
      rows.push({
        label: `${prefix} (nova)`,
        current: "—",
        revision: revisionAction.description,
        changed: true,
      });
      continue;
    }

    if (currentAction && !revisionAction) {
      rows.push({
        label: `${prefix} (removida)`,
        current: currentAction.description,
        revision: "—",
        changed: true,
      });
      continue;
    }

    if (!currentAction || !revisionAction) {
      continue;
    }

    const comparisons: Array<{ label: string; left: unknown; right: unknown; format?: string }> = [
      { label: "Descrição", left: currentAction.description, right: revisionAction.description },
      { label: "Status", left: currentAction.status, right: revisionAction.status, format: "status" },
      {
        label: "Tipo",
        left: currentAction.action_type,
        right: revisionAction.action_type,
        format: "action_type",
      },
      { label: "Prazo", left: currentAction.due_date, right: revisionAction.due_date },
    ];

    for (const comparison of comparisons) {
      const left =
        comparison.format === "action_type"
          ? actionTypeLabel(String(comparison.left ?? ""))
          : formatPlanValue(comparison.format ?? "text", comparison.left);
      const right =
        comparison.format === "action_type"
          ? actionTypeLabel(String(comparison.right ?? ""))
          : formatPlanValue(comparison.format ?? "text", comparison.right);
      if (left !== right) {
        rows.push({
          label: `${prefix} · ${comparison.label}`,
          current: left,
          revision: right,
          changed: true,
        });
      }
    }
  }

  return rows;
}

function buildTeamDiff(current: ActionPlanDetail["team_members"], revision: unknown): RevisionDiffRow[] {
  const currentValue = formatStringList(
    (current ?? []).map((member) => member.member_name).filter(Boolean),
  );
  const revisionMembers = Array.isArray(revision) ? revision : [];
  const revisionValue = formatStringList(
    revisionMembers
      .map((member) =>
        member && typeof member === "object"
          ? String((member as { member_name?: string }).member_name ?? "").trim()
          : "",
      )
      .filter(Boolean),
  );
  if (currentValue === revisionValue) {
    return [];
  }
  return [
    {
      label: "Membros da equipe",
      current: currentValue,
      revision: revisionValue,
      changed: true,
    },
  ];
}

function buildEvidencesDiff(
  current: ActionPlanDetail["evidences"],
  revision: unknown,
): RevisionDiffRow[] {
  const formatEvidenceList = (items: unknown): string => {
    if (!Array.isArray(items) || items.length === 0) {
      return "—";
    }
    return items
      .map((item) => {
        if (!item || typeof item !== "object") {
          return "";
        }
        const record = item as { file_name?: string; description?: string; section?: string };
        return record.file_name || record.description || record.section || "evidência";
      })
      .filter(Boolean)
      .join(", ");
  };

  const currentValue = formatEvidenceList(current ?? []);
  const revisionValue = formatEvidenceList(revision);
  if (currentValue === revisionValue) {
    return [];
  }
  return [
    {
      label: "Anexos (metadados)",
      current: currentValue,
      revision: revisionValue,
      changed: true,
    },
  ];
}

export function buildRevisionSnapshotDiff(
  detail: ActionPlanDetail,
  snapshot: Record<string, unknown>,
): RevisionDiffSection[] {
  const snapshotPlan =
    typeof snapshot.plan === "object" && snapshot.plan !== null
      ? (snapshot.plan as Record<string, unknown>)
      : {};

  const sections: RevisionDiffSection[] = [];

  const identificationRows = buildFieldDiffRows(
    detail.plan as Record<string, unknown>,
    snapshotPlan,
    PLAN_DIFF_FIELDS,
  );
  if (identificationRows.length) {
    sections.push({
      key: "identification",
      title: "Identificação",
      rows: identificationRows,
    });
  }

  const ishikawaRows = buildIshikawaDiff(detail.ishikawa, snapshot.ishikawa);
  if (ishikawaRows.length) {
    sections.push({ key: "ishikawa", title: "Ishikawa (6M)", rows: ishikawaRows });
  }

  const fiveWhysRows = buildFiveWhysDiff(detail.five_whys, snapshot.five_whys);
  if (fiveWhysRows.length) {
    sections.push({ key: "five_whys", title: "5 Porquês", rows: fiveWhysRows });
  }

  const actionsRows = buildActionsDiff(detail.actions ?? [], snapshot.actions);
  if (actionsRows.length) {
    sections.push({ key: "actions", title: "Ações", rows: actionsRows });
  }

  const teamRows = buildTeamDiff(detail.team_members, snapshot.team_members);
  if (teamRows.length) {
    sections.push({ key: "team", title: "Equipe 8D", rows: teamRows });
  }

  const evidenceRows = buildEvidencesDiff(detail.evidences, snapshot.evidences);
  if (evidenceRows.length) {
    sections.push({ key: "evidences", title: "Evidências", rows: evidenceRows });
  }

  const effectivenessRows = buildFieldDiffRows(
    detail.plan as Record<string, unknown>,
    snapshotPlan,
    EFFECTIVENESS_DIFF_FIELDS,
  );
  if (effectivenessRows.length) {
    sections.push({ key: "effectiveness", title: "Eficácia", rows: effectivenessRows });
  }

  return sections;
}
