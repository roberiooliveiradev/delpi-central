import { useEffect, useMemo, useRef, useState } from "react";
import { FilePlus2, Inbox, SearchX } from "lucide-react";
import { useLnfPermissions } from "../../application/useLnfPermissions";
import { branchLabel, type BranchCode } from "../../constants/branch";
import { ApiError } from "../../data/api/httpClient";
import * as api from "../../data/api/invoicePostingApi";
import type { InvoicePostingRequest, ListFilters } from "../../domain/types";
import { RequestFilters } from "../components/RequestFilters";
import { LnfPageHeader } from "../components/LnfPageHeader";
import { StatusBadge } from "../components/StatusBadge";
import {
  formatDate,
  formatDateTime,
  formatDocument,
  formatMoney,
  hasActiveFilters,
} from "../format";

type Props = {
  branch: BranchCode;
  highlightId?: string;
  onCreate: () => void;
  onOpen: (requestId: string) => void;
};

function defaultFilters(branch: BranchCode): ListFilters {
  return { page: 1, page_size: 20, status: "pending", branch };
}

type SyncState = "idle" | "checking" | "updated" | "unavailable";

function oldestIds(items: InvoicePostingRequest[], count = 3): Set<string> {
  const sorted = [...items].sort((a, b) =>
    String(a.received_at).localeCompare(String(b.received_at)),
  );
  return new Set(sorted.slice(0, Math.min(count, sorted.length)).map((r) => r.id));
}

