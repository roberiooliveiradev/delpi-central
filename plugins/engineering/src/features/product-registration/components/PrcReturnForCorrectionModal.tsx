/** PRC-REF-022-FIX-02 — modal compacto para Devolver para correção.
 * Lista única e uniforme: cada campo corrigível (SB1 e atributos SA5)
 * aparece como checkbox + motivo, sem seções, seletores ou etapas.
 * A identidade técnica do vínculo (supplierCode/store/targetAttribute)
 * é preenchida automaticamente a partir da ficha — invisível ao analista. */

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
import type { InfoSupplierOption } from "../prcInformationExchange";
import { PRC_SUPPLIER_LABELS, prcFieldLabel } from "../prcCopy";
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

export type PrcReturnEntry =
  | { key: string; kind: "field"; label: string; path: string }
  | {
      key: string;
      kind: "supplier";
      label: string;
      supplierCode: string;
      store: string;
      targetAttribute: "partNumber" | "catalogNumber" | null;
    };

/** Lista única de campos devolvíveis: paths SB1 do catálogo + por
 * vínculo existente na ficha as opções Fornecedor (link integral),
 * Part Number e Catálogo. A identidade técnica sai da ficha — nunca
 * de input do analista. */
export function prcReturnEntryList(
  fieldSpecs: PrcFieldSpec[] | null | undefined,
  suppliers: InfoSupplierOption[] | null | undefined,
): PrcReturnEntry[] {
  const fromSpec = (fieldSpecs || [])
    .map((s) => s.path)
    .filter((p) => p !== "officialProductCode" && p !== "suppliers");
  const base = Array.from(
    new Set(fromSpec.length ? fromSpec : FIELD_CANDIDATES),
  );
  const out: PrcReturnEntry[] = base.map((path) => ({
    key: `FIELD:${path}`,
    kind: "field",
    label: prcFieldLabel(path),
    path,
  }));
  const links = new Map<string, { code: string; store: string }>();
  for (const s of suppliers || []) {
    const code = String(s.supplierCode || "").trim();
    const store = String(s.store || "").trim();
    if (code && store) links.set(`${code}|${store}`, { code, store });
  }
  const multiple = links.size > 1;
  for (const { code, store } of links.values()) {
    const suffix = multiple ? ` — Fornecedor ${code} / ${store}` : "";
    const id = `${code}|${store}`;
    out.push({
      key: `SUP:${id}:link`,
      kind: "supplier",
      label: multiple ? `Fornecedor ${code} / ${store}` : "Fornecedor",
      supplierCode: code,
      store,
      targetAttribute: null,
    });
    out.push({
      key: `SUP:${id}:partNumber`,
      kind: "supplier",
      label: `${PRC_SUPPLIER_LABELS.partNumber}${suffix}`,
      supplierCode: code,
      store,
      targetAttribute: "partNumber",
    });
    out.push({
      key: `SUP:${id}:catalogNumber`,
      kind: "supplier",
      label: `${PRC_SUPPLIER_LABELS.catalogNumber}${suffix}`,
      supplierCode: code,
      store,
      targetAttribute: "catalogNumber",
    });
  }
  return out;
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
  /** Vínculos já presentes na ficha — origem das opções SA5 e da
   * identidade técnica enviada ao backend (nunca input livre). */
  suppliers?: InfoSupplierOption[];
  onSubmit: (targets: PrcCorrectionTargetInput[]) => void;
  onCancel: () => void;
}) {
  const formId = useId();
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  const [reasons, setReasons] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState("");

  const entries = useMemo<PrcReturnEntry[]>(
    () => prcReturnEntryList(fieldSpecs, suppliers),
    [fieldSpecs, suppliers],
  );

  if (!open) return null;

  const toggle = (key: string, checked: boolean) => {
    setSelected((prev) => ({ ...prev, [key]: checked }));
    setFormError("");
  };

  const submit = () => {
    const targets: PrcCorrectionTargetInput[] = [];
    for (const entry of entries) {
      if (!selected[entry.key]) continue;
      const reason = (reasons[entry.key] || "").trim();
      if (reason.length < 3) {
        setFormError(
          `Informe o motivo (mín. 3 caracteres) para «${entry.label}».`,
        );
        return;
      }
      if (entry.kind === "field") {
        targets.push({
          targetType: "FIELD",
          targetPath: entry.path,
          reason,
        });
      } else {
        targets.push({
          targetType: "SUPPLIER_LINK",
          targetPath: "suppliers",
          targetAttribute: entry.targetAttribute,
          supplierKey: {
            supplierCode: entry.supplierCode,
            store: entry.store,
          },
          reason,
        });
      }
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
        Selecione os campos que precisam de correção e informe o motivo.
        O solicitante editará na mesma ficha técnica.
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
          {entries.map((entry) => {
            const picked = Boolean(selected[entry.key]);
            return (
              <div key={entry.key} className="engineering-prc__edit-row">
                <EngineeringCheckboxControl
                  checked={picked}
                  disabled={busy}
                  onChange={(v) => toggle(entry.key, v)}
                  label={entry.label}
                />
                {picked ? (
                  <EngineeringTextAreaField
                    id={`${formId}-reason-${entry.key}`}
                    label="Motivo da correção"
                    value={reasons[entry.key] || ""}
                    onChange={(v) =>
                      setReasons((s) => ({ ...s, [entry.key]: v }))
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
