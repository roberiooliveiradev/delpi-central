import type { InspecoesProcessoAuditoriaApontamentoItem } from "../types/api";
import { formatIsoDatePt } from "../utils/format";

type AuditoriaTableProps = {
  items: InspecoesProcessoAuditoriaApontamentoItem[];
};

function statusLabel(item: InspecoesProcessoAuditoriaApontamentoItem): string {
  if (item.operador_inspecionou) return "Inspecionou";
  if (item.tem_inspecao_na_op_operacao) {
    return "Não (outra pessoa)";
  }
  return "Não inspecionou";
}

function statusClass(item: InspecoesProcessoAuditoriaApontamentoItem): string {
  if (item.operador_inspecionou) return "ip-status-pill ip-status-pill--ok";
  return "ip-status-pill ip-status-pill--pendente";
}

export function AuditoriaTable({ items }: AuditoriaTableProps) {
  return (
    <div className="ip-table-wrap">
      <table className="ip-table">
        <thead>
          <tr>
            <th scope="col">Inspeção</th>
            <th scope="col">Operador</th>
            <th scope="col">OP</th>
            <th scope="col">Produto</th>
            <th scope="col">Descrição</th>
            <th scope="col">Operação</th>
            <th scope="col">CT</th>
            <th scope="col">Data</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr
              key={`${item.cod_operador}-${item.op}-${item.operacao}-${item.produto}`}
            >
              <td>
                <span className={statusClass(item)}>{statusLabel(item)}</span>
              </td>
              <td className="ip-table__cell--wrap">
                {item.nome_operador?.trim() || "—"}
              </td>
              <td>{item.op?.trim() || "—"}</td>
              <td>{item.produto?.trim() || "—"}</td>
              <td className="ip-table__cell--wrap">
                {item.descricao_produto?.trim() || "—"}
              </td>
              <td>{item.operacao?.trim() || "—"}</td>
              <td>{item.centro_trabalho?.trim() || "—"}</td>
              <td>{formatIsoDatePt(item.data_producao)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
