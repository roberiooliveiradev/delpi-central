import { EmptyState } from "./EmptyState";
import type { InspecoesProcessoPorProdutoItem } from "../types/api";
import { formatNumber, formatPercent } from "../utils/format";

type RankingProdutoSectionProps = {
  items: InspecoesProcessoPorProdutoItem[];
  loading: boolean;
  error: string | null;
  onRetry: () => void;
};

export function RankingProdutoSection({
  items,
  loading,
  error,
  onRetry,
}: RankingProdutoSectionProps) {
  return (
    <section className="ip-panel" aria-labelledby="ip-ranking-produto-title">
      <div className="ip-panel__header">
        <h3 id="ip-ranking-produto-title" className="ip-panel__title">
          Produtos com mais reprovações
        </h3>
        <p className="ip-panel__subtitle">Top 10 da filial atual</p>
      </div>

      {loading ? (
        <div className="ip-alert ip-alert--info" role="status" aria-live="polite">
          <p>Carregando ranking por produto…</p>
        </div>
      ) : null}

      {error ? (
        <div className="ip-alert ip-alert--error" role="alert">
          <p>{error}</p>
          <button type="button" className="ip-button" onClick={onRetry}>
            Tentar novamente
          </button>
        </div>
      ) : null}

      {!loading && !error && items.length === 0 ? (
        <EmptyState
          title="Sem produtos no ranking"
          description="Não há itens agregados de ranking por produto para esta filial."
        />
      ) : null}

      {!loading && !error && items.length > 0 ? (
        <div className="ip-table-wrap">
          <table className="ip-table">
            <thead>
              <tr>
                <th scope="col">#</th>
                <th scope="col">Código</th>
                <th scope="col">Descrição</th>
                <th scope="col">Revisão</th>
                <th scope="col">Ensaios reprovados</th>
                <th scope="col">OPs reprovadas</th>
                <th scope="col">% ensaios reprovados</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item, index) => (
                <tr
                  key={`${item.codigo_produto}-${item.revisao_produto}-${index}`}
                >
                  <td>{index + 1}</td>
                  <td>{item.codigo_produto?.trim() || "—"}</td>
                  <td className="ip-table__cell--wrap">
                    {item.descricao_produto?.trim() || "—"}
                  </td>
                  <td>{item.revisao_produto?.trim() || "—"}</td>
                  <td>{formatNumber(item.qtde_ensaios_reprovados)}</td>
                  <td>{formatNumber(item.qtde_ops_reprovadas)}</td>
                  <td>{formatPercent(item.percentual_ensaios_reprovados)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      <p className="ip-muted-note">
        Ranking agregado por produto. O histórico detalhado será carregado somente sob demanda.
      </p>
    </section>
  );
}
