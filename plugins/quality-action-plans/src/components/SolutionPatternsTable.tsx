import type { SolutionPattern } from "../types/solutionPattern";
import { formatEffectivenessRate } from "../utils/symptomTags";

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
    <div className="pac-table-wrap">
      <table className="pac-table">
        <thead>
          <tr>
            <th>Título</th>
            <th>Categoria</th>
            <th>Modo de falha</th>
            <th>Eficácia</th>
            <th>Usos</th>
            <th>Ações recomendadas</th>
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
