/** PRC-REF-022 — modal compacto para Devolver para correção.
 * Seleciona alvos do catálogo oficial + motivo por campo.
 * Não duplica a ficha técnica nem cria Q&A paralelo. */

import { useId, useMemo, useState } from "react";

import {
  EngineeringActionButton,
  EngineeringCheckboxControl,
  EngineeringFormActions,
  EngineeringHostDialog,
  EngineeringStateBanner,
  EngineeringTextAreaField,
} from "../../../ui/engineeringUi";
import type { PrcFieldSpec } from "../api/productRegistrationApi";
import { prcFieldLabel } from "../prcCopy";
import type { PrcCorrectionTargetInput } from "./prcActionSpecs";

const FIELD_CANDIDATES = [
  "description",
  "group",
  "productKind",
  "unit",
  "defaultWarehouse",
  "accountingAccount",
  "thirdPartyProduct",
  "customerReference",
];

export function PrcReturnForCorrectionModal({
  open,
  busy,
  fieldSpecs,
  onSubmit,
  onCancel,
}: {
  open: boolean;
  busy: boolean;
  fieldSpecs?: PrcFieldSpec[] | null;
  onSubmit: (targets: PrcCorrectionTargetInput[]) => void;
  onCancel: () => void;
}) {
  const formId = useId();
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  const [reasons, setReasons] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState("");

  const paths = useMemo(() => {
    const fromSpec = (fieldSpecs || [])
      .map((s) => s.path)
      .filter((p) => p !== "officialProductCode" && p !== "suppliers");
    const base = fromSpec.length ? fromSpec : FIELD_CANDIDATES;
    return Array.from(new Set(base));
  }, [fieldSpecs]);

  if (!open) return null;

  const toggle = (path: string, checked: boolean) => {
    setSelected((prev) => ({ ...prev, [path]: checked }));
  };

  const submit = () => {
    const targets: PrcCorrectionTargetInput[] = [];
    for (const path of paths) {
      if (!selected[path]) continue;
      const reason = (reasons[path] || "").trim();
      if (reason.length < 3) {
        setFormError(
          `Informe o motivo (mín. 3 caracteres) para «${prcFieldLabel(path)}».`,
        );
        return;
      }
      targets.push({
        targetType: "FIELD",
        targetPath: path,
        reason,
      });
    }
    if (!targets.length) {
      setFormError("Selecione ao menos um campo para devolver.");
      return;
    }
    setFormError("");
    onSubmit(targets);
  };

  return (
    <EngineeringHostDialog
      open={open}
      onClose={busy ? () => undefined : onCancel}
      title="Devolver para correção"
      className="engineering-prc-return-modal"
      footer={
        <EngineeringFormActions>
          <EngineeringActionButton
            variant="ghost"
            disabled={busy}
            onClick={onCancel}
          >
            Cancelar
          </EngineeringActionButton>
          <EngineeringActionButton
            variant="primary"
            softDisabled={busy}
            onClick={submit}
          >
            Devolver para correção
          </EngineeringActionButton>
        </EngineeringFormActions>
      }
    >
      <p className="engineering-prc__muted">
        Indique os campos da ficha e o motivo de cada correção. O solicitante
        editará na mesma ficha técnica.
      </p>
      <form
        id={formId}
        className="engineering-prc__return-modal"
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
      >
        <div className="engineering-prc__edit-list">
          {paths.map((path) => {
            const picked = Boolean(selected[path]);
            return (
              <div key={path} className="engineering-prc__edit-row">
                <EngineeringCheckboxControl
                  checked={picked}
                  disabled={busy}
                  onChange={(v) => toggle(path, v)}
                  label={prcFieldLabel(path)}
                />
                {picked ? (
                  <EngineeringTextAreaField
                    id={`${formId}-reason-${path}`}
                    label="Motivo da correção"
                    value={reasons[path] || ""}
                    onChange={(v) =>
                      setReasons((s) => ({ ...s, [path]: v }))
                    }
                    required
                    maxLength={1000}
                    disabled={busy}
                    rows={2}
                  />
                ) : null}
              </div>
            );
          })}
        </div>

        {formError ? (
          <EngineeringStateBanner variant="error">
            {formError}
          </EngineeringStateBanner>
        ) : null}
      </form>
    </EngineeringHostDialog>
  );
}
