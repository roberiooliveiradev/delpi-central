import { useEffect, useMemo, useState } from "react";
import * as api from "../../data/api/invoicePostingApi";
import type { LinkedPurchaseOrderSnapshot, OpenPurchaseOrderGroup } from "../../domain/types";
import {
  preselectLineKeys,
  PurchaseOrderSelector,
  selectedGroupsFromLineKeys,
} from "./PurchaseOrderSelector";

type Props = {
  open: boolean;
  requestId: string;
  supplierName: string;
  branchCode: string;
  canLink: boolean;
  onClose: () => void;
  onLinked?: () => void;
  restrictToProductCodes?: string[] | null;
};

function normalizeLinked(raw: unknown): LinkedPurchaseOrderSnapshot[] {
  if (Array.isArray(raw)) return raw;
  if (raw && typeof raw === "object") return [raw as LinkedPurchaseOrderSnapshot];
  return [];
}

function setsEqual(a: Set<string>, b: Set<string>): boolean {
  if (a.size !== b.size) return false;
  for (const key of a) {
    if (!b.has(key)) return false;
  }
  return true;
}

export function PurchaseOrdersModal({
  open,
  requestId,
  supplierName,
  branchCode,
  canLink,
  onClose,
  onLinked,
  restrictToProductCodes = null,
}: Props) {
  const [loading, setLoading] = useState(false);
  const [linking, setLinking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [groups, setGroups] = useState<OpenPurchaseOrderGroup[]>([]);
  const [linked, setLinked] = useState<LinkedPurchaseOrderSnapshot[]>([]);
  const [orderCount, setOrderCount] = useState(0);
  const [selectedLineKeys, setSelectedLineKeys] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    setSelectedLineKeys(new Set());
    void api
      .listRequestPurchaseOrders(requestId, controller.signal)
      .then((data) => {
        if (controller.signal.aborted) return;
        const nextGroups = data.groups ?? [];
        const nextLinked = normalizeLinked(data.linked);
        setGroups(nextGroups);
        setLinked(nextLinked);
        setOrderCount(data.order_count ?? 0);
        setSelectedLineKeys(preselectLineKeys(nextGroups, nextLinked));
      })
      .catch((err) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Falha ao consultar pedidos de compra no Protheus.");
        setGroups([]);
        setLinked([]);
        setOrderCount(0);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [open, requestId]);

  const selectedGroupsPayload = useMemo(
    () => selectedGroupsFromLineKeys(groups, selectedLineKeys),
    [groups, selectedLineKeys],
  );
  const linkedKeys = useMemo(() => preselectLineKeys(groups, linked), [groups, linked]);
  const selectionChanged = !setsEqual(selectedLineKeys, linkedKeys);

  async function handleLink() {
    if (!canLink || linking) return;
    setLinking(true);
    setError(null);
    try {
      await api.linkRequestPurchaseOrder(requestId, { groups: selectedGroupsPayload });
      onLinked?.();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao amarrar pedido de compra.");
    } finally {
      setLinking(false);
    }
  }

  if (!open) return null;

  return (
    <div className="lnf-modal-backdrop" role="presentation">
      <div className="lnf-modal lnf-modal--wide" role="dialog" aria-modal="true" aria-labelledby="lnf-po-title">
        <div className="lnf-modal__header">
          <h2 id="lnf-po-title">Pedidos de compra</h2>
          <button
            type="button"
            className="lnf-modal__close"
            onClick={onClose}
            disabled={linking}
            aria-label="Fechar"
            data-testid="po-close-btn"
          >
            ×
          </button>
        </div>
        <p className="lnf-muted">
          Em aberto no Protheus · Filial {branchCode} · {supplierName}
        </p>
        <PurchaseOrderSelector
          groups={groups}
          orderCount={orderCount}
          loading={loading}
          error={error}
          canSelect={canLink}
          selectedLineKeys={selectedLineKeys}
          onSelectedLineKeysChange={setSelectedLineKeys}
          linked={linked}
          restrictToProductCodes={restrictToProductCodes}
        />
        <div className="lnf-modal__actions">
          <button type="button" className="lnf-btn lnf-btn--ghost" onClick={onClose} disabled={linking}>
            Fechar
          </button>
          {canLink ? (
            <button
              type="button"
              className="lnf-btn lnf-btn--primary"
              disabled={linking || loading || !selectionChanged}
              onClick={() => void handleLink()}
              data-testid="po-link-btn"
            >
              {linking
                ? "Salvando…"
                : selectedLineKeys.size === 0
                  ? "Desamarrar todos"
                  : `Salvar amarração (${selectedLineKeys.size} it.)`}
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
}
