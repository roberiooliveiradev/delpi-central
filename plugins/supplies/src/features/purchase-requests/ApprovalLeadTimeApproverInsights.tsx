import type { ApprovalApproverStats, ApprovalLeadTimeResponse } from "./approvalLeadTimeApi";
import { SuppliesEmptyState, SuppliesSectionCard } from "../../app/suppliesUi";

type Summary = ApprovalLeadTimeResponse["summary"];

function asNumber(value: number | null | undefined, decimals = 0): string {
  return value == null ? "—" : value.toLocaleString("pt-BR", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

/** Stage timing is an estimate of each approver's queue, not total SC cycle. */
export function ApprovalLeadTimeApproverInsights({
  summary,
  approvers,
}: {
  summary: Summary;
  approvers: ApprovalApproverStats[];
}) {
  const distribution = [
    { label: "Mesmo dia", value: summary.same_day },
    { label: "1 a 2 dias", value: summary.one_to_two_days },
    { label: "3 a 5 dias", value: summary.three_to_five_days },
    { label: "6 a 10 dias", value: summary.six_to_ten_days },
    { label: "Acima de 10 dias", value: summary.over_10_days },
  ];
  // Minimum sample protects the ranking from 1- or 2-event outliers.
  const ranked = approvers
    .filter((row) => row.approvals >= 5 && row.avg_days !== null)
    .sort((a, b) => (b.avg_days ?? 0) - (a.avg_days ?? 0))
    .slice(0, 7);
  const maxAverage = Math.max(1, ...ranked.map((row) => row.avg_days ?? 0));

  return (
    <>
      <div className="sp-approval-lead-time__charts">
        <SuppliesSectionCard title="Distribuição por prazo" hint="Aprovação completa da SC, em dias corridos.">
          <div className="sp-approval-lead-time__buckets">
            {distribution.map((bucket) => {
              const pct = summary.total_requests ? 100 * bucket.value / summary.total_requests : 0;
              return (
                <div key={bucket.label} className="sp-approval-lead-time__bucket">
                  <div className="sp-approval-lead-time__bucket-label">
                    <span>{bucket.label}</span>
                    <strong>{asNumber(bucket.value)} · {asNumber(pct, 1)}%</strong>
                  </div>
                  <div className="sp-approval-lead-time__bar">
                    <div role="img" aria-label={`${bucket.label}: ${asNumber(bucket.value)} SCs, ${asNumber(pct, 1)}%`} style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </SuppliesSectionCard>

        <SuppliesSectionCard
          title="Tempo médio por aprovador"
          hint="Top 7 por maior média, somente quem possui ao menos 5 aprovações comprovadas. Cada nível começa após sua liberação estimada."
        >
          {ranked.length ? (
            <div className="sp-approval-lead-time__ranking">
              {ranked.map((row) => {
                const pct = 100 * (row.avg_days ?? 0) / maxAverage;
                return (
                  <div key={row.approver_code} className="sp-approval-lead-time__bucket">
                    <div className="sp-approval-lead-time__bucket-label">
                      <span className="sp-approval-lead-time__ranking-name" title={row.approver_name}>
                        {row.approver_name}
                        <span className="sp-approval-lead-time__ranking-count"> · {asNumber(row.approvals)} aprovações</span>
                      </span>
                      <strong>{asNumber(row.avg_days, 2)} d</strong>
                    </div>
                    <div className="sp-approval-lead-time__bar sp-approval-lead-time__bar--approver">
                      <div role="img" aria-label={`${row.approver_name}: média ${asNumber(row.avg_days, 2)} dias em ${row.approvals} aprovações`} style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <SuppliesEmptyState title="Sem amostra suficiente" message="É necessário ter pelo menos cinco aprovações comprovadas por pessoa." />
          )}
        </SuppliesSectionCard>
      </div>

      <SuppliesSectionCard
        title="Comparativo de aprovadores"
        hint="Média estimada por evento e nível da SCR, independente do prazo completo da SC. Quantidade de aprovações permite avaliar o tamanho da amostra."
      >
        {!approvers.length ? (
          <SuppliesEmptyState title="Nenhum aprovador no período" message="Não há eventos de aprovação ou pendência comprovados no recorte." />
        ) : (
          <div className="sp-approval-lead-time__table-scroll">
            <table className="sp-approval-lead-time__table">
              <thead>
                <tr>
                  <th>Aprovador</th>
                  <th>Código</th>
                  <th>Aprovações</th>
                  <th>Média por etapa</th>
                  <th>Maior prazo</th>
                  <th>No mesmo dia</th>
                  <th>SCs pendentes</th>
                </tr>
              </thead>
              <tbody>
                {approvers.map((row) => (
                  <tr key={row.approver_code}>
                    <td className="sp-approval-lead-time__name-cell"><strong>{row.approver_name}</strong></td>
                    <td>{row.approver_code}</td>
                    <td>{asNumber(row.approvals)}</td>
                    <td><strong>{row.avg_days == null ? "Sem histórico" : `${asNumber(row.avg_days, 2)} d`}</strong></td>
                    <td>{row.max_days == null ? "—" : `${row.max_days} d`}</td>
                    <td>{asNumber(row.same_day)}</td>
                    <td>{asNumber(row.pending_count)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <p className="sp-approval-lead-time__table-note">
          A média começa no maior entre emissão da SC, registro SCR e término do nível anterior.
          É uma estimativa por data, não o horário exato em que a tarefa apareceu para cada pessoa.
          Reaprovações históricas podem afetar os resultados. O gráfico exige ao menos 5 aprovações;
          a tabela mostra também amostras menores.
        </p>
      </SuppliesSectionCard>
    </>
  );
}
