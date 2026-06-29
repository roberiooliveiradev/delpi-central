import { useEffect, useState } from "react";

import { fetchPlanSimilarCases } from "../api/actionPlansApi";
import { StateAlert } from "./StateAlert";
import { SectionCard } from "./ui/SectionCard";
import type { PlanSimilarCasesResult } from "../types/similarCases";
import { detailPath } from "../constants/actionPlans";
import { PAC_HELP_TOOLTIPS } from "../content/helpTooltips";
import { formatDate } from "../utils/format";
import { TableHeaderCell } from "./ui/HelpTooltip";

const T = PAC_HELP_TOOLTIPS.tables;

type Props = {
  planId: string;
  onNavigate: (path: string) => void;
};

export function SimilarCasesPanel({ planId, onNavigate }: Props) {
  const [data, setData] = useState<PlanSimilarCasesResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    void fetchPlanSimilarCases(planId)
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Erro ao carregar casos similares.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [planId]);

  const cases = data?.similar_cases ?? [];
  const recurrence = data?.recurrence_signals;

  return (
    <SectionCard title="Casos similares" hint={PAC_HELP_TOOLTIPS.sections.similarCases}>
      {loading ? <p className="pac-muted">Buscando histórico…</p> : null}
      {error ? <StateAlert variant="error">{error}</StateAlert> : null}
      {!loading && !error && cases.length === 0 ? (
        <p className="pac-muted">Nenhum caso semelhante encontrado no histórico indexado.</p>
      ) : null}
      {recurrence && (recurrence.same_product > 0 || recurrence.same_symptom > 0) ? (
        <p className="pac-muted pac-similar-recurrence">
          Recorrência: {recurrence.same_product} mesmo produto · {recurrence.same_symptom} sintoma
          semelhante
        </p>
      ) : null}
      {cases.length > 0 ? (
        <div className="pac-table-wrap">
          <table className="pac-table pac-table--compact">
            <thead>
              <tr>
                <TableHeaderCell label="Plano" hint={T.planRef} />
                <TableHeaderCell label="Score" hint={T.similarityScore} />
                <TableHeaderCell label="Produto" hint={T.product} />
                <TableHeaderCell label="Resumo" hint={T.summary} />
                <TableHeaderCell label="Eficácia" hint={T.effectivenessStatus} />
              </tr>
            </thead>
            <tbody>
              {cases.map((item) => (
                <tr key={item.plan_uuid ?? item.plan_id}>
                  <td>
                    {item.plan_uuid ? (
                      <button
                        type="button"
                        className="pac-link-btn"
                        onClick={() => onNavigate(detailPath(item.plan_uuid!))}
                      >
                        {item.plan_id}
                      </button>
                    ) : (
                      item.plan_id
                    )}
                  </td>
                  <td>{Math.round(item.similarity_score * 100)}%</td>
                  <td>{item.product_code ?? "—"}</td>
                  <td>{item.problem_summary ?? "—"}</td>
                  <td>
                    {item.effectiveness_status ?? "—"}
                    {item.closed_at ? ` · ${formatDate(item.closed_at)}` : ""}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
      {data?.suggested_focus_areas?.length ? (
        <div className="pac-similar-focus">
          <strong>Focos sugeridos:</strong>
          <ul>
            {data.suggested_focus_areas.map((area) => (
              <li key={area}>{area}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </SectionCard>
  );
}
