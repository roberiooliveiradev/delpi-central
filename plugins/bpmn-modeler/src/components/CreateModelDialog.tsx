import { useState } from "react";

import { ActionButton } from "@delpi/plugin-ui/index";
import { BpmnmModal, BpmnmTextField } from "../ui/kit";

type Props = {
  open: boolean;
  busy: boolean;
  onCancel: () => void;
  onConfirm: (displayName: string) => void;
};

export function CreateModelDialog({ open, busy, onCancel, onConfirm }: Props) {
  const [name, setName] = useState("");
  const valid = name.trim().length > 0 && name.trim().length <= 120;

  // reset na abertura — adjust-state-during-render (React docs), evita
  // setState em effect (react-hooks/set-state-in-effect)
  const [wasOpen, setWasOpen] = useState(open);
  if (wasOpen !== open) {
    setWasOpen(open);
    if (open) setName("");
  }

  return (
    <BpmnmModal
      open={open}
      title="Novo modelo"
      onClose={onCancel}
      initialFocusSelector="input"
    >
      <form
        onSubmit={(event) => {
          event.preventDefault();
          if (valid && !busy) onConfirm(name.trim());
        }}
      >
        <BpmnmTextField
          label="Nome do modelo"
          value={name}
          onChange={setName}
          required
        />
        <div className="bpmnm-dialog__actions">
          <ActionButton type="button" onClick={onCancel} disabled={busy}>
            Cancelar
          </ActionButton>
          <ActionButton
            variant="primary"
            type="submit"
            disabled={!valid || busy}
          >
            {busy ? "Criando…" : "Criar"}
          </ActionButton>
        </div>
      </form>
    </BpmnmModal>
  );
}
