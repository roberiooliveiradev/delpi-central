import { listCompetences } from "../../api/competencesApi";
import {
  getEntryAuditSummary,
  listEntryAuditAnalyses,
} from "../../api/entryAuditApi";

export type HomeHeroHighlight = {
  id: string;
  label: string;
  value: string;
};

function formatCompetencePeriod(period: string): string {
  const [year, month] = period.split("-");
  if (!year || !month) return period;
  const date = new Date(Number(year), Number(month) - 1, 1);
  const label = date.toLocaleDateString("pt-BR", {
    month: "short",
    year: "numeric",
  });
  return label.replace(".", "").replace(/^./, (c) => c.toUpperCase());
}

/**
 * Highlights reais do Início (H1): competência aberta + atenções
 * (altas pendentes da última auditoria). Sem inventar número.
 */
export async function loadHomeHeroHighlights(
  signal?: AbortSignal,
): Promise<HomeHeroHighlight[]> {
  let competenceValue = "Nenhuma competência aberta";
  let attentionValue = "Nenhuma atenção";

  try {
    const competences = await listCompetences({ signal });
    const open = competences
      .filter((item) => item.status === "OPEN")
      .sort((a, b) => b.period.localeCompare(a.period));
    if (open[0]) {
      competenceValue = `${formatCompetencePeriod(open[0].period)} · Aberta`;
    }
  } catch {
    competenceValue = "Competência indisponível";
  }

  try {
    const analyses = await listEntryAuditAnalyses(
      { page_size: 1 },
      signal,
    );
    const latest = analyses.items[0];
    if (latest && ["done", "partial"].includes(latest.status)) {
      const summary = await getEntryAuditSummary(latest.id, {}, signal);
      const highPending = Math.min(summary.kpis.high, summary.kpis.pending);
      const parts: string[] = [];
      if (summary.kpis.high > 0) {
        parts.push(
          `${summary.kpis.high} Alta${summary.kpis.high === 1 ? "" : "s"} na última auditoria`,
        );
      } else if (summary.kpis.pending > 0) {
        parts.push(`${summary.kpis.pending} pendência(s) na última auditoria`);
      }
      if (parts.length) attentionValue = parts.join(" · ");
      else if (highPending === 0) attentionValue = "Nenhuma atenção";
    }
  } catch {
    // Mantém «Nenhuma atenção» se a auditoria não estiver acessível.
  }

  return [
    { id: "competence", label: "Competência", value: competenceValue },
    { id: "attention", label: "Atenções", value: attentionValue },
  ];
}
