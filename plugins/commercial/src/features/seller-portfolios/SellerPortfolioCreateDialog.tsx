import { useEffect, useState } from "react";

import {
  CommercialActionButton,
  CommercialHostDialog,
  CommercialStateBanner,
  CommercialTextField,
} from "../../app/commercialUi";
import { CM_HELP } from "../../content/helpTooltips";

type SellerPortfolioCreateDialogProps = {
  open: boolean;
  busy: boolean;
  error: string | null;
  onClose: () => void;
  onCreate: (input: { displayName: string }) => void;
};

export function SellerPortfolioCreateDialog({
  open,
  busy,
  error,
  onClose,
  onCreate,
}: SellerPortfolioCreateDialogProps) {
  const [displayName, setDisplayName] = useState("");

  useEffect(() => {
    if (open) return;
    setDisplayName("");
  }, [open]);

  function handleClose() {
    if (busy) return;
    setDisplayName("");
    onClose();
  }

  function handleCreate() {
    const name = displayName.trim();
    if (!name) return;
    onCreate({ displayName: name });
  }

  return (
    <CommercialHostDialog
      open={open}
      title="Nova carteira"
      description={CM_HELP.sellerPortfolios.createDialog}
      onClose={handleClose}
      footer={
        <div className="cm-portfolios-form__actions">
          <CommercialActionButton variant="ghost" onClick={handleClose} disabled={busy}>
            Cancelar
          </CommercialActionButton>
          <CommercialActionButton
            variant="primary"
            onClick={handleCreate}
            disabled={busy || !displayName.trim()}
          >
            {busy ? "Salvando…" : "Criar"}
          </CommercialActionButton>
        </div>
      }
    >
      <div className="cm-portfolios-form">
        {error ? <CommercialStateBanner variant="error">{error}</CommercialStateBanner> : null}
        <div className="cm-portfolios-form__display-name">
          <CommercialTextField
            label="Nome da carteira"
            hint={CM_HELP.sellerPortfolios.displayName}
            value={displayName}
            onChange={setDisplayName}
            placeholder="Ex.: Carteira Sul"
          />
        </div>
      </div>
    </CommercialHostDialog>
  );
}
