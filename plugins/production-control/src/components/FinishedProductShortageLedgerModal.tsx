import { HostContainedWideDialog } from "./PpcConfirmModal";
import { copy } from "../content/copy";
import type {
  FinishedProductShortageLedgerRow,
  FinishedProductShortageMaterial,
} from "../types";
import { formatIsoDate } from "../utils/formatIsoDate";
import { formatOpQuantity } from "../utils/formatOpQuantity";

type FinishedProductShortageLedgerModalProps = {
  material: FinishedProductShortageMaterial | null;
  motherOrder: string;
  ledger: FinishedProductShortageLedgerRow[];
  onClose: () => void;
};

export function FinishedProductShortageLedgerModal({
  material,
  motherOrder,
  ledger,
  onClose,
}: FinishedProductShortageLedgerModalProps) {
  if (!material) return null;
  const texts = copy.materials.paShortage;

  return (
    <HostContainedWideDialog open title={texts.ledgerTitle(material.product_code)} onClose={onClose}>
      <div className="ppc-pa-shortage-ledger">
        <p className="ppc-pa-shortage-ledger__product">
          {material.product_code}
          {material.product_description ? ` · ${material.product_description}` : ""}
        </p>
        <p className="ppc-pa-shortage-ledger__hint">{texts.ledgerHint}</p>
        {ledger.length === 0 ? (
          <p className="ppc-state">{texts.emptyIdle}</p>
        ) : (
          <table className="ppc-pa-shortage-ledger__table">
            <thead>
              <tr>
                <th>{texts.ledgerDate}</th>
                <th>{texts.ledgerOrigin}</th>
                <th>{texts.ledgerReference}</th>
                <th>{texts.ledgerIn}</th>
                <th>{texts.ledgerOut}</th>
                <th>{texts.ledgerBalance}</th>
              </tr>
            </thead>
            <tbody>
              {ledger.map((row) => {
                const highlight = row.finished_production_order === motherOrder;
                return (
                  <tr
                    key={`${row.sequence}-${row.origin}-${row.reference}`}
                    data-highlight={highlight ? "true" : undefined}
                  >
                    <td>{formatIsoDate(row.event_date)}</td>
                    <td>{row.origin_label || row.origin}</td>
                    <td>{row.reference}</td>
                    <td>{formatOpQuantity(row.inflow)}</td>
                    <td>{formatOpQuantity(row.outflow)}</td>
                    <td>{formatOpQuantity(row.running_balance)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </HostContainedWideDialog>
  );
}
