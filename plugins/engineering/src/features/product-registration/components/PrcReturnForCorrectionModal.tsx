/** PRC-REF-022 — modal compacto para Devolver para correção.
 * Seleciona alvos do catálogo oficial + vínculos SA5 (SUPPLIER_LINK)
 * por pesquisa oficial, com atributo e motivo por alvo.
 * Não duplica a ficha técnica nem cria Q&A paralelo. */

import { useId, useMemo, useState } from "react";

import {
  EngineeringActionButton,
  EngineeringCheckboxControl,
  EngineeringFormActions,
  EngineeringHostDialog,
  EngineeringSearchableSelect,
  EngineeringStateBanner,
  EngineeringTextAreaField,
} from "../../../ui/engineeringUi";
import type { PrcFieldSpec } from "../api/productRegistrationApi";
import { INFO_SUPPLIER_ATTRIBUTE_OPTIONS } from "../prcInformationExchange";
import type { InfoSupplierOption } from "../prcInformationExchange";
import { PRC_SUPPLIER_LABELS, prcFieldLabel } from "../prcCopy";
import type { PrcCorrectionTargetInput } from "./prcActionSpecs";
import { PrcOfficialSupplierSearchField } from "./PrcOfficialSupplierSearchField";

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

const MAX_SUPPLIER_TARGETS = 20;

type SupplierTargetDraft = {
  rowId: string;
  supplierCode: string;
  store: string;
  supplierName?: string;
  targetAttribute: "partNumber" | "catalogNumber";
  reason: string;
};

let supplierRowSeq = 0;

function emptySupplierTarget(): SupplierTargetDraft {
  supplierRowSeq += 1;
  return {
    rowId: `sup-target-${supplierRowSeq}`,
    supplierCode: "",
    store: "",
    targetAttribute: "partNumber",
    reason: "",
  };
}

