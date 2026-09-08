import { useEffect, useId, useState } from "react";
import { ActionButton, FieldLabel, NativeTextAreaControl } from "@delpi/plugin-ui/index";

import { MY_REQUESTS_HELP_TOOLTIPS } from "../content/helpTooltips";
import { MyRequestsFormActions, MyRequestsModal } from "../ui/mrUi";

export type ReasonConfirmKind = "return" | "cancel";

type ReasonConfirmModalProps = {
  open: boolean;
  kind: ReasonConfirmKind;
  busy?: boolean;
  onClose: () => void;
  onConfirm: (reason: string) => void;
};

const COPY: Record<
  ReasonConfirmKind,
  { title: string; label: string; confirm: string; description: string }
> = {
  return: {
    title: "Devolver solicitação",
    label: "Motivo da devolução",
    confirm: "Devolver",
    description:
      "Explique o que precisa ser ajustado. O solicitante verá este motivo ao reabrir o pedido.",
  },
  cancel: {
    title: "Cancelar solicitação",
    label: "Justificativa do cancelamento",
    confirm: "Cancelar solicitação",
    description: "Informe por que a solicitação será cancelada. Esta ação encerra o fluxo.",
  },
};

export function ReasonConfirmModal({
  open,
  kind,
  busy,
  onClose,
  onConfirm,
}: ReasonConfirmModalProps) {
  const [reason, setReason] = useState("");
  const fieldId = useId();
  const copy = COPY[kind];
  const trimmed = reason.trim();

  useEffect(() => {
    if (open) setReason("");
  }, [open, kind]);

  return (
    <MyRequestsModal
      open={open}
      title={copy.title}
      description={copy.description}
      onClose={onClose}
      closeAriaLabel="Fechar"
      footer={
        <MyRequestsFormActions>
          <ActionButton type="button" variant="ghost" disabled={busy} onClick={onClose}>
            Voltar
          </ActionButton>
          <ActionButton
            type="button"
            variant="primary"
            disabled={busy || !trimmed}
            onClick={() => onConfirm(trimmed)}
          >
            {copy.confirm}
          </ActionButton>
        </MyRequestsFormActions>
      }
    >
      <div title={MY_REQUESTS_HELP_TOOLTIPS.detail.actions}>
        <FieldLabel label={copy.label} htmlFor={fieldId} />
        <NativeTextAreaControl
          id={fieldId}
          value={reason}
          onChange={setReason}
          rows={4}
          disabled={busy}
          data-testid="reason-confirm-textarea"
        />
      </div>
    </MyRequestsModal>
  );
}
