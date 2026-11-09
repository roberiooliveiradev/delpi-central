import { DataTable, type DataTableColumn } from "./DataTable";
import type { NcOperatorRankingResponse } from "../types/nonconformity";

type OperatorRankingRow = NcOperatorRankingResponse["ranking"][number] & { position: number };

type Props = {
  data: NcOperatorRankingResponse | null;
  loading: boolean;
  error: string | null;
  operatorCode: string;
  onOperatorChange: (value: string) => void;
  onRetry: () => void;
};

const formatCount = (value: number) => new Intl.NumberFormat("pt-BR").format(value);

export function NcOperatorRanking({
  data,
  loading,
  error,
  operatorCode,
  onOperatorChange,
  onRetry,
}: Props) {
  const selectedCode = data?.detail?.operator_code ?? "";
  const selected = data?.detail;
  const rankingRows: OperatorRankingRow[] = (data?.ranking ?? []).map((item, index) => ({
    ...item,
    position: index + 1,
  }));
  const rankingColumns: DataTableColumn<OperatorRankingRow>[] = [
    {
      key: "position",
      header: "#",
      render: (row) => `${row.position}º`,
    },
    {
      key: "operator_name",
      header: "Operador",
      interactive: true,
      render: (row) => (
        <button
          type="button"
          onClick={() => onOperatorChange(row.operator_code)}
          aria-pressed={selectedCode === row.operator_code}
          className="dq-nc-operators__operator-button"
        >
          {row.operator_name}
        </button>
      ),
    },
    {
      key: "total_ncs",
      header: "Total de NCs",
      align: "right",
      className: "dq-nc-operators__number",
      render: (row) => formatCount(row.total_ncs),
    },
    {
      key: "main_defect",
      header: "Principal defeito",
      render: (row) => row.main_defect,
    },
  ];

  return (
    <section className="dq-nc-operators dq-card" aria-label="Operadores com mais não conformidades" aria-busy={loading}>
      <header className="dq-nc-operators__header">
        <div>
          <h2>Top 5 operadores com mais NCs</h2>
          <p>Quantidade de ocorrências por operador no período selecionado.</p>
        </div>
        <label className="dq-nc-operators__select">
          <span>Operador</span>
          <select
            value={operatorCode && data?.operators.some((o) => o.operator_code === operatorCode) ? operatorCode : selectedCode}
            onChange={(event) => onOperatorChange(event.target.value)}
            disabled={loading || !data?.operators.length}
            aria-label="Selecionar operador para detalhar as não conformidades"
          >
            {(data?.operators ?? []).map((item) => (
              <option key={item.operator_code} value={item.operator_code}>
                {item.operator_name}
              </option>
            ))}
          </select>
        </label>
      </header>

      {error ? (
        <div role="alert" className="dq-nc-operators__error">
          <span>{error}</span>
          <button type="button" onClick={onRetry}>Tentar novamente</button>
        </div>
      ) : null}

      {!error && !loading && !data?.ranking.length ? (
        <p className="dq-nc-operators__empty">
          Nenhum registro de NC com operador informado para os filtros atuais.
        </p>
      ) : null}

      {(loading && !data) ? (
        <p role="status" className="dq-nc-operators__empty">Carregando análise dos operadores…</p>
      ) : null}

      {data?.ranking.length ? (
        <div className="dq-nc-operators__layout">
          <div className="dq-nc-operators__ranking">
            <DataTable
              columns={rankingColumns}
              rows={rankingRows}
              rowKey={(row) => row.operator_code}
              layout="section"
              getRowClassName={(row) =>
                selectedCode === row.operator_code ? "dq-nc-operators__active" : undefined
              }
            />
          </div>
          <div className="dq-nc-operators__detail">
            <div className="dq-nc-operators__metrics">
              <div><span>NCs do operador</span><strong>{selected ? formatCount(selected.total_ncs) : "—"}</strong></div>
              <div><span>Tipos de defeito</span><strong>{selected ? formatCount(selected.defect_types_count) : "—"}</strong></div>
            </div>
            <h3>Tipos de NC {selected ? `de ${selected.operator_name}` : ""}</h3>
            <div className="dq-nc-operators__defects" aria-live="polite">
              {selected?.defects.map((item) => (
                <div className="dq-nc-operators__defect" key={item.description}>
                  <span title={item.description}>{item.description}</span>
                  <strong>{formatCount(item.count)}</strong>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
