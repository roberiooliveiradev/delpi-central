import { useEffect, useState } from "react";
import { UserDirectoryPicker, type DirectoryUserOption } from "@delpi/plugin-ui/index";

import { searchDirectoryUsers } from "../../api/commercialPortfolioApi";
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
  onCreate: (input: { userIds: string[]; displayName: string }) => void;
};

export function SellerPortfolioCreateDialog({
  open,
  busy,
  error,
  onClose,
  onCreate,
}: SellerPortfolioCreateDialogProps) {
  const [createUsers, setCreateUsers] = useState<DirectoryUserOption[]>([]);
  const [createDisplayName, setCreateDisplayName] = useState("");

  useEffect(() => {
    if (open) return;
    setCreateUsers([]);
    setCreateDisplayName("");
  }, [open]);

  function reset() {
    setCreateUsers([]);
    setCreateDisplayName("");
  }

  function handleClose() {
    if (busy) return;
    reset();
    onClose();
  }

  function handleCreate() {
    if (createUsers.length === 0) return;
    const primary = createUsers[0];
    const displayName =
      createDisplayName.trim() ||
      primary?.name.trim() ||
      primary?.email.trim() ||
      "Usuário";
    onCreate({
      userIds: createUsers.map((user) => user.id),
      displayName,
    });
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
            disabled={busy || createUsers.length === 0}
          >
            {busy ? "Salvando…" : "Criar"}
          </CommercialActionButton>
        </div>
      }
    >
      <div className="cm-portfolios-form">
        {error ? <CommercialStateBanner variant="error">{error}</CommercialStateBanner> : null}
        <div className="cm-portfolios-form__user">
          <UserDirectoryPicker
            value={createUsers}
            onChange={(users) => {
              setCreateUsers(users);
              const next = users[0];
              if (next && !createDisplayName.trim()) {
                const fallback = next.name.trim() || next.email.trim();
                if (fallback) setCreateDisplayName(fallback);
              }
              if (users.length === 0) setCreateDisplayName("");
            }}
            searchUsers={searchDirectoryUsers}
            labels={{
              title: "Usuário com acesso ao Portal Comercial",
              hint: CM_HELP.sellerPortfolios.directoryUser,
              placeholder: "Buscar usuário…",
            }}
          />
        </div>
        <div className="cm-portfolios-form__display-name">
          <CommercialTextField
            label="Nome de exibição"
            hint={CM_HELP.sellerPortfolios.displayName}
            value={createDisplayName}
            onChange={setCreateDisplayName}
            placeholder="Ex.: João Silva (padrão = nome do primeiro usuário)"
          />
        </div>
      </div>
    </CommercialHostDialog>
  );
}