export function QueuePage({ branch, highlightId, onCreate, onOpen }: Props) {
  const perms = useLnfPermissions();
  const [filters, setFilters] = useState<ListFilters>(() => defaultFilters(branch));
  const [debounced, setDebounced] = useState<ListFilters>(() =>
    defaultFilters(branch),
  );
  const [items, setItems] = useState<InvoicePostingRequest[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);
  const [syncState, setSyncState] = useState<SyncState>("idle");
  const [syncNotice, setSyncNotice] = useState<string | null>(null);
  const [listLoadedAt, setListLoadedAt] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const refreshStartedRef = useRef(false);
  const mountedRef = useRef(true);
  const debouncedRef = useRef(debounced);

  useEffect(() => {
    const next = defaultFilters(branch);
    setFilters(next);
    setDebounced(next);
    refreshStartedRef.current = false;
  }, [branch]);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    debouncedRef.current = debounced;
  }, [debounced]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setDebounced({
        ...filters,
        supplier: filters.supplier?.trim() || undefined,
        document: filters.document?.trim() || undefined,
      });
    }, 350);
    return () => window.clearTimeout(timer);
  }, [filters]);

  useEffect(() => {
    if (perms.loading) return;
    if (!perms.canRead) {
      setForbidden(true);
      setLoading(false);
      setError("Você não tem permissão para consultar solicitações.");
      return;
    }
    setForbidden(false);
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setLoading(true);
    setError(null);
    api
      .listRequests(debounced, controller.signal)
      .then((data) => {
        setItems(data.items ?? []);
        setTotal(data.total ?? 0);
        setTotalPages(data.total_pages ?? 0);
        setListLoadedAt(new Date().toISOString());
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        if (err instanceof ApiError && err.status === 403) {
          setForbidden(true);
          setError(err.message);
        } else {
          setError(err instanceof Error ? err.message : "Falha ao carregar a fila.");
        }
        setItems([]);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [debounced, perms.loading, perms.canRead]);

  useEffect(() => {
    if (perms.loading || !perms.canRead || refreshStartedRef.current) return;
    refreshStartedRef.current = true;
    let cancelled = false;
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), 45_000);
    setSyncState("checking");
    setSyncNotice(null);

    void (async () => {
      try {
        const result = await api.refreshReconciliation(controller.signal);
        if (!mountedRef.current || cancelled) return;

        if (result.status === "completed" && result.updated > 0) {
          const data = await api.listRequests(debouncedRef.current, controller.signal);
          if (!mountedRef.current || cancelled) return;
          setItems(data.items ?? []);
          setTotal(data.total ?? 0);
          setTotalPages(data.total_pages ?? 0);
          setListLoadedAt(new Date().toISOString());
          setSyncState("updated");
          setSyncNotice(
            result.updated === 1
              ? "1 solicitação atualizada com o Protheus."
              : `${result.updated} solicitações atualizadas com o Protheus.`,
          );
        } else if (result.status === "failed") {
          setSyncState("unavailable");
          setSyncNotice(
            "Não foi possível verificar lançamentos no Protheus agora. A fila permanece disponível.",
          );
        } else {
          setSyncState("updated");
        }
      } catch (err: unknown) {
        if (!mountedRef.current || cancelled) return;
        if (err instanceof ApiError && err.status === 403) {
          setSyncState("idle");
          return;
        }
        setSyncState("unavailable");
        setSyncNotice(
          "Não foi possível verificar lançamentos no Protheus agora. A fila permanece disponível.",
        );
      } finally {
        window.clearTimeout(timeoutId);
      }
    })();

    return () => {
      cancelled = true;
      window.clearTimeout(timeoutId);
      controller.abort();
    };
  }, [perms.loading, perms.canRead]);

  const page = debounced.page ?? 1;
  const filterDefaults = { branch, status: "pending" as const };
  const filtersActive = hasActiveFilters(debounced, filterDefaults);
  const aging = useMemo(() => oldestIds(items), [items]);
  const resetFilters = () => setFilters(defaultFilters(branch));

  const syncLabel =
    syncState === "checking"
      ? "Verificando…"
      : syncState === "unavailable"
        ? "Não disponível"
        : syncState === "updated"
          ? "Atualizada"
          : null;

  return (
    <div className="lnf-stack" data-testid="queue-page">
      <LnfPageHeader
        title="Lançamento de Notas Fiscais"
        subtitle={`Fila · ${branchLabel(branch)} · por ordem de recebimento físico.`}
        meta={
          listLoadedAt
            ? `Fila carregada em ${formatDateTime(listLoadedAt)}`
            : undefined
        }
        actions={
          perms.canCreate ? (
            <button
              type="button"
              className="lnf-btn lnf-btn--primary"
              onClick={onCreate}
              data-testid="btn-new-request"
            >
              <FilePlus2 size={16} aria-hidden />
              Nova solicitação
            </button>
          ) : null
        }
      />

      <div className="lnf-context-bar" data-testid="queue-context-bar" aria-live="polite">
        <span>
          <strong>{total}</strong> encontrada(s) nos filtros atuais
        </span>
        <span className="lnf-context-bar__sep" aria-hidden>
          ·
        </span>
        <span>Mais antigas primeiro</span>
        {syncLabel ? (
          <>
            <span className="lnf-context-bar__sep" aria-hidden>
              ·
            </span>
            <span
              className={`lnf-sync-chip lnf-sync-chip--${syncState}`}
              data-testid="queue-syncing"
            >
              {syncState === "checking"
                ? "Verificando lançamentos no Protheus…"
                : `Conciliação: ${syncLabel}`}
            </span>
          </>
        ) : null}
      </div>

      <RequestFilters
        value={filters}
        lockedBranch={branch}
        onChange={setFilters}
        onClear={resetFilters}
      />

      <section className="lnf-card lnf-queue-panel">
        {syncNotice ? (
          <p className="lnf-sync-notice" data-testid="queue-sync-notice">
            {syncNotice}
          </p>
        ) : null}

        {loading ? <p data-testid="queue-loading">Carregando fila…</p> : null}
        {error ? (
          <p className="lnf-error" role="alert" data-testid="queue-error">
            {error}
          </p>
        ) : null}

        {!loading && !error && items.length === 0 ? (
          <div className="lnf-empty" data-testid="queue-empty">
            {filtersActive ? (
              <>
                <SearchX size={28} aria-hidden />
                <h2>Nenhuma solicitação encontrada</h2>
                <p className="lnf-muted">
                  Os filtros atuais não retornaram resultados. Ajuste ou limpe os
                  filtros para ver a fila novamente.
                </p>
                <button
                  type="button"
                  className="lnf-btn lnf-btn--ghost"
                  onClick={resetFilters}
                  data-testid="btn-clear-empty-filters"
                >
                  Limpar filtros
                </button>
              </>
            ) : (
              <>
                <Inbox size={28} aria-hidden />
                <h2>Nenhuma solicitação cadastrada</h2>
                <p className="lnf-muted">
                  Cadastre o recebimento físico da nota para iniciar o fluxo de
                  lançamento no Protheus.
                </p>
                {perms.canCreate ? (
                  <button
                    type="button"
                    className="lnf-btn lnf-btn--primary"
                    onClick={onCreate}
                    data-testid="btn-empty-create"
                  >
                    Criar primeira solicitação
                  </button>
                ) : null}
              </>
            )}
          </div>
        ) : null}

        {!loading && items.length > 0 ? (
          <>
            <div className="lnf-table-wrap lnf-queue-desktop">
              <table className="lnf-table">
                <thead>
                  <tr>
                    <th>Recebimento</th>
                    <th>Filial</th>
                    <th>Nota</th>
                    <th>Fornecedor</th>
                    <th>Emissão</th>
                    <th>Valor</th>
                    <th>Status</th>
                    <th>Responsável</th>
                    <th>Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((row) => (
                    <tr
                      key={row.id}
                      className={[
                        highlightId === row.id ? "lnf-row--highlight" : "",
                        aging.has(row.id) ? "lnf-row--aging" : "",
                        "lnf-row--clickable",
                      ]
                        .filter(Boolean)
                        .join(" ")}
                      data-testid={`queue-row-${row.id}`}
                      tabIndex={0}
                      onClick={() => onOpen(row.id)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault();
                          onOpen(row.id);
                        }
                      }}
                    >
                      <td>{formatDateTime(row.received_at)}</td>
                      <td>{row.branch_code}</td>
                      <td className="lnf-cell-strong">
                        {formatDocument(row.document_number, row.series)}
                      </td>
                      <td>
                        <div className="lnf-cell-strong">{row.supplier_name}</div>
                        <div className="lnf-muted lnf-cell-sub">
                          {row.supplier_code}/{row.supplier_store}
                        </div>
                      </td>
                      <td>{formatDate(row.issue_date)}</td>
                      <td className="lnf-cell-num">{formatMoney(Number(row.amount))}</td>
                      <td>
                        <StatusBadge status={row.status} />
                      </td>
                      <td>{row.assignee_name || "—"}</td>
                      <td>
                        <button
                          type="button"
                          className="lnf-btn lnf-btn--ghost lnf-btn--sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            onOpen(row.id);
                          }}
                        >
                          Detalhes
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <ul className="lnf-queue-cards" data-testid="queue-cards">
              {items.map((row) => (
                <li
                  key={row.id}
                  className={[
                    "lnf-queue-card",
                    aging.has(row.id) ? "lnf-row--aging" : "",
                    highlightId === row.id ? "lnf-row--highlight" : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                >
                  <button
                    type="button"
                    className="lnf-queue-card__body"
                    onClick={() => onOpen(row.id)}
                  >
                    <div className="lnf-queue-card__top">
                      <strong>{formatDocument(row.document_number, row.series)}</strong>
                      <StatusBadge status={row.status} />
                    </div>
                    <div className="lnf-cell-strong">{row.supplier_name}</div>
                    <div className="lnf-muted lnf-cell-sub">
                      {row.supplier_code}/{row.supplier_store} · Filial {row.branch_code}
                    </div>
                    <div className="lnf-queue-card__meta">
                      <span>Recebido {formatDateTime(row.received_at)}</span>
                      <span>{formatMoney(Number(row.amount))}</span>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          </>
        ) : null}

        {!forbidden && totalPages > 1 ? (
          <div className="lnf-pagination">
            <button
              type="button"
              className="lnf-btn lnf-btn--ghost lnf-btn--sm"
              disabled={page <= 1 || loading}
              onClick={() => setFilters((f) => ({ ...f, page: page - 1 }))}
            >
              Anterior
            </button>
            <span className="lnf-muted">
              Página {page} de {totalPages}
            </span>
            <button
              type="button"
              className="lnf-btn lnf-btn--ghost lnf-btn--sm"
              disabled={page >= totalPages || loading}
              onClick={() => setFilters((f) => ({ ...f, page: page + 1 }))}
            >
              Próxima
            </button>
          </div>
        ) : null}
      </section>
    </div>
  );
}
