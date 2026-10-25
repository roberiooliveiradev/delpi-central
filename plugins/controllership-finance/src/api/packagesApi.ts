/** Cliente da BFF — P5 packages, review e conclusão mensal (docs 12/37). */
import { cfApiUrl, httpGet, httpPost } from "./httpClient";

export type PackageState =
  | "PACKAGE_INCOMPLETE"
  | "PACKAGE_FINALIZED"
  | "PACKAGE_SUBMITTED_FOR_REVIEW";

export type ReviewState =
  | "REVIEW_PENDING"
  | "REVIEW_IN_PROGRESS"
  | "CHANGES_REQUESTED"
  | "WAITING_FOR_CLARIFICATION"
  | "CLARIFICATION_RESOLVED"
  | "REVIEW_ACCEPTED"
  | "REVIEW_REJECTED";

export type ReviewOutcome =
  | "ACCEPTED"
  | "CHANGES_REQUESTED"
  | "REJECTED";

export type ClosingState =
  | "PENDING"
  | "MONTHLY_CLOSING_COMPLETED"
  | "TERMINALLY_REJECTED";

export type PackageVersion = {
  package_version_id: string;
  package_id: string;
  version_no: number;
  status: "DRAFT" | "FINALIZED" | "SUBMITTED";
  content: Record<string, unknown>;
  required_areas: string[] | null;
  previous_version_id: string | null;
  change_reason: string | null;
  finalized_by: string | null;
  finalized_at: string | null;
  submitted_by: string | null;
  submitted_at: string | null;
  revision: number;
  created_by: string;
  created_at: string;
};

export type AreaDecision = {
  decision_id: string;
  area: string;
  outcome: ReviewOutcome;
  actor_subject: string;
  note: string | null;
  created_at: string;
};

export type Clarification = {
  clarification_id: string;
  area: string | null;
  state: "OPEN" | "RESOLVED";
  question: string;
  response: string | null;
  opened_by: string;
  opened_at: string;
  resolved_by: string | null;
  resolved_at: string | null;
};

export type ReviewAssignment = {
  assignment_id: string;
  competence_id: string;
  package_id: string | null;
  role: "REVIEWER" | "COORDINATOR";
  area: string | null;
  subject: string;
  active: boolean;
  assigned_by: string;
  assigned_at: string;
  deactivated_by: string | null;
  deactivated_at: string | null;
  deactivate_reason: string | null;
};

export type ClosingPackage = {
  package_id: string | null;
  recipient_area: string;
  state: PackageState;
  review_state: ReviewState;
  current_version: PackageVersion | null;
  required_areas: string[];
  area_decisions: Record<string, AreaDecision>;
  open_clarifications: number;
  assignments: ReviewAssignment[];
  version_count?: number;
  versions?: (PackageVersion & {
    area_decisions: Record<string, AreaDecision>;
    clarifications: Clarification[];
  })[];
  blockers?: string[];
  revision: number;
};

export type PackageList = {
  period: string;
  applicable_areas: string[];
  packages: ClosingPackage[];
};

export type MonthlyClosingState = {
  period: string;
  state: ClosingState;
  blocking_reasons: string[];
  packages: ClosingPackage[];
  terminal_rejection: {
    state: string;
    reason: string;
    confirmed_by: string;
    confirmed_at: string;
  } | null;
};

export type Cockpit = {
  period: string;
  checklist: Record<string, number>;
  p3: {
    cutoff_confirmed: boolean;
    domains: {
      domain: string;
      source_state: string;
      provenance_kind: string | null;
      divergence: string | null;
    }[];
  };
  p4_pendencies: Record<string, number>;
  closing: MonthlyClosingState;
};

type Envelope<T> = { data?: T };

function base(period: string): string {
  return `/closing/competences/${period}`;
}

export async function listPackages(
  period: string,
  signal?: AbortSignal,
): Promise<PackageList> {
  const envelope = await httpGet<Envelope<PackageList>>(
    cfApiUrl(`${base(period)}/packages`),
    { signal },
  );
  return (
    envelope?.data ?? {
      period,
      applicable_areas: [],
      packages: [],
    }
  );
}

export async function getPackage(
  period: string,
  packageId: string,
  signal?: AbortSignal,
): Promise<ClosingPackage | null> {
  const envelope = await httpGet<Envelope<ClosingPackage>>(
    cfApiUrl(`${base(period)}/packages/${packageId}`),
    { signal },
  );
  return envelope?.data ?? null;
}

export async function finalizePackage(
  period: string,
  recipientArea: string,
  notes?: string,
): Promise<ClosingPackage | null> {
  const envelope = await httpPost<Envelope<ClosingPackage>>(
    cfApiUrl(`${base(period)}/packages/finalize`),
    { recipient_area: recipientArea, notes },
  );
  return envelope?.data ?? null;
}

