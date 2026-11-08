import { useEffect, useMemo, useState } from "react";
import { fetchInspecoesEntradaNcsFornecedores } from "../api/inspecoesEntradaApi";
import type { FornecedorNc, FornecedoresNcResponse } from "../types/fornecedoresNc";
import { formatNumber, formatText } from "../utils/format";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import { IE_STATE_BOX } from "../ui/stateChrome";

type Props = {
  branch: string;
  refreshToken: number;
  onLoadingChange?: (loading: boolean) => void;
};

function currentMonth(): { start: string; end: string } {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return { start: `${year}-${month}-01`, end: `${year}-${month}-${day}` };
}

function formatDate(value: string | null): string {
  if (!value) return "—";
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    const [year, month, day] = value.split("-");
    return `${day}/${month}/${year}`;
  }
  return value;
}

function statusTone(status: string | null): string {
  if (status === "5" || status === "4") return "neutral";
  if (status === "2") return "warning";
  if (status === "3") return "success";
  return "neutral";
}

export function FornecedoresNcPage({ branch, refreshToken, onLoadingChange }: Props) {
  const [initialPeriod] = useState(currentMonth);
  const [startDate, setStartDate] = useState(initialPeriod.start);
  const [endDate, setEndDate] = useState(initialPeriod.end);
  const [status, setStatus] = useState("");
  const [itemCode, setItemCode] = useState("");
  const [description, setDescription] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [expandedKey, setExpandedKey] = useState<string | null>(null);
  const [data, setData] = useState<FornecedoresNcResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const debouncedItem = useDebouncedValue(itemCode, 350);
  const debouncedDescription = useDebouncedValue(description, 350);

  const filters = useMemo(() => ({
    branch,
    start_date: startDate,
    end_date: endDate,
    status,
    item_code: debouncedItem,
    description: debouncedDescription,
    page,
    page_size: pageSize,
  }), [branch, startDate, endDate, status, debouncedItem, debouncedDescription, page, pageSize]);

  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      try {
        setLoading(true);
        setError(null);
        const result = await fetchInspecoesEntradaNcsFornecedores(filters, controller.signal);
        if (!controller.signal.aborted) setData(result);
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(err instanceof Error ? err.message : "Erro ao carregar NCs de fornecedores.");
          setData(null);
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }
    void load();
    return () => controller.abort();
  }, [filters, refreshToken]);

  useEffect(() => { onLoadingChange?.(loading); }, [loading, onLoadingChange]);
  const total = data?.total ?? 0;
  const totalPages = Math.max(1, data?.total_pages ?? 1);
  const items = data?.items ?? [];

  function updateFilter(setter: (value: string) => void, value: string) {
    setter(value);
    setPage(1);
    setExpandedKey(null);
  }

  function detail(row: FornecedorNc) {
    const fields = [
      ["Fornecedor", [row.supplier_code, row.supplier_store].filter(Boolean).join("/")],
      ["Item", row.item_code],
      ["Descrição detalhada", row.detailed_description],
      ["Prioridade", row.priority_label],
      ["Revisão", row.revision],
      ["Quantidade devolvida", row.returned_quantity === null ? null : formatNumber(row.returned_quantity)],
    ];
    return (
      <div className="ie-nc-detail">
        {fields.map(([label, value]) => (
          <div key={label} className="ie-nc-detail__field">
            <span>{label}</span><strong>{formatText(value)}</strong>
          </div>
        ))}
      </div>
    );
  }

  return (
    <section className="ie-nc-area" aria-label="Não conformidades de fornecedores">
      <div className="ie-card ie-nc-intro">
        <div>
          <h2>Não conformidades de fornecedores</h2>
          <p>Registros do TOTVS Protheus · somente tipo Fornecedor · filial {branch}</p>
        </div>
        <div className="ie-nc-total">{total.toLocaleString("pt-BR")} <span>registros</span></div>
      </div>

      <div className="ie-card ie-nc-filters">
        <label>De
          <input type="date" value={startDate} max={endDate || undefined}
            onChange={(e) => updateFilter(setStartDate, e.target.value)} />
        </label>
        <label>Até
          <input type="date" value={endDate} min={startDate || undefined}
            onChange={(e) => updateFilter(setEndDate, e.target.value)} />
        </label>
        <label>Situação
          <select value={status} onChange={(e) => updateFilter(setStatus, e.target.value)}>
            <option value="">Todas</option>
            <option value="1">Registrada</option>
            <option value="2">Em análise</option>
            <option value="3">Procede</option>
            <option value="4">Não procede</option>
            <option value="5">Cancelada</option>
          </select>
        </label>
        <label>Código do item
          <input value={itemCode} placeholder="Pesquisar item" maxLength={50}
            onChange={(e) => updateFilter(setItemCode, e.target.value)} />
        </label>
        <label>Descrição
          <input value={description} placeholder="Pesquisar descrição" maxLength={160}
            onChange={(e) => updateFilter(setDescription, e.target.value)} />
        </label>
        <button className="ie-btn ie-btn--ghost" type="button" onClick={() => {
          setStartDate(initialPeriod.start); setEndDate(initialPeriod.end);
          setStatus(""); setItemCode(""); setDescription(""); setPage(1); setExpandedKey(null);
        }}>Limpar filtros</button>
      </div>

      {loading ? <div className={IE_STATE_BOX} role="status">Carregando NCs de fornecedores…</div> : null}
      {error ? <div className="ie-alert ie-alert--error" role="alert">
        <p>{error}</p>
      </div> : null}
      {!loading && !error && items.length === 0 ?
        <div className={IE_STATE_BOX}>Nenhuma NC de fornecedor encontrada no período.</div> : null}

      {!error && items.length > 0 ? (
        <div className="ie-card ie-nc-table-card">
          <div className="ie-nc-table-scroll"><table className="ie-nc-table">
            <thead><tr>
              <th>NC</th><th>Ocorrência</th><th>Registro</th><th>Item</th>
              <th>Descrição</th><th>Situação</th><th>Qtd. devolvida</th><th></th>
            </tr></thead>
            <tbody>{items.map((row, index) => {
              const key = `${row.branch}:${row.code}:${row.revision}:${index}`;
              const expanded = expandedKey === key;
              return (
                <tr key={key} className={expanded ? "ie-nc-table__expanded" : undefined}>
                  <td className="ie-cell-mono">{formatText(row.code_display || row.code)}</td>
                  <td>{formatDate(row.occurrence_date)}</td>
                  <td>{formatDate(row.registered_date)}</td>
                  <td className="ie-cell-mono">{formatText(row.item_code)}</td>
                  <td className="ie-nc-table__description" title={row.description || ""}>{formatText(row.description)}</td>
                  <td><span className={`ie-badge ie-badge--${statusTone(row.status_code)}`}>{formatText(row.status_label)}</span></td>
                  <td>{formatNumber(row.returned_quantity)}</td>
                  <td>
                    <button className="ie-btn ie-btn--ghost ie-btn--sm" type="button"
                      aria-expanded={expanded} onClick={() => setExpandedKey(expanded ? null : key)}>
                      {expanded ? "Ocultar" : "Detalhes"}
                    </button>
                    {expanded ? detail(row) : null}
                  </td>
                </tr>
              );
            })}</tbody>
          </table></div>
          <div className="ie-nc-footer">
            <label>Por página
              <select value={pageSize} onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }}>
                <option value={20}>20</option><option value={50}>50</option><option value={100}>100</option>
              </select>
            </label>
            <span>Página {page} de {totalPages}</span>
            <div>
              <button type="button" className="ie-btn ie-btn--ghost ie-btn--sm"
                disabled={page <= 1 || loading} onClick={() => setPage((value) => Math.max(1, value - 1))}>Anterior</button>
              <button type="button" className="ie-btn ie-btn--ghost ie-btn--sm"
                disabled={page >= totalPages || loading} onClick={() => setPage((value) => Math.min(totalPages, value + 1))}>Próxima</button>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
