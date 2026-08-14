import { useEffect, useRef, useState } from "react";
import { FilePlus2, Inbox } from "lucide-react";
import { useIssuancePermissions } from "../../application/useIssuancePermissions";
import { branchLabel, type BranchCode } from "../../constants/branch";
import { invoiceTypeLabel, statusTone } from "../../domain/status";
import { ApiError } from "../../data/api/httpClient";
import * as api from "../../data/api/invoiceIssuanceApi";
import type { IssuanceRequest, ListFilters } from "../../domain/types";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { firstGivenName, formatDateTime, formatMoney } from "../format";

type Props = {
  branch: BranchCode;
  highlightId?: string;
  onCreate: () => void;
  onOpen: (requestId: string) => void;
};

function defaultFilters(branch: BranchCode): ListFilters {
  return { page: 1, page_size: 20, status: "open", branch };
}

export function QueuePage({ branch, highlightId, onCreate, onOpen }: Props) {
  const perms = useIssuancePermissions();
  const [filters, setFilters] = useState<ListFilters>(() => defaultFilters(branch));
  const [items, setItems] = useState<IssuanceRequest[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    setFilters(defaultFilters(branch));
  }, [branch]);

  useEffect(() => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setLoading(true);
    setError(null);
    api
      .listRequests(filters, controller.signal)
      .then((data) => {
        setItems(data.items);
        setTotal(data.total);
      })
      .catch((err: unknown) => {
        if ((err as { name?: string }).name === "AbortError") return;
        setError(err instanceof ApiError ? err.message : "Falha ao carregar a fila.");
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [filters]);

  return (
    <div className="ii-stack" data-testid="queue-page">
      <PageHeader
        title={`Solicitações de emissão — ${branchLabel(branch)}`}
        subtitle={`${total} registro(s)`}
        actions={
          perms.canCreate ? (
            <button type="button" className="ii-btn ii-btn--primary" onClick={onCreate}>
              <FilePlus2 size={16} /> Nova solicitação
            </button>
          ) : null
        }
      />

      <div className="ii-filters">
        <label>
          Status
          <select
            value={filters.status ?? "open"}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                page: 1,
                status: event.target.value,
              }))
            }
          >
            <option value="open">Em aberto</option>
            <option value="pending">Aguardando atendimento</option>
            <option value="in_progress">Em atendimento</option>
            <option value="issued">Emitida</option>
            <option value="returned">Devolvida</option>
            <option value="cancelled">Cancelada</option>
          </select>
        </label>
        <label>
          Tipo
          <select
            value={filters.invoice_type ?? ""}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                page: 1,
                invoice_type: event.target.value || undefined,
              }))
            }
          >
            <option value="">Todos</option>
            <option value="sale">Venda</option>
            <option value="return">Devolução</option>
            <option value="sample">Amostra</option>
            <option value="repair_shipment">Remessa ou retorno de conserto</option>
            <option value="other">Outros</option>
          </select>
        </label>
        <label>
          Destinatário
          <input
            type="search"
            placeholder="Nome ou código"
            value={filters.q ?? ""}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                page: 1,
                q: event.target.value.trim() || undefined,
              }))
            }
          />
        </label>
      </div>

      {error ? (
        <div className="ii-alert ii-error" role="alert">
          {error}
        </div>
      ) : null}

      {loading ? <p className="ii-muted">Carregando…</p> : null}

      {!loading && items.length === 0 ? (
        <div className="ii-empty">
          <Inbox size={28} />
          <h2>Nenhuma solicitação nesta fila</h2>
        </div>
      ) : (
        <div className="ii-table-wrap">
          <table className="ii-table">
            <thead>
              <tr>
                <th>Data</th>
                <th>Solicitante</th>
                <th>Destinatário</th>
                <th>Tipo</th>
                <th>Itens</th>
                <th>Valor</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr
                  key={row.id}
                  className={[
                    highlightId === row.id ? "ii-row--highlight" : "",
                    `ii-row--status-${statusTone(row.status)}`,
                    "ii-row--clickable",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                  onClick={() => onOpen(row.id)}
                >
                  <td>{formatDateTime(row.created_at)}</td>
                  <td data-testid="queue-requester">{firstGivenName(row.created_by_name)}</td>
                  <td>
                    <div className="ii-cell-strong">{row.party_name}</div>
                    <div className="ii-cell-sub">
                      {row.party_code}/{row.party_store}
                    </div>
                  </td>
                  <td>{invoiceTypeLabel(row.invoice_type)}</td>
                  <td>{row.items_count ?? row.items?.length ?? 0}</td>
                  <td className="ii-cell-num">{formatMoney(row.total_amount)}</td>
                  <td>
                    <StatusBadge status={row.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
