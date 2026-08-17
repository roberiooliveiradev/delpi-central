import type { PersonnelPlan, PersonnelPlanLine } from "../types/budgetPlanning";
import { HEADCOUNT_COLUMNS } from "../utils/personnelPlans";
import { SectionCard } from "./uiKit";

export function PersonnelLinesReadOnly({
  lines,
  totals,
}: {
  lines: PersonnelPlanLine[];
  totals?: PersonnelPlan["totals"] | null;
}) {
  const active = lines.filter((ln) => ln.is_active !== false);
  return (
    <SectionCard title="Linhas de headcount" hint="Visualização somente leitura.">
      {!active.length ? (
        <p className="po-muted">Nenhuma linha ativa neste orçamento.</p>
      ) : (
        <div className="po-table-wrap">
          <table className="po-table">
            <thead>
              <tr>
                <th>Cargo</th>
                {HEADCOUNT_COLUMNS.map((col) => (
                  <th key={col.field}>{col.label}</th>
                ))}
                <th>Observações</th>
              </tr>
            </thead>
            <tbody>
              {active.map((line) => (
                <tr key={line.id}>
                  <td>{line.position_name}</td>
                  {HEADCOUNT_COLUMNS.map((col) => (
                    <td key={col.field}>{line[col.field] ?? "—"}</td>
                  ))}
                  <td>{line.observations?.trim() || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {totals ? (
        <dl className="po-detail-grid po-approval-personnel-totals">
          {HEADCOUNT_COLUMNS.map((col) => (
            <div key={col.field}>
              <dt>Total {col.label}</dt>
              <dd>{totals[col.field] ?? 0}</dd>
            </div>
          ))}
        </dl>
      ) : null}
    </SectionCard>
  );
}
