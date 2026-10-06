import { useEffect, useState } from "react";
import { SearchX } from "lucide-react";
import { useLnfPermissions } from "../../application/useLnfPermissions";
import { branchLabel } from "../../constants/branch";
import { helpTooltips } from "../../content/helpTooltips";
import { ApiError } from "../../data/api/httpClient";
import * as api from "../../data/api/invoicePostingApi";
import type {
  UnmappedProductFilters,
  UnmappedSupplierProduct,
} from "../../domain/types";
import { LnfPageHeader } from "../components/LnfPageHeader";
import { formatDateTime, formatDocument } from "../format";

function readRequestId(): string {
  if (typeof window === "undefined") return "";
  try {
    return new URLSearchParams(window.location.search).get("requestId")?.trim() ?? "";
  } catch {
    return "";
  }
}

function requestHref(row: UnmappedSupplierProduct): string {
  const filial = row.branch_code === "02" ? "filial-02" : "filial-01";
  return `/apps/lancamento-notas-fiscais/${filial}?requestId=${encodeURIComponent(row.request_id)}`;
}

function statusLabel(status: UnmappedSupplierProduct["mapping_status"]): string {
  return status === "ambiguous" ? "Ambíguo" : "Sem vínculo";
}

function quantityLabel(row: UnmappedSupplierProduct): string {
  const quantity = String(row.quantity ?? "").trim();
  const unit = String(row.unit ?? "").trim();
  if (!quantity) return "—";
  return unit ? `${quantity} ${unit}` : quantity;
}

const EMPTY_FILTERS: UnmappedProductFilters = {
  page: 1,
  page_size: 20,
  supplier: "",
  product_code: "",
  branch: "",
  mapping_status: "",
};

export function UnmappedProductsPage() {
  const perms = useLnfPermissions();
  const [requestId, setRequestId] = useState(readRequestId);
  const [filters, setFilters] = useState<UnmappedProductFilters>(EMPTY_FILTERS);
  const [debounced, setDebounced] = useState<UnmappedProductFilters>(EMPTY_FILTERS);
  const [items, setItems] = useState<UnmappedSupplierProduct[]>([]);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setDebounced({
        ...filters,
        supplier: filters.supplier?.trim() || undefined,
        product_code: filters.product_code?.trim() || undefined,
        branch: filters.branch || undefined,
        mapping_status: filters.mapping_status || undefined,
        request_id: requestId || undefined,
      });
    }, 350);
    return () => window.clearTimeout(timer);
  }, [filters, requestId]);

  useEffect(() => {
    if (perms.loading) return;
    if (!perms.canReviewUnmappedProducts) {
      setForbidden(true);
      setLoading(false);
      setError("Você não tem permissão para ver os produtos sem código Delpi.");
      return;
    }
    setForbidden(false);
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    api
      .listUnmappedProducts(debounced, controller.signal)
      .then((data) => {
        setItems(data.items ?? []);
        setTotalPages(data.total_pages ?? 0);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        if (err instanceof ApiError && err.status === 403) {
          setForbidden(true);
        }
        setError(err instanceof Error ? err.message : "Falha ao carregar o histórico.");
        setItems([]);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [debounced, perms.loading, perms.canReviewUnmappedProducts]);

  const page = debounced.page ?? 1;

  function clearRequestFilter() {
    setRequestId("");
    setFilters((current) => ({ ...current, page: 1 }));
    if (typeof window !== "undefined") {
      const url = new URL(window.location.href);
      url.searchParams.delete("requestId");
      window.history.replaceState({}, "", `${url.pathname}${url.search}`);
    }
  }

  return (
    <div className="lnf-stack" data-testid="unmapped-products-page">
      <LnfPageHeader
        title="Produtos sem código Delpi"
        subtitle={helpTooltips.unmappedProducts}
      />

      {requestId ? (
        <p className="lnf-muted" data-testid="unmapped-request-filter">
          Mostrando a solicitação desta notificação.{" "}
          <button type="button" className="lnf-btn lnf-btn--ghost lnf-btn--sm" onClick={clearRequestFilter}>
            Ver todo o histórico
          </button>
        </p>
      ) : null}

      <div className="lnf-filters__row">
        <label className="lnf-field">
          Fornecedor
          <input
            value={filters.supplier ?? ""}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                supplier: event.target.value,
                page: 1,
              }))
            }
          />
        </label>
        <label className="lnf-field">
          Código na nota
          <input
            value={filters.product_code ?? ""}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                product_code: event.target.value,
                page: 1,
              }))
            }
          />
        </label>
        <label className="lnf-field">
          Filial
          <select
            value={filters.branch ?? ""}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                branch: event.target.value,
                page: 1,
              }))
            }
          >
            <option value="">Todas</option>
            <option value="01">Filial 01 (SC)</option>
            <option value="02">Filial 02 (ES)</option>
          </select>
        </label>
        <label className="lnf-field">
          Situação
          <select
            value={filters.mapping_status ?? ""}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                mapping_status: event.target.value as UnmappedProductFilters["mapping_status"],
                page: 1,
              }))
            }
          >
            <option value="">Todas</option>
            <option value="unmapped">Sem vínculo</option>
            <option value="ambiguous">Ambíguo</option>
          </select>
        </label>
      </div>

      {error ? (
        <div className="lnf-alert lnf-error" role="alert">
          <p>{error}</p>
        </div>
      ) : null}

      {!forbidden && loading ? <p className="lnf-muted">Carregando histórico…</p> : null}

      {!forbidden && !loading && items.length === 0 ? (
        <div className="lnf-empty" data-testid="unmapped-empty">
          <SearchX size={28} />
          <h2>Nenhum produto sem vínculo</h2>
          <p>Não há ocorrências para este filtro.</p>
        </div>
      ) : null}

      {!forbidden && items.length > 0 ? (
        <div className="lnf-table-wrap">
          <table className="lnf-table" data-testid="unmapped-table">
            <thead>
              <tr>
                <th>Quando</th>
                <th>Filial</th>
                <th>Fornecedor</th>
                <th>Código na nota</th>
                <th>Descrição</th>
                <th>Quantidade</th>
                <th>Situação</th>
                <th>Nota</th>
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr key={row.id}>
                  <td>{formatDateTime(row.created_at)}</td>
                  <td>{branchLabel(row.branch_code)}</td>
                  <td>
                    <div className="lnf-cell-strong">{row.supplier_name}</div>
                    <div className="lnf-muted lnf-cell-sub">
                      {row.supplier_code}/{row.supplier_store}
                    </div>
                  </td>
                  <td>{row.supplier_product_code}</td>
                  <td>{row.supplier_product_description || "—"}</td>
                  <td>{quantityLabel(row)}</td>
                  <td>{statusLabel(row.mapping_status)}</td>
                  <td>
                    <a href={requestHref(row)}>
                      {formatDocument(row.document_number, row.series)}
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {!forbidden && totalPages > 1 ? (
        <div className="lnf-pagination">
          <button
            type="button"
            className="lnf-btn lnf-btn--ghost lnf-btn--sm"
            disabled={page <= 1 || loading}
            onClick={() => setFilters((current) => ({ ...current, page: page - 1 }))}
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
            onClick={() => setFilters((current) => ({ ...current, page: (current.page ?? 1) + 1 }))}
          >
            Próxima
          </button>
        </div>
      ) : null}
    </div>
  );
}
