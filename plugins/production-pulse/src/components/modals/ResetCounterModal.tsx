import { PpActionButton, PpHostContainedDialog } from "../../app/productionPulseUi";
import { PP_HELP } from "../../content/helpTooltips";

type ResetCounterModalProps = {
  open: boolean;
  loading: boolean;
  error: string | null;
  onConfirm: () => void;
  onClose: () => void;
};

export function ResetCounterModal({
  open,
  loading,
  error,
  onConfirm,
  onClose,
}: ResetCounterModalProps) {
  return (
    <PpHostContainedDialog open={open} title={PP_HELP.modals.resetTitle} onClose={onClose}>
      <div className="pp-modal-body">
        <p>{PP_HELP.modals.resetBody}</p>
        {error ? <p className="pp-modal-body__error">{error}</p> : null}
        <div className="pp-modal-body__actions">
          <PpActionButton variant="ghost" onClick={onClose} disabled={loading}>
            Cancelar
          </PpActionButton>
          <PpActionButton variant="primary" onClick={onConfirm} disabled={loading}>
            {loading ? "Enviando…" : "Zerar contador"}
          </PpActionButton>
        </div>
      </div>
    </PpHostContainedDialog>
  );
}
