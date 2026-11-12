import type { InspecoesProcessoAuditoriaApontamentoItem } from "../types/api";
import { formatIsoDatePt } from "../utils/format";

type AuditoriaTableProps = {
  items: InspecoesProcessoAuditoriaApontamentoItem[];
};

function statusLabel(item: InspecoesProcessoAuditoriaApontamentoItem): string {
  if (item.operador_inspecionou) return "Inspecionou";
  if (item.tem_inspecao_na_op_operacao || item.tem_inspecao_amarrada) {
    return "Não inspecionou";
  }
  return "Não possui inspeção cadastrada";
}

function statusClass(item: InspecoesProcessoAuditoriaApontamentoItem): string {
  if (item.operador_inspecionou) return "ip-status-pill ip-status-pill--ok";
  if (item.tem_inspecao_na_op_operacao || item.tem_inspecao_amarrada) {
    return "ip-status-pill ip-status-pill--pendente";
  }
  return "ip-status-pill ip-status-pill--sem-cadastro";
}

function InspecoesMinimoCell({ item }: { item: InspecoesProcessoAuditoriaApontamentoItem }) {
  const exigivel = item.tem_inspecao_amarrada || item.tem_inspecao_na_op_operacao;
  const quantidade = item.qtd_inspecoes_operador ?? 0;
  const atende = quantidade >= 2;
  const classe = !exigivel && !quantidade
    ? "ip-status-pill--sem-cadastro"
    : atende
      ? "ip-status-pill--ok"
      : "ip-status-pill--pendente";
  const descricao = !exigivel && !quantidade
    ? "Sem exigência"
    : atende
      ? "Mínimo atingido"
      : quantidade === 1
        ? "Falta 1"
        : "Faltam 2";
  return (
    <span
      className={`ip-status-pill ${classe}`}
      title="Sessões do mesmo operador nesta OP e operação, independentemente do dia/turno. Mínimo: 2."
      aria-label={`${quantidade} inspeções, ${descricao.toLowerCase()}`}
    >
      {quantidade} · {descricao}
    </span>
  );
}

export function AuditoriaTable({ items }: AuditoriaTableProps) {
  return (
    <div className="ip-table-wrap">
      <table className="ip-table">
        <thead>
          <tr>
            <th scope="col">Inspeção</th>
            <th scope="col">Operador</th>
            <th scope="col" title="Sessões por operador, OP e operação. Mínimo 2, em toda a OP.">
              Qtd. inspeções (mín. 2)
            </th>
            <th scope="col">OP</th>
            <th scope="col">Produto</th>
            <th scope="col">Descrição</th>
            <th scope="col">Operação</th>
            <th scope="col">CT</th>
            <th scope="col">Turno</th>
            <th scope="col">Data</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr
              key={`${item.filial}-${item.data_producao}-${item.turno ?? "?"}-${item.cod_operador}-${item.op}-${item.operacao}-${item.produto}`}
            >
              <td>
                <span className={statusClass(item)}>{statusLabel(item)}</span>
              </td>
              <td className="ip-table__cell--wrap">
                {item.nome_operador?.trim() || "—"}
              </td>
              <td><InspecoesMinimoCell item={item} /></td>
              <td>{item.op?.trim() || "—"}</td>
              <td>{item.produto?.trim() || "—"}</td>
              <td className="ip-table__cell--wrap">
                {item.descricao_produto?.trim() || "—"}
              </td>
              <td>{item.operacao?.trim() || "—"}</td>
              <td>{item.centro_trabalho?.trim() || "—"}</td>
              <td>{item.turno_label?.trim() || "—"}</td>
              <td>{formatIsoDatePt(item.data_producao)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
