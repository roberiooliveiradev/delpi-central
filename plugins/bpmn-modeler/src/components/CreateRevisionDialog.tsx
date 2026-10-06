import { useState } from "react";

import { ActionButton } from "@delpi/plugin-ui/index";

import { BpmnmModal, BpmnmTextField, BpmnmTextAreaField } from "../ui/kit";

type Props = {
  open: boolean;
  busy: boolean;
  onCancel: () => void;
  onConfirm: (meta: { name?: string; description?: string }) => void;
};

/** Criação explícita de revisão — checkpoint imutável (não é autosave).
 *  Nome/descrição são metadata opcionais do contrato real do domínio;
 *  ambos ficam vazios = revisão anônima continua válida. */
export function CreateRevisionDialog({ open, busy, onCancel, onConfirm }: Props) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const nameTooLong = name.trim().length > 120;
  const descTooLong = description.trim().length > 500;
  const valid = !nameTooLong && !descTooLong;

  // reset na abertura — adjust-state-during-render (React docs)
  const [wasOpen, setWasOpen] = useState(open);
  if (wasOpen !== open) {
    setWasOpen(open);
    if (open) {
      setName("");
      setDescription("");
    }
  }

  return (
    <BpmnmModal
      open={open}
      title="Criar revisão"
      onClose={onCancel}
      initialFocusSelector="input"
      footer={
        <>
          <ActionButton type="button" onClick={onCancel} disabled={busy}>
            Cancelar
          </ActionButton>
          <ActionButton
            variant="primary"
            type="submit"
            form="bpmnm-create-revision-form"
            disabled={!valid || busy}
          >
            {busy ? "Criando…" : "Criar revisão"}
          </ActionButton>
        </>
      }
    >
      <form
        id="bpmnm-create-revision-form"
        onSubmit={(event) => {
          event.preventDefault();
          if (!valid || busy) return;
          onConfirm({
            name: name.trim() || undefined,
            description: description.trim() || undefined,
          });
        }}
      >
        <BpmnmTextField
          label="Nome da revisão"
          value={name}
          onChange={setName}
          placeholder="Ex.: Versão inicial"
          hint={nameTooLong ? "Máximo de 120 caracteres." : undefined}
        />
        <BpmnmTextAreaField
          label="Observação"
          value={description}
          onChange={setDescription}
          placeholder="Opcional — contexto desta versão."
          hint={descTooLong ? "Máximo de 500 caracteres." : undefined}
        />
        <p className="bpmnm-hint">
          A revisão é um marco imutável do estado atual — alterações seguintes
          continuam sendo salvas automaticamente na cópia de trabalho.
        </p>
      </form>
    </BpmnmModal>
  );
}