export async function submitPackageForReview(
  period: string,
  packageVersionId: string,
  revision: number,
): Promise<ClosingPackage | null> {
  const envelope = await httpPost<Envelope<ClosingPackage>>(
    cfApiUrl(
      `${base(period)}/package-versions/${packageVersionId}/submit`,
    ),
    { revision },
  );
  return envelope?.data ?? null;
}

export async function reopenPackageVersion(
  period: string,
  packageVersionId: string,
  reason: string,
): Promise<ClosingPackage | null> {
  const envelope = await httpPost<Envelope<ClosingPackage>>(
    cfApiUrl(
      `${base(period)}/package-versions/${packageVersionId}/reopen`,
    ),
    { reason },
  );
  return envelope?.data ?? null;
}

export async function createPackageComplement(
  period: string,
  packageVersionId: string,
  reason: string,
): Promise<ClosingPackage | null> {
  const envelope = await httpPost<Envelope<ClosingPackage>>(
    cfApiUrl(
      `${base(period)}/package-versions/${packageVersionId}/complement`,
    ),
    { reason },
  );
  return envelope?.data ?? null;
}

export async function createReviewAssignment(
  period: string,
  input: {
    role: "REVIEWER" | "COORDINATOR";
    subject: string;
    recipientArea?: string;
    area?: string;
  },
): Promise<ReviewAssignment | null> {
  const envelope = await httpPost<Envelope<ReviewAssignment>>(
    cfApiUrl(`${base(period)}/assignments`),
    {
      role: input.role,
      subject: input.subject,
      recipient_area: input.recipientArea,
      area: input.area,
    },
  );
  return envelope?.data ?? null;
}

export async function deactivateReviewAssignment(
  period: string,
  assignmentId: string,
  reason?: string,
): Promise<ReviewAssignment | null> {
  const envelope = await httpPost<Envelope<ReviewAssignment>>(
    cfApiUrl(`${base(period)}/assignments/${assignmentId}/deactivate`),
    { reason },
  );
  return envelope?.data ?? null;
}

export async function recordReviewDecision(
  period: string,
  packageVersionId: string,
  input: {
    area: string;
    outcome: ReviewOutcome;
    note?: string;
  },
): Promise<AreaDecision | null> {
  const envelope = await httpPost<Envelope<AreaDecision>>(
    cfApiUrl(
      `${base(period)}/package-versions/${packageVersionId}/decisions`,
    ),
    { area: input.area, outcome: input.outcome, note: input.note },
  );
  return envelope?.data ?? null;
}

export async function openClarification(
  period: string,
  packageVersionId: string,
  input: { question: string; area?: string },
): Promise<Clarification | null> {
  const envelope = await httpPost<Envelope<Clarification>>(
    cfApiUrl(
      `${base(period)}/package-versions/${packageVersionId}`
        + "/clarifications",
    ),
    { question: input.question, area: input.area },
  );
  return envelope?.data ?? null;
}

export async function resolveClarification(
  period: string,
  clarificationId: string,
  response: string,
): Promise<Clarification | null> {
  const envelope = await httpPost<Envelope<Clarification>>(
    cfApiUrl(
      `${base(period)}/clarifications/${clarificationId}/resolve`,
    ),
    { response },
  );
  return envelope?.data ?? null;
}

export async function confirmTerminalRejection(
  period: string,
  reason: string,
): Promise<unknown> {
  const envelope = await httpPost<Envelope<unknown>>(
    cfApiUrl(`${base(period)}/terminal-rejection`),
    { reason },
  );
  return envelope?.data ?? null;
}

export async function revertTerminalRejection(
  period: string,
  reason: string,
): Promise<unknown> {
  const envelope = await httpPost<Envelope<unknown>>(
    cfApiUrl(`${base(period)}/terminal-rejection/revert`),
    { reason },
  );
  return envelope?.data ?? null;
}

export async function getMonthlyClosingState(
  period: string,
  signal?: AbortSignal,
): Promise<MonthlyClosingState | null> {
  const envelope = await httpGet<Envelope<MonthlyClosingState>>(
    cfApiUrl(`${base(period)}/closing-state`),
    { signal },
  );
  return envelope?.data ?? null;
}

export async function getClosingCockpit(
  period: string,
  signal?: AbortSignal,
): Promise<Cockpit | null> {
  const envelope = await httpGet<Envelope<Cockpit>>(
    cfApiUrl(`${base(period)}/cockpit`),
    { signal },
  );
  return envelope?.data ?? null;
}
