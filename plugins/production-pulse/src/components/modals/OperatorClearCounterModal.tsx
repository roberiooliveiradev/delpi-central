import { PpActionButton, PpHostContainedDialog } from "../../app/productionPulseUi";
import { PP_HELP } from "../../content/helpTooltips";

type OperatorClearCounterModalProps = {
  open: boolean;
  loading: boolean;
  error: string | null;
  onConfirm: () => void;
  onClose: () => void;
};

export function OperatorClearCounterModal({
  open,
  loading,
  error,
  onConfirm,
  onClose,
}: OperatorClearCounterModalProps) {
  return (
    <PpHostContainedDialog open={open} title={PP_HELP.modals.clearOperatorTitle} onClose={onClose}>
      <div className="pp-modal-body pp-modal-body--operator">
        <p>{PP_HELP.modals.clearOperatorBody}</p>
        {error ? <p className="pp-modal-body__error">{error}</p> : null}
        <div className="pp-modal-body__actions pp-modal-body__actions--operator">
          <PpActionButton variant="ghost" className="pp-modal-body__action-btn" onClick={onClose} disabled={loading}>
            Cancelar
          </PpActionButton>
          <PpActionButton variant="primary" className="pp-modal-body__action-btn" onClick={onConfirm} disabled={loading}>
            {loading ? "Enviando…" : "Sim, zerar (0)"}
          </PpActionButton>
        </div>
      </div>
    </PpHostContainedDialog>
  );
}
