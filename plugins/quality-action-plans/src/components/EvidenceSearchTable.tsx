import { Eye } from "lucide-react";

import { branchLabel, detailPath } from "../constants/actionPlans";
import type { EvidenceSearchHit } from "../types/evidenceSearch";
import { formatDateTime } from "../utils/format";

type Props = {
  items: EvidenceSearchHit[];
  loading?: boolean;
  emptyMessage?: string;
  onNavigate: (path: string) => void;
};

export function EvidenceSearchTable({ items, loading, emptyMessage, onNavigate }: Props) {
  if (loading) {
    return <p className="pac-muted">Buscando evidências…</p>;
  }

  if (!items.length) {
    return <p className="pac-muted">{emptyMessage ?? "Nenhuma evidência encontrada."}</p>;
  }

  return (
    <div className="pac-table-wrap">
      <table className="pac-table">
        <thead>
          <tr>
            <th>Arquivo</th>
            <th>Plano</th>
            <th>Filial</th>
            <th>Produto</th>
            <th>Seção</th>
            <th>Descrição</th>
            <th>Enviado em</th>
            <th aria-label="Ações" />
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id}>
              <td>{item.file_name ?? item.stored_name ?? "—"}</td>
              <td>{item.plan_code ?? "—"}</td>
              <td>{branchLabel(item.branch_code)}</td>
              <td>{item.product_code ?? "—"}</td>
              <td>{item.section ?? "—"}</td>
              <td>{item.description ?? item.text_excerpt ?? "—"}</td>
              <td>{formatDateTime(item.created_at)}</td>
              <td>
                <button
                  type="button"
                  className="pac-icon-btn"
                  title="Abrir plano"
                  onClick={() => onNavigate(detailPath(item.plan_id))}
                >
                  <Eye size={16} aria-hidden />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
