import { useEffect, useRef, useState } from "react";
import { ApiError } from "../../data/api/httpClient";
import * as api from "../../data/api/invoicePostingApi";
import type { OpenPurchaseOrderGroup, Supplier } from "../../domain/types";
import type { InvoiceProductSummaryLine } from "./purchaseOrderProductFilter";
import { branchLabel, type BranchCode } from "../../constants/branch";
import {
  preselectLineKeys,
  PurchaseOrderSelector,
  selectedGroupsFromLineKeys,
  type PurchaseOrderGroupSelection,
} from "./PurchaseOrderSelector";

type Props = {
  branch: string;
  supplier: Supplier;
  selection: PurchaseOrderGroupSelection[];
  onSelectionChange: (next: PurchaseOrderGroupSelection[]) => void;
  onBack: () => void;
  onSubmit: () => void;
  busy: boolean;
  submitError: string | null;
  restrictToProductCodes?: string[] | null;
  invoiceProducts?: InvoiceProductSummaryLine[];
};

export function CreateRequestPurchaseOrderStep({
  branch,
  supplier,
  selection,
  onSelectionChange,
  onBack,
  onSubmit,
  busy,
  submitError,
  restrictToProductCodes = null,
  invoiceProducts = [],
}: Props) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [groups, setGroups] = useState<OpenPurchaseOrderGroup[]>([]);
  const [orderCount, setOrderCount] = useState(0);
  const [selectedLineKeys, setSelectedLineKeys] = useState<Set<string>>(new Set());
  const requestSeq = useRef(0);
  const selectionRef = useRef(selection);
  selectionRef.current = selection;

  useEffect(() => {
    const seq = ++requestSeq.current;
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    setGroups([]);
    api
      .listOpenPurchaseOrders(branch, supplier.supplier_code, supplier.supplier_store, controller.signal)
      .then((data) => {
        if (seq !== requestSeq.current) return;
        const nextGroups = data.groups ?? [];
        setGroups(nextGroups);
        setOrderCount(data.order_count ?? 0);
        setSelectedLineKeys(preselectLineKeys(nextGroups, selectionRef.current));
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted || seq !== requestSeq.current) return;
        setGroups([]);
        setOrderCount(0);
        setSelectedLineKeys(new Set());
        setError(
          err instanceof ApiError || err instanceof Error
            ? err.message
            : "Não foi possível consultar os pedidos de compra no Protheus.",
        );
      })
      .finally(() => {
        if (seq === requestSeq.current) setLoading(false);
      });
    return () => controller.abort();
  }, [branch, supplier.supplier_code, supplier.supplier_store]);

  function changeSelection(next: Set<string>) {
    setSelectedLineKeys(next);
    onSelectionChange(selectedGroupsFromLineKeys(groups, next));
  }

  const hasSelection = selection.length > 0;

  return (
    <section className="lnf-card" data-testid="purchase-order-step">
      <header className="lnf-po-step-head">
        <h2>Pedido de compra</h2>
        <p className="lnf-muted">
          Selecione o pedido, se já estiver no Protheus. Sem pedido, conclua e amarre depois.
        </p>
        <p className="lnf-po-context" data-testid="po-step-context">
          <span>{branchLabel(branch as BranchCode) || branch}</span>
          <span>{supplier.supplier_name}</span>
          <span>
            {supplier.supplier_code}/{supplier.supplier_store}
          </span>
        </p>
        {invoiceProducts.length > 0 ? (
          <ul className="lnf-po-invoice-products" data-testid="po-invoice-products">
            {invoiceProducts.map((line, index) => (
              <li key={`${line.code}-${line.reference}-${index}`}>
                <strong>{line.code}</strong>
                <span>{line.reference}</span>
                <span>
                  {line.quantity}
                  {line.unit ? ` ${line.unit}` : ""}
                </span>
              </li>
            ))}
          </ul>
        ) : null}
      </header>
      <PurchaseOrderSelector
        groups={groups}
        orderCount={orderCount}
        loading={loading}
        error={error}
        canSelect
        selectedLineKeys={selectedLineKeys}
        onSelectedLineKeysChange={changeSelection}
        emptyMessage="Nenhum pedido de compra em aberto foi encontrado para este fornecedor."
        restrictToProductCodes={restrictToProductCodes}
      />
      {!loading && groups.length === 0 && !error ? (
        <p className="lnf-muted">Conclua sem pedido e amarre depois.</p>
      ) : null}
      {submitError ? (
        <p className="lnf-error" role="alert" data-testid="form-submit-error">
          {submitError}
        </p>
      ) : null}
      <div className="lnf-form__actions">
        <button type="button" className="lnf-btn lnf-btn--ghost" onClick={onBack} disabled={busy}>
          Voltar
        </button>
        <button
          type="button"
          className="lnf-btn lnf-btn--primary"
          data-testid="btn-submit-request"
          disabled={busy}
          onClick={onSubmit}
        >
          {busy
            ? "Salvando…"
            : hasSelection
              ? "Concluir com pedido de compra"
              : "Concluir sem pedido de compra"}
        </button>
      </div>
    </section>
  );
}
