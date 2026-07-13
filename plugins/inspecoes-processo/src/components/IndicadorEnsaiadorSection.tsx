import { EmptyState } from "./EmptyState";
import type { InspecoesProcessoPorEnsaiadorItem } from "../types/api";
import { formatNumber, formatPercent } from "../utils/format";

type IndicadorEnsaiadorSectionProps = {
  items: InspecoesProcessoPorEnsaiadorItem[];
  loading: boolean;
  error: string | null;
  onRetry: () => void;
};

export function IndicadorEnsaiadorSection({
  items,
  loading,
  error,
  onRetry,
}: IndicadorEnsaiadorSectionProps) {
  return (
    <section className="ip-panel" aria-labelledby="ip-indicador-ensaiador-title">
      <div className="ip-panel__header">
        <h3 id="ip-indicador-ensaiador-title" className="ip-panel__title">
          Indicadores por ensaiador
        </h3>
        <p className="ip-panel__subtitle">Top 10 da filial atual</p>
      </div>

      {loading ? (
        <div className="ip-alert ip-alert--info" role="status" aria-live="polite">
          <p>Carregando indicadores por ensaiador…</p>
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
          title="Sem indicadores por ensaiador"
          description="Não há itens agregados por ensaiador para esta filial."
        />
      ) : null}

      {!loading && !error && items.length > 0 ? (
        <div className="ip-table-wrap">
          <table className="ip-table">
            <thead>
              <tr>
                <th scope="col">#</th>
                <th scope="col">Ensaiador</th>
                <th scope="col">Matrícula</th>
                <th scope="col">Ensaios</th>
                <th scope="col">Ensaios reprovados</th>
                <th scope="col">OPs reprovadas</th>
                <th scope="col">% ensaios reprovados</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item, index) => (
                <tr key={`${item.matricula_ensaiador}-${index}`}>
                  <td>{index + 1}</td>
                  <td className="ip-table__cell--wrap">
                    {item.nome_ensaiador?.trim() || "—"}
                  </td>
                  <td>{item.matricula_ensaiador?.trim() || "—"}</td>
                  <td>{formatNumber(item.qtde_ensaios)}</td>
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
        Indicador agregado por filial. Use para análise operacional e acompanhamento de
        processo, não como avaliação individual isolada.
      </p>
    </section>
  );
}
