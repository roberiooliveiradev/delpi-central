import type {
  AdminLearningSummary,
  AdminMetricsSummary,
  AdminResponseEvaluationSummary,
  AdminSecuritySummary,
  AdminToolHealthResponse,
} from "../../../../data/api/adminTypes";
import type { AdminNavState } from "../../../../navigation/adminNavigation";
import { ADMIN_ATTENTION } from "../../../../content/adminAttentionContent";

export type AttentionSeverity = "critical" | "warning" | "info";

export type AttentionItem = {
  id: string;
  severity: AttentionSeverity;
  title: string;
  detail: string;
  nav: AdminNavState;
};

export type AttentionQueueInput = {
  toolHealth?: AdminToolHealthResponse | null;
  security?: AdminSecuritySummary | null;
  learning?: AdminLearningSummary | null;
  evaluations?: AdminResponseEvaluationSummary | null;
  metrics?: AdminMetricsSummary | null;
};

const SEVERITY_ORDER: Record<AttentionSeverity, number> = {
  critical: 0,
  warning: 1,
  info: 2,
};

function formatCount(value: number): string {
  return new Intl.NumberFormat("pt-BR").format(value);
}

function formatRate(value: number): string {
  return new Intl.NumberFormat("pt-BR", {
    style: "percent",
    maximumFractionDigits: 1,
  }).format(value);
}

function fill(template: string, vars: Record<string, string>): string {
  return template.replace(/\{(\w+)\}/g, (_, key: string) => vars[key] ?? "");
}

function pendingCandidateCount(learning: AdminLearningSummary | null | undefined): number {
  if (!learning) {
    return 0;
  }

  const byStatus = learning.candidates?.byStatus?.pending;
  if (typeof byStatus === "number" && byStatus > 0) {
    return byStatus;
  }

  return typeof learning.funnel?.pending === "number" ? learning.funnel.pending : 0;
}

/**
 * Monta a fila priorizada a partir dos summaries já usados no Painel / Aprendizagem.
 * Sem custo anômalo: falta baseline comparável na API (documentado no backlog).
 */
export function buildAttentionQueue(input: AttentionQueueInput): AttentionItem[] {
  const items: AttentionItem[] = [];
  const { thresholds } = ADMIN_ATTENTION;

  for (const tool of input.toolHealth?.items ?? []) {
    if (tool.status === "ok" || tool.status === "unknown") {
      continue;
    }

    const isError = tool.status === "error";
    items.push({
      id: `tool:${tool.id}`,
      severity: isError ? "critical" : "warning",
      title: isError ? ADMIN_ATTENTION.toolErrorTitle : ADMIN_ATTENTION.toolWarningTitle,
      detail: fill(ADMIN_ATTENTION.toolDetail, {
        label: tool.label,
        description: tool.description || tool.status,
      }),
      nav: { section: "platform", subTab: "tools" },
    });
  }

  const blocked = input.security?.blockedCount ?? 0;
  if (blocked > 0) {
    items.push({
      id: "security:blocked",
      severity: blocked >= 10 ? "critical" : "warning",
      title: ADMIN_ATTENTION.blockedTitle,
      detail: fill(ADMIN_ATTENTION.blockedDetail, { count: formatCount(blocked) }),
      nav: { section: "governance", subTab: "security" },
    });
  }

  const pending = pendingCandidateCount(input.learning);
  if (pending > 0) {
    items.push({
      id: "learning:pending",
      severity: "warning",
      title: ADMIN_ATTENTION.pendingCandidatesTitle,
      detail: fill(ADMIN_ATTENTION.pendingCandidatesDetail, {
        count: formatCount(pending),
      }),
      nav: { section: "knowledge", subTab: "learning", page: "candidates" },
    });
  }

  const failing = input.learning?.evaluation?.failing ?? 0;
  if (failing > 0) {
    items.push({
      id: "learning:eval-failing",
      severity: "critical",
      title: ADMIN_ATTENTION.failingEvalTitle,
      detail: fill(ADMIN_ATTENTION.failingEvalDetail, { count: formatCount(failing) }),
      nav: { section: "knowledge", subTab: "learning", page: "evaluation" },
    });
  }

  const errorRate = input.metrics?.errorRate24h;
  if (typeof errorRate === "number" && errorRate >= thresholds.errorRateWarning) {
    items.push({
      id: "metrics:error-rate",
      severity:
        errorRate >= thresholds.errorRateCritical ? "critical" : "warning",
      title: ADMIN_ATTENTION.errorRateTitle,
      detail: fill(ADMIN_ATTENTION.errorRateDetail, { rate: formatRate(errorRate) }),
      nav: { section: "quality", subTab: "metrics", page: "errors" },
    });
  }

  const avgScore = input.evaluations?.averageScore;
  const recentEvals = input.evaluations?.recent24h ?? 0;
  if (
    typeof avgScore === "number" &&
    recentEvals > 0 &&
    avgScore < thresholds.lowAverageScore
  ) {
    items.push({
      id: "evaluations:low-score",
      severity: "warning",
      title: ADMIN_ATTENTION.lowEvalScoreTitle,
      detail: fill(ADMIN_ATTENTION.lowEvalScoreDetail, {
        score: avgScore.toFixed(1),
        count: formatCount(recentEvals),
      }),
      nav: { section: "quality", subTab: "evaluations" },
    });
  }

  return items.sort((a, b) => {
    const bySeverity = SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity];
    if (bySeverity !== 0) {
      return bySeverity;
    }
    return a.id.localeCompare(b.id);
  });
}
