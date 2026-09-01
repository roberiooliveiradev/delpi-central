import { ModalShell, modalShellBemClasses } from "@delpi/plugin-ui/index";

import { PpActionButton } from "../../app/productionPulseUi";
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
    <ModalShell
      open={open}
      title={PP_HELP.modals.clearOperatorTitle}
      onClose={onClose}
      classNames={modalShellBemClasses("pp")}
    >
      <div className="pp-modal-body pp-modal-body--operator">
        <p>{PP_HELP.modals.clearOperatorBody}</p>
        {error ? <p className="pp-modal-body__error">{error}</p> : null}
        <div className="pp-modal-body__actions pp-modal-body__actions--operator">
          <PpActionButton variant="ghost" onClick={onClose} disabled={loading}>
            Cancelar
          </PpActionButton>
          <PpActionButton variant="primary" onClick={onConfirm} disabled={loading}>
            {loading ? "Enviando…" : "Sim, zerar (0)"}
          </PpActionButton>
        </div>
      </div>
    </ModalShell>
  );
}
