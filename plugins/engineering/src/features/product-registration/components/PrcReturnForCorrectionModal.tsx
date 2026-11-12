/** PRC-REF-022-FIX-02 / GRANULAR-CORRECTION-09 — modal de devolução
 * para correção. A seleção (campos escalares + células de fornecedor
 * com motivo por alvo) é o componente compartilhado do kit; aqui ficam
 * apenas o diálogo do portal e o envio do contrato. */

import { useMemo, useState } from "react";

import {
  PrcCorrectionTargetSelector,
  correctionReasonControlId,
  correctionTargetsFromSelection,
  emptyCorrectionSelection,
  firstInvalidCorrectionTarget,
  orderedCorrectionTargetKeys,
  pruneCorrectionErrors,
  PRC_FIELD_GROUP_BY_PATH,
  type PrcCorrectionFieldOption,
  type PrcCorrectionSelection,
  type PrcCorrectionTargetErrors,
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
  return base.map((path) => ({
    path,
    label: prcFieldLabel(path),
    group: PRC_FIELD_GROUP_BY_PATH[path] || null,
  }));
}

export function PrcReturnForCorrectionModal({
  open,
  busy,
  fieldSpecs,
  suppliers,
  draft,
  onSubmit,
  onCancel,
}: {
  open: boolean;
  busy: boolean;
  fieldSpecs?: PrcFieldSpec[] | null;
  /** Vínculos da ficha — origem das opções SA5 e da identidade técnica
   * enviada ao backend (nunca input do analista). */
  suppliers?: InfoSupplierOption[];
  /** Ficha atual — valor "Atual:" por campo (vazio também é alvo). */
  draft?: Record<string, unknown> | null;
  onSubmit: (targets: PrcCorrectionTargetInput[]) => void;
  onCancel: () => void;
}) {
  const [selection, setSelection] = useState<PrcCorrectionSelection>(
    emptyCorrectionSelection,
  );
  const [formError, setFormError] = useState("");
  /* FIX-12 — erros por alvo exibidos junto ao motivo; o resumo global
   * fica só para o caso sem campo responsável (nenhum alvo marcado). */
  const [fieldErrors, setFieldErrors] =
    useState<PrcCorrectionTargetErrors>({});

  const fieldOptions = useMemo(
    () => prcReturnFieldOptions(fieldSpecs),
    [fieldSpecs],
  );

  if (!open) return null;

  const submit = () => {
    const { targets, error, errors } = correctionTargetsFromSelection(
      selection,
      fieldOptions,
      suppliers || [],
    );
    if (!targets) {
      setFormError(error);
      setFieldErrors(errors);
      /* FIX-12 — foca o primeiro inválido na ordem visual e rola o
       * conteúdo interno do modal até ele. */
      const first = firstInvalidCorrectionTarget(
        errors,
        orderedCorrectionTargetKeys(fieldOptions, suppliers || []),
      );
      if (first) {
        requestAnimationFrame(() => {
          const el = document.getElementById(
            correctionReasonControlId("eng-prc-return", first),
          );
          if (!el) return;
          el.scrollIntoView?.({ block: "center", behavior: "auto" });
          el.focus({ preventScroll: true });
        });
      }
      return;
    }
    setFormError("");
    setFieldErrors({});
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
        de cada um — mesmo que estejam vazios. O solicitante editará
        somente os alvos devolvidos, no mesmo chamado.
      </p>
      <PrcCorrectionTargetSelector
        fieldOptions={fieldOptions}
        suppliers={suppliers || []}
        draft={draft}
        selection={selection}
        onChange={(next) => {
          setSelection(next);
          setFormError("");
          /* FIX-12 — corrige/desmarca um alvo → some só o erro dele. */
          setFieldErrors((prev) =>
            pruneCorrectionErrors(
              prev,
              next,
              fieldOptions,
              suppliers || [],
            ),
          );
        }}
        errors={fieldErrors}
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
