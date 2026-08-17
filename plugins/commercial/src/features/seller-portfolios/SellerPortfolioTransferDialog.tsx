import { useEffect, useMemo, useState } from "react";

import {
  CommercialActionButton,
  CommercialHostDialog,
  CommercialMultiSelectField,
  CommercialSelectField,
  CommercialStateBanner,
  CommercialTextAreaField,
  CommercialTextField,
} from "../../app/commercialUi";
import { CM_HELP } from "../../content/helpTooltips";
import { customerKey } from "../../shared/format";
import type { SellerPortfolio } from "../../types/portfolio";

type SellerPortfolioTransferDialogProps = {
  open: boolean;
  busy: boolean;
  error: string | null;
  source: SellerPortfolio | null;
  portfolios: SellerPortfolio[];
  onClose: () => void;
  onTransfer: (input: {
    targetId: string;
    customerKeys: string[];
    reason: string;
  }) => void;
};

export function SellerPortfolioTransferDialog({
  open,
  busy,
  error,
  source,
  portfolios,
  onClose,
  onTransfer,
}: SellerPortfolioTransferDialogProps) {
  const [targetId, setTargetId] = useState("");
  const [customerKeys, setCustomerKeys] = useState<string[]>([]);
  const [reason, setReason] = useState("");

  const targetOptions = useMemo(
    () =>
      portfolios
        .filter((item) => item.active && item.id !== source?.id)
        .map((item) => ({ value: item.id, label: item.display_name })),
    [portfolios, source?.id],
  );

  const customerOptions = useMemo(
    () =>
      (source?.customers ?? []).map((customer) => ({
        value: customerKey(customer.customer_code, customer.customer_store),
        label: `${customer.customer_code}/${customer.customer_store} · ${customer.customer_name?.trim() || "—"}`,
      })),
    [source],
  );

  useEffect(() => {
    if (!open || !source) return;
    setTargetId("");
    setReason("");
    setCustomerKeys(
      source.customers.map((customer) =>
        customerKey(customer.customer_code, customer.customer_store),
      ),
    );
  }, [open, source]);

  function handleClose() {
    if (busy) return;
    onClose();
  }

  function handleTransfer() {
    if (!source || !targetId || customerKeys.length === 0 || !reason.trim()) return;
    onTransfer({ targetId, customerKeys, reason: reason.trim() });
  }

  return (
    <CommercialHostDialog
      open={open}
      title="Transferir clientes"
      description={CM_HELP.sellerPortfolios.transfer}
      onClose={handleClose}
      footer={
        <div className="cm-portfolios-form__actions">
          <CommercialActionButton variant="ghost" onClick={handleClose} disabled={busy}>
            Cancelar
          </CommercialActionButton>
          <CommercialActionButton
            variant="primary"
            onClick={handleTransfer}
            disabled={busy || !targetId || customerKeys.length === 0 || !reason.trim()}
          >
            {busy ? "Transferindo…" : "Transferir"}
          </CommercialActionButton>
        </div>
      }
    >
      <div className="cm-portfolios-form">
        {error ? <CommercialStateBanner variant="error">{error}</CommercialStateBanner> : null}
        <CommercialTextField
          label="De"
          hint={CM_HELP.sellerPortfolios.transferSource}
          value={source?.display_name ?? "—"}
          onChange={() => undefined}
          disabled
        />
        <CommercialSelectField
          label="Para"
          hint={CM_HELP.sellerPortfolios.transferTarget}
          value={targetId}
          onChange={setTargetId}
          options={targetOptions}
          allowEmpty
          emptyLabel="Selecione carteira ativa"
          searchable
        />
        <div className="cm-portfolios-form__user">
          <CommercialMultiSelectField
            label="Clientes"
            hint={CM_HELP.sellerPortfolios.transferCustomers}
            options={customerOptions}
            selectedValues={customerKeys}
            onChange={setCustomerKeys}
            searchable
            showSelectedTags
          />
        </div>
        <div className="cm-portfolios-form__user">
          <CommercialTextAreaField
            label="Motivo"
            hint={CM_HELP.sellerPortfolios.transferReason}
            value={reason}
            onChange={setReason}
            placeholder="Ex.: Reorganização de carteira regional"
            required
          />
        </div>
      </div>
    </CommercialHostDialog>
  );
}
