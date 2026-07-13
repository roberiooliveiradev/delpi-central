import type { InspecoesProcessoHistoricoItem } from "../types/api";
import { formatIsoDatePt, formatNumber } from "../utils/format";

type HistoricoTableProps = {
  items: InspecoesProcessoHistoricoItem[];
  onViewDetail: (item: InspecoesProcessoHistoricoItem) => void;
};

function formatUltimaMedicao(item: InspecoesProcessoHistoricoItem): string {
  const date = formatIsoDatePt(item.ultima_data_medicao);
  const time = item.ultima_hora_medicao?.trim();
  if (date === "—" && !time) return "—";
  if (date === "—") return time || "—";
  return time ? `${date} ${time}` : date;
}

export function HistoricoTable({ items, onViewDetail }: HistoricoTableProps) {
  return (
    <div className="ip-table-wrap">
      <table className="ip-table">
        <thead>
          <tr>
            <th scope="col">OP</th>
            <th scope="col">Produto</th>
            <th scope="col">Descrição</th>
            <th scope="col">Resultado</th>
            <th scope="col">Ensaios</th>
            <th scope="col">Reprovados</th>
            <th scope="col">Operações</th>
            <th scope="col">Último ensaiador</th>
            <th scope="col">Última medição</th>
            <th scope="col">Ação</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={`${item.ordem_producao}-${item.chave_cabecalho_inspecao}`}>
              <td>{item.ordem_producao?.trim() || "—"}</td>
              <td>{item.codigo_produto?.trim() || "—"}</td>
              <td className="ip-table__cell--wrap">
                {item.descricao_produto?.trim() || "—"}
              </td>
              <td>
                {item.resultado_inspecao?.trim() ||
                  item.resultado_inspecao_codigo?.trim() ||
                  "—"}
              </td>
              <td>{formatNumber(item.qtde_ensaios)}</td>
              <td>{formatNumber(item.qtde_ensaios_reprovados)}</td>
              <td>{formatNumber(item.qtde_operacoes)}</td>
              <td className="ip-table__cell--wrap">
                {item.nome_ultimo_ensaiador?.trim() || "—"}
              </td>
              <td>{formatUltimaMedicao(item)}</td>
              <td>
                <button
                  type="button"
                  className="ip-button ip-button--sm"
                  onClick={() => onViewDetail(item)}
                  disabled={!item.ordem_producao?.trim()}
                >
                  Ver detalhe
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
