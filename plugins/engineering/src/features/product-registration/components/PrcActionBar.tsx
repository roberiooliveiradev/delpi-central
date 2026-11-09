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
import type { PrcFieldSpec } from "../api/productRegistrationApi";
import type { InfoSupplierOption } from "../prcInformationExchange";
import {
  PRC_ACTION_ORDER,
  PRC_ACTION_SPECS,
  type PrcActionExtras,
  type PrcActionSpec,
} from "./prcActionSpecs";
import { PrcRequestInformationModal } from "./PrcRequestInformationModal";

type PendingAction = {
  spec: PrcActionSpec;
  reason: string;
  officialCode: string;
  codeError: string;
};

export function PrcActionBar({
  allowedActions,
  busy,
  officialCode,
  requestType,
  requesterLabel,
  fieldSpecs,
  suppliers,
  onRunAction,
  onEditDraft,
}: {
  allowedActions: string[];
  busy: boolean;
  officialCode: string;
  /** CREATE: código editável na conclusão; UPDATE: travado no baseline. */
  requestType?: "create" | "update" | string;
  /** PRC-REF-019 — destinatário exibido em "Solicitar informações". */
  requesterLabel?: string;
  /** Catálogo de campos (alvos FIELD das perguntas). */
  fieldSpecs?: PrcFieldSpec[] | null;
  /** Fornecedores da ficha técnica (atalho para alvos SUPPLIER_LINK). */
  suppliers?: InfoSupplierOption[];
  onRunAction: (spec: PrcActionSpec, extras: PrcActionExtras) => void;
  onEditDraft?: () => void;
}) {
  const [pending, setPending] = useState<PendingAction | null>(null);
  const [infoSpec, setInfoSpec] = useState<PrcActionSpec | null>(null);
  const [reasonError, setReasonError] = useState("");
  const isUpdate = requestType === "update";

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
    if (spec.needsOfficialCode) {
      const code = pending.officialCode.trim();
      if (!isUpdate && !code) {
        setPending((p) =>
          p
            ? {
                ...p,
                codeError:
                  "Informe o código oficial atribuído ao produto após o cadastro manual no TOTVS.",
              }
            : p,
        );
        return;
      }
      if (isUpdate && !code) {
        setPending((p) =>
          p
            ? {
                ...p,
                codeError:
                  "Solicitação UPDATE sem código oficial baseline.",
              }
            : p,
        );
        return;
      }
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
    if (spec.needsQuestions) {
      setInfoSpec(spec);
      return;
    }
    if (spec.confirmTitle) {
      setPending({
        spec,
        reason: "",
        officialCode,
        codeError: "",
      });
      setReasonError("");
      return;
    }
    onRunAction(spec, {});
  };

  const verifyConfirmMessage = isUpdate
    ? "A Engineering API relê o cadastro oficial no TOTVS e compara " +
      "apenas os campos alterados nesta solicitação. Qualquer " +
      "divergência mantém a revisão em aberto."
    : "Informe o código oficial gerado no TOTVS após o cadastro " +
      "manual. A Engineering API confirma existência e " +
      "correspondência campo a campo antes de concluir.";

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

      {infoSpec ? (
        <PrcRequestInformationModal
          open
          busy={busy}
          requesterLabel={requesterLabel}
          fieldSpecs={fieldSpecs}
          suppliers={suppliers}
          onCancel={() => setInfoSpec(null)}
          onSubmit={({ questions, message, pendingFields }) => {
            onRunAction(infoSpec, { questions, message, pendingFields });
            setInfoSpec(null);
          }}
        />
      ) : null}

      {pending ? (
        <EngineeringConfirmDialog
          open
          title={pending.spec.confirmTitle || pending.spec.label}
          message={
            <div className="engineering-prc__confirm-body">
              <p>
                {pending.spec.action === "verify_and_complete"
                  ? verifyConfirmMessage
                  : pending.spec.confirmMessage}
              </p>
              {pending.spec.needsOfficialCode ? (
                <EngineeringTextField
                  id="prc-action-official-code"
                  label={
                    isUpdate
                      ? "Código oficial TOTVS (baseline)"
                      : "Código do produto criado no TOTVS"
                  }
                  hint={
                    isUpdate
                      ? "Código travado no baseline D15 — troca exige operação própria."
                      : "Informe o código oficial atribuído ao produto após o cadastro manual no TOTVS."
                  }
                  value={pending.officialCode}
                  onChange={(v) =>
                    setPending((p) =>
                      p && !isUpdate
                        ? { ...p, officialCode: v, codeError: "" }
                        : p,
                    )
                  }
                  required
                  readOnly={isUpdate}
                />
              ) : null}
              {pending.codeError ? (
                <p className="engineering-prc__field-error" role="alert">
                  {pending.codeError}
                </p>
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
