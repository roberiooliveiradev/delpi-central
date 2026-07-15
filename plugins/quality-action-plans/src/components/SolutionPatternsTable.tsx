import { TableHeaderCell } from "./ui/TableHeaderCell";
import { PAC_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { SolutionPattern } from "../types/solutionPattern";
import { formatEffectivenessRate } from "../utils/symptomTags";
import { PAC_TABLE } from "./ui/tableChrome";

const T = PAC_HELP_TOOLTIPS.tables;

type Props = {
  items: SolutionPattern[];
  loading?: boolean;
  emptyMessage?: string;
};

export function SolutionPatternsTable({ items, loading, emptyMessage }: Props) {
  if (loading) {
    return <p className="pac-muted">Carregando padrões…</p>;
  }

  if (!items.length) {
    return <p className="pac-muted">{emptyMessage ?? "Nenhum padrão cadastrado."}</p>;
  }

  return (
    <div className={PAC_TABLE.wrap}>
      <table className={PAC_TABLE.table}>
        <thead>
          <tr>
            <TableHeaderCell label="Título" hint={T.title} />
            <TableHeaderCell label="Categoria" hint={T.category} />
            <TableHeaderCell label="Modo de falha" hint={T.failureMode} />
            <TableHeaderCell label="Eficácia" hint={T.effectiveness} />
            <TableHeaderCell label="Usos" hint={T.usageCount} />
            <TableHeaderCell label="Ações recomendadas" hint={T.recommendedActions} />
          </tr>
        </thead>
        <tbody>
          {items.map((pattern) => (
            <tr key={pattern.id}>
              <td>{pattern.title}</td>
              <td>{pattern.problem_category ?? "—"}</td>
              <td>{pattern.failure_mode ?? "—"}</td>
              <td>{formatEffectivenessRate(pattern.effectiveness_rate)}</td>
              <td>{pattern.usage_count}</td>
              <td>
                <ul className="pac-inline-list">
                  {pattern.recommended_actions.slice(0, 3).map((action) => (
                    <li key={action}>{action}</li>
                  ))}
                  {pattern.recommended_actions.length > 3 ? (
                    <li className="pac-muted">+{pattern.recommended_actions.length - 3} mais</li>
                  ) : null}
                </ul>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
