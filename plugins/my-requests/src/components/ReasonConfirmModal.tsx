import { useEffect, useId, useState } from "react";
import {
  ActionButton,
  FieldLabel,
  NativeCheckboxControl,
  NativeTextAreaControl,
} from "@delpi/plugin-ui/index";

import type { CorrectionTargetOption } from "../content/correctionTargets";
import { MY_REQUESTS_HELP_TOOLTIPS } from "../content/helpTooltips";
import { MyRequestsFormActions, MyRequestsModal } from "../ui/mrUi";

export type ReasonConfirmKind = "return" | "cancel" | "reject_fulfillment";

export type ReasonConfirmResult = {
  reason: string;
  correctionTargets: string[];
};

type ReasonConfirmModalProps = {
  open: boolean;
  kind: ReasonConfirmKind;
  busy?: boolean;
  /** Só na devolução do atendimento — opções de seções/campos a marcar. */
  correctionOptions?: CorrectionTargetOption[];
  onClose: () => void;
  onConfirm: (result: ReasonConfirmResult) => void;
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
      "Explique o que precisa ser ajustado e, se quiser, marque as seções que o solicitante deve corrigir.",
  },
  cancel: {
    title: "Cancelar solicitação",
    label: "Justificativa do cancelamento",
    confirm: "Cancelar solicitação",
    description: "Informe por que a solicitação será cancelada. Esta ação encerra o fluxo.",
  },
  reject_fulfillment: {
    title: "Devolver para correção",
    label: "Motivo da devolução",
    confirm: "Devolver para correção",
    description:
      "Explique o que está incorreto no atendimento ou na nota. A equipe poderá substituir o documento e registrar a emissão novamente.",
  },
};

export function ReasonConfirmModal({
  open,
  kind,
  busy,
  correctionOptions = [],
  onClose,
  onConfirm,
}: ReasonConfirmModalProps) {
  const [reason, setReason] = useState("");
  const [selected, setSelected] = useState<string[]>([]);
  const fieldId = useId();
  const copy = COPY[kind];
  const trimmed = reason.trim();
  const showTargets = kind === "return" && correctionOptions.length > 0;

  useEffect(() => {
    if (open) {
      setReason("");
      setSelected([]);
    }
  }, [open, kind]);

  function toggleTarget(id: string, checked: boolean) {
    setSelected((prev) => {
      if (checked) return prev.includes(id) ? prev : [...prev, id];
      return prev.filter((row) => row !== id);
    });
  }

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
            onClick={() =>
              onConfirm({
                reason: trimmed,
                correctionTargets: showTargets ? selected : [],
              })
            }
          >
            {copy.confirm}
          </ActionButton>
        </MyRequestsFormActions>
      }
    >
      <div className="my-requests-reason-modal" title={MY_REQUESTS_HELP_TOOLTIPS.detail.actions}>
        <FieldLabel label={copy.label} htmlFor={fieldId} />
        <NativeTextAreaControl
          id={fieldId}
          value={reason}
          onChange={setReason}
          rows={4}
          disabled={busy}
          data-testid="reason-confirm-textarea"
        />

        {showTargets ? (
          <div
            className="my-requests-reason-modal__targets"
            data-testid="reason-confirm-targets"
          >
            <FieldLabel
              label="Campos a corrigir"
              hint={MY_REQUESTS_HELP_TOOLTIPS.detail.correctionTargets}
            />
            <ul className="my-requests-reason-modal__target-list">
              {correctionOptions.map((option) => (
                <li key={option.id}>
                  <NativeCheckboxControl
                    checked={selected.includes(option.id)}
                    disabled={busy}
                    label={option.label}
                    onChange={(checked) => toggleTarget(option.id, checked)}
                  />
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>
    </MyRequestsModal>
  );
}