function supplierTargetKey(draft: SupplierTargetDraft): string {
  return `${draft.supplierCode.trim()}|${draft.store.trim()}|${draft.targetAttribute}`;
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
  /** Vínculos já presentes na ficha — atalho de preenchimento da
   * identidade oficial (supplierCode + store). */
  suppliers?: InfoSupplierOption[];
  onSubmit: (targets: PrcCorrectionTargetInput[]) => void;
  onCancel: () => void;
}) {
  const formId = useId();
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  const [reasons, setReasons] = useState<Record<string, string>>({});
  const [supplierTargets, setSupplierTargets] = useState<
    SupplierTargetDraft[]
  >([]);
  const [supplierErrors, setSupplierErrors] = useState<
    Record<string, string>
  >({});
  const [formError, setFormError] = useState("");

  const paths = useMemo(() => {
    const fromSpec = (fieldSpecs || [])
      .map((s) => s.path)
      .filter((p) => p !== "officialProductCode" && p !== "suppliers");
    const base = fromSpec.length ? fromSpec : FIELD_CANDIDATES;
    return Array.from(new Set(base));
  }, [fieldSpecs]);

  const draftLinkOptions = useMemo(
    () =>
      (suppliers || [])
        .filter((s) => s.supplierCode.trim() && s.store.trim())
        .map((s) => ({
          value: `${s.supplierCode.trim()}|${s.store.trim()}`,
          label: `${s.supplierCode.trim()} / ${s.store.trim()}${
            s.supplierName ? ` — ${s.supplierName}` : ""
          }`,
        })),
    [suppliers],
  );

  if (!open) return null;

  const toggle = (path: string, checked: boolean) => {
    setSelected((prev) => ({ ...prev, [path]: checked }));
  };

  const patchTarget = (
    rowId: string,
    change: Partial<SupplierTargetDraft>,
  ) => {
    setSupplierTargets((list) =>
      list.map((t) => (t.rowId === rowId ? { ...t, ...change } : t)),
    );
    setSupplierErrors((errors) => {
      if (!errors[rowId]) return errors;
      const next = { ...errors };
      delete next[rowId];
      return next;
    });
    setFormError("");
  };

  const pickDraftLink = (rowId: string, value: string) => {
    const [code = "", store = ""] = value.split("|");
    patchTarget(rowId, {
      supplierCode: code.trim(),
      store: store.trim(),
      supplierName: (suppliers || []).find(
        (s) =>
          s.supplierCode.trim() === code.trim() &&
          s.store.trim() === store.trim(),
      )?.supplierName,
    });
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
    const rowErrors: Record<string, string> = {};
    const seen = new Set<string>();
    for (const draft of supplierTargets) {
      const code = draft.supplierCode.trim();
      const store = draft.store.trim();
      if (!code || !store) {
        rowErrors[draft.rowId] =
          "Selecione o fornecedor pela pesquisa oficial ou pela lista de vínculos.";
        continue;
      }
      if (draft.reason.trim().length < 3) {
        rowErrors[draft.rowId] =
          "Informe o motivo (mín. 3 caracteres) para este vínculo.";
        continue;
      }
      const key = supplierTargetKey(draft);
      if (seen.has(key)) {
        rowErrors[draft.rowId] =
          "Este vínculo e atributo já foram adicionados à devolução.";
        continue;
      }
      seen.add(key);
      targets.push({
        targetType: "SUPPLIER_LINK",
        targetPath: "suppliers",
        targetAttribute: draft.targetAttribute,
        supplierKey: { supplierCode: code, store },
        reason: draft.reason.trim(),
      });
    }
    if (Object.keys(rowErrors).length) {
      setSupplierErrors(rowErrors);
      setFormError("Revise os vínculos destacados.");
      return;
    }
    if (!targets.length) {
      setFormError(
        "Selecione ao menos um campo ou vínculo para devolver.",
      );
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
        Indique os campos da ficha e os atributos de fornecedores a
        corrigir, com o motivo de cada alvo. O solicitante editará na
        mesma ficha técnica.
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

        <h3 className="engineering-prc__info-heading">
          Vínculos de fornecedores
        </h3>
        <ol className="engineering-prc__info-questions">
          {supplierTargets.map((draft, index) => {
            const selectedSupplier =
              draft.supplierCode && draft.store
                ? {
                    supplierCode: draft.supplierCode,
                    store: draft.store,
                    supplierName: draft.supplierName,
                  }
                : null;
            return (
              <li
                key={draft.rowId}
                className="engineering-prc__info-question"
                aria-label={`Vínculo ${index + 1}`}
              >
                <div className="engineering-prc__info-question-head">
                  <strong>{`Vínculo ${index + 1}`}</strong>
                  <EngineeringActionButton
                    variant="ghost"
                    disabled={busy}
                    onClick={() =>
                      setSupplierTargets((list) =>
                        list.filter((t) => t.rowId !== draft.rowId),
                      )
                    }
                  >
                    Remover alvo
                  </EngineeringActionButton>
                </div>
                <div className="engineering-prc__info-question-target">
                  {draftLinkOptions.length ? (
                    <EngineeringSearchableSelect
                      id={`${formId}-sup-${draft.rowId}-pick`}
                      label="Vínculo da ficha"
                      searchable
                      value={
                        draft.supplierCode && draft.store
                          ? `${draft.supplierCode}|${draft.store}`
                          : ""
                      }
                      onChange={(v) => pickDraftLink(draft.rowId, v)}
                      options={draftLinkOptions}
                      placeholder="Preencher a partir da ficha"
                      disabled={busy}
                    />
                  ) : null}
                  <PrcOfficialSupplierSearchField
                    id={`${formId}-sup-${draft.rowId}-search`}
                    selected={selectedSupplier}
                    disabled={busy}
                    onSelect={(hit) =>
                      patchTarget(draft.rowId, {
                        supplierCode: hit.supplierCode,
                        store: hit.store,
                        supplierName: hit.supplierName,
                      })
                    }
                    onClear={() =>
                      patchTarget(draft.rowId, {
                        supplierCode: "",
                        store: "",
                        supplierName: undefined,
                      })
                    }
                  />
                  <EngineeringSearchableSelect
                    id={`${formId}-sup-${draft.rowId}-attr`}
                    label="Atributo a corrigir"
                    value={draft.targetAttribute}
                    onChange={(v) =>
                      patchTarget(draft.rowId, {
                        targetAttribute:
                          v as SupplierTargetDraft["targetAttribute"],
                      })
                    }
                    options={INFO_SUPPLIER_ATTRIBUTE_OPTIONS.map((o) => ({
                      value: o.value,
                      label: o.label,
                    }))}
                    disabled={busy}
                  />
                </div>
                <EngineeringTextAreaField
                  id={`${formId}-sup-${draft.rowId}-reason`}
                  label={`Motivo da correção — ${PRC_SUPPLIER_LABELS[draft.targetAttribute]}`}
                  value={draft.reason}
                  onChange={(v) =>
                    patchTarget(draft.rowId, { reason: v })
                  }
                  required
                  maxLength={1000}
                  disabled={busy}
                  rows={2}
                />
                {supplierErrors[draft.rowId] ? (
                  <p className="engineering-prc__field-error" role="alert">
                    {supplierErrors[draft.rowId]}
                  </p>
                ) : null}
              </li>
            );
          })}
        </ol>
        <div>
          <EngineeringActionButton
            variant="ghost"
            disabled={busy || supplierTargets.length >= MAX_SUPPLIER_TARGETS}
            onClick={() =>
              setSupplierTargets((list) => [
                ...list,
                emptySupplierTarget(),
              ])
            }
          >
            Adicionar vínculo
          </EngineeringActionButton>
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
