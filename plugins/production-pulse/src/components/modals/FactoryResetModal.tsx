import { PpActionButton, PpHostContainedDialog } from "../../app/productionPulseUi";
import { PP_HELP } from "../../content/helpTooltips";

type FactoryResetModalProps = {
  open: boolean;
  loading: boolean;
  error: string | null;
  onConfirm: () => void;
  onClose: () => void;
};

export function FactoryResetModal({
  open,
  loading,
  error,
  onConfirm,
  onClose,
}: FactoryResetModalProps) {
  return (
    <PpHostContainedDialog open={open} title={PP_HELP.modals.factoryResetTitle} onClose={onClose}>
      <div className="pp-modal-body">
        <p>{PP_HELP.modals.factoryResetBody}</p>
        {error ? <p className="pp-modal-body__error">{error}</p> : null}
        <div className="pp-modal-body__actions">
          <PpActionButton variant="ghost" onClick={onClose} disabled={loading}>
            Cancelar
          </PpActionButton>
          <PpActionButton variant="primary" onClick={onConfirm} disabled={loading}>
            {loading ? "Enviando…" : PP_HELP.modals.factoryResetConfirm}
          </PpActionButton>
        </div>
      </div>
    </PpHostContainedDialog>
  );
}
