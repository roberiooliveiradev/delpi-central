/** PRC-REF-022-FIX-02 / GRANULAR-CORRECTION-09 — modal de devolução
 * para correção. A seleção (campos escalares + células de fornecedor
 * com motivo por alvo) é o componente compartilhado do kit; aqui ficam
 * apenas o diálogo do portal e o envio do contrato. */

import { useMemo, useState } from "react";

import {
  PrcCorrectionTargetSelector,
  correctionTargetsFromSelection,
  emptyCorrectionSelection,
  type PrcCorrectionFieldOption,
  type PrcCorrectionSelection,
} from "@delpi/plugin-ui/index";

import {
  EngineeringActionButton,
  EngineeringFormActions,
  EngineeringHostDialog,
  EngineeringStateBanner,
} from "../../../ui/engineeringUi";
import type { PrcFieldSpec } from "../api/productRegistrationApi";
import type { InfoSupplierOption } from "../prcInformationExchange";
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

/** Campos devolvíveis: paths SB1 do catálogo (sem código oficial nem o
 * agregado de fornecedores — esses têm alvo próprio SUPPLIER_LINK). */
export function prcReturnFieldOptions(
  fieldSpecs: PrcFieldSpec[] | null | undefined,
): PrcCorrectionFieldOption[] {
  const fromSpec = (fieldSpecs || [])
    .map((s) => s.path)
    .filter((p) => p !== "officialProductCode" && p !== "suppliers");
  const base = Array.from(
    new Set(fromSpec.length ? fromSpec : FIELD_CANDIDATES),
  );
  return base.map((path) => ({ path, label: prcFieldLabel(path) }));
}

export function PrcReturnForCorrectionModal({
  open,
  busy,
  fieldSpecs,
  suppliers,
  onSubmit,
  onCancel,
}: {
  open: boolean;
  busy: boolean;
  fieldSpecs?: PrcFieldSpec[] | null;
  /** Vínculos da ficha — origem das opções SA5 e da identidade técnica
   * enviada ao backend (nunca input do analista). */
  suppliers?: InfoSupplierOption[];
  onSubmit: (targets: PrcCorrectionTargetInput[]) => void;
  onCancel: () => void;
}) {
  const [selection, setSelection] = useState<PrcCorrectionSelection>(
    emptyCorrectionSelection,
  );
  const [formError, setFormError] = useState("");

  const fieldOptions = useMemo(
    () => prcReturnFieldOptions(fieldSpecs),
    [fieldSpecs],
  );

  if (!open) return null;

  const submit = () => {
    const { targets, error } = correctionTargetsFromSelection(
      selection,
      fieldOptions,
      suppliers || [],
    );
    if (!targets) {
      setFormError(error);
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
      className="engineering-prc-return-modal engineering-modal--wide delpi-ui-modal--wide"
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
        Selecione os campos que precisam ser corrigidos e informe o motivo
        de cada um. O solicitante editará somente os alvos devolvidos, no
        mesmo chamado.
      </p>
      <PrcCorrectionTargetSelector
        fieldOptions={fieldOptions}
        suppliers={suppliers || []}
        selection={selection}
        onChange={(next) => {
          setSelection(next);
          setFormError("");
        }}
        busy={busy}
        idPrefix="eng-prc-return"
      />

      {formError ? (
        <EngineeringStateBanner variant="error">
          {formError}
        </EngineeringStateBanner>
      ) : null}
    </EngineeringHostDialog>
  );
}
