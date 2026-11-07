/** Barra de ações do detalhe — allowedActions do backend é a única
 * fonte de disponibilidade. Confirmações host-contained; motivo
 * obrigatório quando o contrato exige; CAS via expectedVersion lido
 * no momento do clique (o caller repassa detail.caseVersion atual). */

import { useState } from "react";

import {
  EngineeringActionButton,
  EngineeringTextAreaField,
  EngineeringTextField,
} from "../../../ui/engineeringUi";
import { EngineeringConfirmDialog } from "../../../ui/EngineeringConfirmDialog";
import {
  PRC_ACTION_ORDER,
  PRC_ACTION_SPECS,
  type PrcActionSpec,
} from "./prcActionSpecs";

type PendingAction = {
  spec: PrcActionSpec;
  reason: string;
  officialCode: string;
};

export function PrcActionBar({
  allowedActions,
  busy,
  officialCode,
  onRunAction,
  onEditDraft,
}: {
  allowedActions: string[];
  busy: boolean;
  officialCode: string;
  onRunAction: (
    spec: PrcActionSpec,
    extras: { reason?: string; officialCode?: string },
  ) => void;
  onEditDraft?: () => void;
}) {
  const [pending, setPending] = useState<PendingAction | null>(null);
  const [reasonError, setReasonError] = useState("");

  const actions = PRC_ACTION_ORDER.filter(
    (a) => allowedActions.includes(a) && PRC_ACTION_SPECS[a],
  ).map((a) => PRC_ACTION_SPECS[a]);

  if (!actions.length) return null;

  const close = () => {
    setPending(null);
    setReasonError("");
  };

  const confirmPending = () => {
    if (!pending) return;
    const { spec } = pending;
    if (spec.needsReason && !pending.reason.trim()) {
      setReasonError("Informe o motivo para continuar.");
      return;
    }
    onRunAction(spec, {
      reason: pending.reason.trim() || undefined,
      officialCode:
        spec.needsOfficialCode && pending.officialCode.trim()
          ? pending.officialCode.trim()
          : undefined,
    });
    close();
  };

  const click = (spec: PrcActionSpec) => {
    if (spec.action === "edit_draft") {
      onEditDraft?.();
      return;
    }
    if (spec.confirmTitle) {
      setPending({ spec, reason: "", officialCode });
      setReasonError("");
      return;
    }
    onRunAction(spec, {});
  };

  return (
    <>
      <div className="engineering-prc__actions" role="group" aria-label="Ações da solicitação">
        {actions.map((spec) => (
          <EngineeringActionButton
            key={spec.action}
            variant={
              spec.danger ? "ghost" : spec.primary ? "primary" : "default"
            }
            softDisabled={busy}
            onClick={() => click(spec)}
          >
            {spec.label}
          </EngineeringActionButton>
        ))}
      </div>

      {pending ? (
        <EngineeringConfirmDialog
          open
          title={pending.spec.confirmTitle || pending.spec.label}
          message={
            <div className="engineering-prc__confirm-body">
              <p>{pending.spec.confirmMessage}</p>
              {pending.spec.needsOfficialCode ? (
                <EngineeringTextField
                  id="prc-action-official-code"
                  label="Código oficial TOTVS"
                  hint="Código do produto cadastrado manualmente no ERP."
                  value={pending.officialCode}
                  onChange={(v) =>
                    setPending((p) =>
                      p ? { ...p, officialCode: v } : p,
                    )
                  }
                  required
                />
              ) : null}
              {pending.spec.needsReason ? (
                <EngineeringTextAreaField
                  id="prc-action-reason"
                  label={pending.spec.reasonLabel || "Motivo"}
                  value={pending.reason}
                  onChange={(v) =>
                    setPending((p) => (p ? { ...p, reason: v } : p))
                  }
                  required
                  maxLength={1000}
                />
              ) : null}
              {reasonError ? (
                <p className="engineering-prc__field-error" role="alert">
                  {reasonError}
                </p>
              ) : null}
            </div>
          }
          confirmLabel={pending.spec.label}
          variant={pending.spec.danger ? "danger" : "default"}
          confirmBusy={busy}
          onConfirm={confirmPending}
          onCancel={close}
        />
      ) : null}
    </>
  );
}
