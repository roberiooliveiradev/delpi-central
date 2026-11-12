/** Ficha técnica — leitura agrupada por assunto + edição seletiva
 * (PATCH campo-a-campo com motivo e CAS). `suppliers` é delta de
 * relação produto×fornecedor: a lista completa editada é enviada como
 * valor proposto do path `suppliers`, conforme contrato de draft. */

import { useEffect, useMemo, useState } from "react";

import {
  PrcReturnedFieldsEditor,
  PrcTechnicalSheetView,
  type PrcSheetLinkOp,
} from "@delpi/plugin-ui/index";

import {
  EngineeringActionButton,
  EngineeringCheckboxControl,
  EngineeringDetailCard,
  EngineeringFormActions,
  EngineeringSelectField,
  EngineeringStateBanner,
  EngineeringTextField,
} from "../../../ui/engineeringUi";
import type {
  PrcFieldSpec,
  PrcRequestDetail,
  PrcReturnedFieldChange,
} from "../api/productRegistrationApi";
import type { PrcCorrectionTargetErrors } from "@delpi/plugin-ui/index";
import {
  PRC_FIELD_LABELS,
  PRC_SUPPLIER_HELP,
  PRC_SUPPLIER_LABELS,
  prcFieldHelp,
} from "../prcCopy";
import {
  emptySupplierRow,
  supplierRowsToPayload,
  toSupplierRows,
  type SupplierRow,
} from "../prcSuppliers";
import {
  PrcAttendanceFlagsProvider,
  PrcAttendanceFlagsSummary,
  usePrcFlagsContext,
} from "./PrcAttendanceFlags";
import {
  findOpenFieldFlag,
  findOpenSupplierFlag,
  findResolvedFieldFlags,
  findResolvedSupplierFlags,
  PrcFieldFlagTrigger,
} from "./PrcFieldFlagTrigger";

function scalarText(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  return String(value);
}

const FIELD_GROUPS: { title: string; paths: string[] }[] = [
  {
    title: "Identificação e classificação",
    paths: ["officialProductCode", "description", "group", "productKind", "unit"],
  },
  {
    title: "Estoque e contabilidade",
    paths: [
      "defaultWarehouse",
      "accountingAccount",
      "thirdPartyProduct",
      "customerReference",
    ],
  },
];

function fieldLabel(path: string): string {
  return PRC_FIELD_LABELS[path] || path;
}

/** UI-FIX-07 — leitura da ficha delegada à composição única do kit;
 * aqui ficam apenas os adornos do perfil Engenharia (flags de
 * acompanhamento e ação «Editar ficha»). */
function PrcTechnicalSheetRead({
  detail,
  draft,
  changedPaths,
  changedReasons,
  specByPath,
  enterEdit,
}: {
  detail: PrcRequestDetail;
  draft: Record<string, unknown>;
  changedPaths: Set<string>;
  changedReasons: Map<string, string>;
  specByPath: Map<string, PrcFieldSpec>;
  enterEdit: () => void;
}) {
  const { flags, openTarget } = usePrcFlagsContext();

  return (
    <PrcTechnicalSheetView
      draft={draft}
      requestType={detail.requestType === "update" ? "update" : "create"}
      changedPaths={Array.from(changedPaths).map((p) => ({
        path: p,
        reason: changedReasons.get(p) || "",
      }))}
      supplierLinkChanges={
        (detail.requestedChanges?.supplierLinkChanges as
          | PrcSheetLinkOp[]
          | undefined) || null
      }
      baselineLinks={detail.officialBaseline?.links || null}
      specNotes={Object.fromEntries(
        Array.from(specByPath, ([p, s]) => [p, s.note]),
      )}
      baselineFields={
        (detail.officialBaseline?.fields as
          | Record<string, unknown>
          | undefined) || null
      }
      suppliersHeaderActions={
        detail.allowedActions.includes("edit_draft") ? (
          <EngineeringActionButton variant="ghost" onClick={enterEdit}>
            Editar ficha
          </EngineeringActionButton>
        ) : undefined
      }
      fieldAdornment={(p, displayValue) => (
        <PrcFieldFlagTrigger
          openFlag={findOpenFieldFlag(flags, p)}
          resolvedFlags={findResolvedFieldFlags(flags, p)}
          label={fieldLabel(p)}
          onOpen={(flag) =>
            openTarget(
              {
                subject: "FIELD",
                targetPath: p,
                fieldLabel: fieldLabel(p),
                currentValue: displayValue,
              },
              flag,
            )
          }
        />
      )}
      supplierAdornment={(r, attribute) => (
        <PrcFieldFlagTrigger
          openFlag={findOpenSupplierFlag(
            flags,
            r.supplierCode,
            r.store,
            attribute,
          )}
          resolvedFlags={findResolvedSupplierFlags(
            flags,
            r.supplierCode,
            r.store,
            attribute,
          )}
          label={`${PRC_SUPPLIER_LABELS[attribute]} ${r.supplierCode}`}
          onOpen={(flag) =>
            openTarget(
              {
                subject: "SUPPLIER_LINK",
                targetAttribute: attribute,
                supplierKey: {
                  supplierCode: r.supplierCode,
                  store: r.store,
                },
                currentValue: String(r[attribute] || ""),
              },
              flag,
            )
          }
        />
      )}
    />
  );
}

export function PrcTechnicalSheet({
  detail,
  fieldSpecs,
  editablePaths,
  editing,
  busy,
  focusElementId,
  focusNonce = 0,
  onStartEdit,
  onCancelEdit,
  onSave,
  onSaveReturned,
  correctionFieldErrors,
}: {
  detail: PrcRequestDetail;
  fieldSpecs: PrcFieldSpec[] | null;
  editablePaths: string[] | null;
  editing: boolean;
  busy: boolean;
  /** PRC-REF-020-UX-01 — id DOM do alvo a destacar (campo/SA5). */
  focusElementId?: string | null;
  focusNonce?: number;
  onStartEdit: () => void;
  onCancelEdit: () => void;
  onSave: (
    changes: Array<{ path: string; proposedValue: unknown; reason: string }>,
  ) => void;
  /** PRC-REF-022 — patch allowlisted do solicitante. */
  onSaveReturned?: (changes: PrcReturnedFieldChange[]) => void;
  /** FIX-12 — erros de campo vindos do backend (data.fields mapeados
   * para targetKeys) exibidos junto ao editor da correção. */
  correctionFieldErrors?: PrcCorrectionTargetErrors;
}) {
  const draft = detail.technicalDraft || {};
  const correctionMode =
    detail.status === "needs_correction" &&
    Boolean(detail.correctionExchange?.canCorrect);
  const openReturn = detail.correctionExchange?.openReturn;
  useEffect(() => {
    if (!focusElementId) return;
    const timer = window.setTimeout(() => {
      const el =
        document.getElementById(focusElementId) ||
        document.getElementById(
          focusElementId.replace("prc-field-", "prc-edit-"),
        );
      if (!el) return;
      el.classList.add("engineering-prc__nav-focus");
      el.scrollIntoView({ behavior: "smooth", block: "center" });
      if (el instanceof HTMLElement) {
        const focusable = el.querySelector<HTMLElement>(
          "input,select,textarea,button,[tabindex]",
        );
        (focusable || el).focus?.({ preventScroll: true });
      }
      window.setTimeout(() => {
        el.classList.remove("engineering-prc__nav-focus");
      }, 4000);
    }, 80);
    return () => window.clearTimeout(timer);
  }, [focusElementId, focusNonce, editing, detail.id]);

  const changedPaths = useMemo(
    () => new Set((detail.changedPaths || []).map((c) => c.path)),
    [detail],
  );
  const changedReasons = useMemo(
    () =>
      new Map(
        (detail.changedPaths || []).map((c) => [c.path, c.reason] as const),
      ),
    [detail],
  );

  const specByPath = useMemo(
    () => new Map((fieldSpecs || []).map((s) => [s.path, s] as const)),
    [fieldSpecs],
  );
  const editable = useMemo(
    () => new Set(editablePaths || []),
    [editablePaths],
  );

  /* Estado de edição — por path selecionado: novo valor + motivo. */
  const [editValues, setEditValues] = useState<Record<string, string>>({});
  const [editReasons, setEditReasons] = useState<Record<string, string>>({});
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [suppliersDraft, setSuppliersDraft] = useState<SupplierRow[] | null>(
    null,
  );
  const [supplierReason, setSupplierReason] = useState("");
  const [formError, setFormError] = useState("");

  const enterEdit = () => {
    setSelected(new Set());
    setEditValues({});
    setEditReasons({});
    setSuppliersDraft(null);
    setSupplierReason("");
    setFormError("");
    onStartEdit();
  };

  const togglePath = (path: string, checked: boolean) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (checked) {
        next.add(path);
        setEditValues((v) => ({
          ...v,
          [path]:
            scalarText(draft[path]) === "—"
              ? ""
              : String(draft[path] ?? ""),
        }));
      } else {
        next.delete(path);
      }
      return next;
    });
  };

  const isUpdate = detail.requestType === "update";
  const sheetEditing = editing || correctionMode;

  const currentScalar = (path: string) =>
    scalarText(draft[path]) === "—" ? "" : String(draft[path] ?? "");

  const isDirty = (path: string) =>
    String(editValues[path] ?? "") !== currentScalar(path);

  const save = () => {
    const changes: Array<{
      path: string;
      proposedValue: unknown;
      reason: string;
    }> = [];
    for (const path of selected) {
      if (!isDirty(path) && isUpdate) {
        continue;
      }
      const reason = (editReasons[path] || "").trim();
      if (!reason) {
        setFormError(`Informe a justificativa para «${fieldLabel(path)}».`);
        return;
      }
      changes.push({
        path,
        proposedValue: editValues[path] ?? "",
        reason,
      });
    }
    if (suppliersDraft !== null) {
      const reason = supplierReason.trim();
      if (!reason) {
        setFormError("Informe a justificativa da alteração de fornecedores.");
        return;
      }
      const missing = suppliersDraft.findIndex(
        (r) =>
          !r.supplierCode.trim() ||
          !r.store.trim() ||
          !r.supplierName.trim() ||
          !r.partNumber.trim(),
      );
      if (missing >= 0) {
        setFormError(
          `Fornecedor ${missing + 1}: código, loja, nome e Part Number são obrigatórios.`,
        );
        return;
      }
      changes.push({
        path: "suppliers",
        proposedValue: supplierRowsToPayload(suppliersDraft),
        reason,
      });
    }
    if (!changes.length) {
      setFormError(
        isUpdate
          ? "Altere ao menos um campo marcado antes de salvar."
          : "Selecione ao menos um campo para alterar.",
      );
      return;
    }
    setFormError("");
    onSave(changes);
  };

  const scalarPaths = FIELD_GROUPS.flatMap((g) => g.paths).filter(
    (p) => p !== "suppliers",
  );

  return (
    <div className="engineering-prc__sheet">
      {!sheetEditing ? (
        <PrcAttendanceFlagsProvider requestId={detail.id}>
          <PrcAttendanceFlagsSummary />
          <PrcTechnicalSheetRead
            detail={detail}
            draft={draft}
            changedPaths={changedPaths}
            changedReasons={changedReasons}
            specByPath={specByPath}
            enterEdit={
              detail.allowedActions.includes("edit_draft")
                ? enterEdit
                : () => undefined
            }
          />
        </PrcAttendanceFlagsProvider>
      ) : correctionMode ? (
        /* CORRECTION-10 — o editor da correção é o componente
         * compartilhado do kit (mesmo renderer de Minhas Solicitações):
         * alvos oficiais devolvidos, identidade de vínculo, modos
         * changed/confirmed e payload do contrato /returned-fields. */
        <EngineeringDetailCard
          title="Corrigir campos devolvidos"
          hint="Somente os campos devolvidos são editáveis. Confirme ou altere cada um."
        >
          <PrcReturnedFieldsEditor
            targets={openReturn?.targets || []}
            fieldSpecs={fieldSpecs || []}
            draft={draft}
            busy={busy}
            idPrefix="eng-prc-correct"
            externalErrors={correctionFieldErrors}
            onSubmit={(changes) => onSaveReturned?.(changes)}
          />
        </EngineeringDetailCard>
      ) : (
        <EngineeringDetailCard
          title={
            isUpdate
              ? "Edição seletiva da ficha"
              : "Editar ficha técnica"
          }
          hint={
            isUpdate
              ? "Marque somente os campos a alterar — valores atuais já vêm preenchidos."
              : "Ajuste os campos com os valores atuais preenchidos. Justificativa só quando houver mudança."
          }
        >
          <div className="engineering-prc__edit-list">
            {scalarPaths
              .filter((p) => p !== "officialProductCode")
              .map((p) => {
                const spec = specByPath.get(p);
                const allowed = editable.size ? editable.has(p) : true;
                const picked = selected.has(p);
                const dirty = isDirty(p);
                return (
                  <div key={p} className="engineering-prc__edit-row">
                    {isUpdate ? (
                      <EngineeringCheckboxControl
                        checked={picked}
                        disabled={!allowed || busy}
                        onChange={(v) => togglePath(p, v)}
                        label={fieldLabel(p)}
                        hint={prcFieldHelp(p, spec?.note)}
                      />
                    ) : (
                      <span className="engineering-prc__edit-row-label">
                        {fieldLabel(p)}
                      </span>
                    )}
                    {isUpdate && !picked ? (
                      <span className="engineering-prc__muted">
                        {scalarText(draft[p])} — não alterado
                      </span>
                    ) : (
                      <div className="engineering-prc__edit-controls">
                        {spec?.enumValues?.length ? (
                          <EngineeringSelectField
                            id={`prc-edit-${p}`}
                            label={fieldLabel(p)}
                            value={
                              editValues[p] ?? String(draft[p] ?? "")
                            }
                            onChange={(v) =>
                              setEditValues((s) => ({ ...s, [p]: v }))
                            }
                            options={spec.enumValues.map((v) => ({
                              value: v,
                              label: v,
                            }))}
                            disabled={busy}
                          />
                        ) : (
                          <EngineeringTextField
                            id={`prc-edit-${p}`}
                            label={fieldLabel(p)}
                            hint={prcFieldHelp(p, spec?.note)}
                            value={
                              editValues[p] ?? currentScalar(p)
                            }
                            onChange={(v) =>
                              setEditValues((s) => ({ ...s, [p]: v }))
                            }
                            maxLength={spec?.maxLength}
                            disabled={busy}
                          />
                        )}
                        {dirty ? (
                          <EngineeringTextField
                            id={`prc-edit-reason-${p}`}
                            label="Justificativa da alteração"
                            value={editReasons[p] ?? ""}
                            onChange={(v) =>
                              setEditReasons((s) => ({ ...s, [p]: v }))
                            }
                            required={dirty}
                            maxLength={500}
                            disabled={busy}
                          />
                        ) : null}
                      </div>
                    )}
                  </div>
                );
              })}
          </div>

          <div className="engineering-prc__edit-suppliers">
            <div className="engineering-prc__edit-suppliers-head">
              <strong>Fornecedores</strong>
              {suppliersDraft === null ? (
                <EngineeringActionButton
                  variant="ghost"
                  disabled={!editable.has("suppliers") && editable.size > 0}
                  onClick={() =>
                    setSuppliersDraft(toSupplierRows(draft.suppliers))
                  }
                >
                  Alterar fornecedores
                </EngineeringActionButton>
              ) : null}
            </div>
            {suppliersDraft !== null ? (
              <>
                {suppliersDraft.map((row, index) => {
                  return (
                    <div
                      key={index}
                      className="engineering-prc__supplier-row"
                    >
                      <EngineeringTextField
                        id={`prc-sup-code-${index}`}
                        label={PRC_SUPPLIER_LABELS.supplierCode}
                        value={row.supplierCode}
                        onChange={(v) =>
                          setSuppliersDraft((rows) =>
                            rows!.map((r, i) =>
                              i === index ? { ...r, supplierCode: v } : r,
                            ),
                          )
                        }
                        required
                        disabled={busy}
                      />
                      <EngineeringTextField
                        id={`prc-sup-store-${index}`}
                        label={PRC_SUPPLIER_LABELS.store}
                        value={row.store}
                        onChange={(v) =>
                          setSuppliersDraft((rows) =>
                            rows!.map((r, i) =>
                              i === index ? { ...r, store: v } : r,
                            ),
                          )
                        }
                        required
                        disabled={busy}
                      />
                      <EngineeringTextField
                        id={`prc-sup-name-${index}`}
                        label={PRC_SUPPLIER_LABELS.supplierName}
                        value={row.supplierName}
                        onChange={(v) =>
                          setSuppliersDraft((rows) =>
                            rows!.map((r, i) =>
                              i === index ? { ...r, supplierName: v } : r,
                            ),
                          )
                        }
                        required
                        disabled={busy}
                      />
                      <EngineeringTextField
                        id={`prc-sup-pn-${index}`}
                        label={PRC_SUPPLIER_LABELS.partNumber}
                        hint={PRC_SUPPLIER_HELP.partNumberHint}
                        value={row.partNumber}
                        onChange={(v) =>
                          setSuppliersDraft((rows) =>
                            rows!.map((r, i) =>
                              i === index ? { ...r, partNumber: v } : r,
                            ),
                          )
                        }
                        required
                        disabled={busy}
                      />
                      <EngineeringTextField
                        id={`prc-sup-cat-${index}`}
                        label={`${PRC_SUPPLIER_LABELS.catalogNumber} (opcional)`}
                        value={row.catalogNumber}
                        onChange={(v) =>
                          setSuppliersDraft((rows) =>
                            rows!.map((r, i) =>
                              i === index ? { ...r, catalogNumber: v } : r,
                            ),
                          )
                        }
                        disabled={busy}
                      />
                      <EngineeringActionButton
                        variant="ghost"
                        disabled={busy}
                        onClick={() =>
                          setSuppliersDraft((rows) =>
                            rows!.filter((_, i) => i !== index),
                          )
                        }
                      >
                        Remover
                      </EngineeringActionButton>
                    </div>
                  );
                })}
                <div className="engineering-prc__supplier-add">
                    <EngineeringActionButton
                      variant="ghost"
                      disabled={busy}
                      onClick={() =>
                        setSuppliersDraft((rows) => [
                          ...(rows || []),
                          emptySupplierRow(),
                        ])
                      }
                    >
                      + Adicionar fornecedor
                    </EngineeringActionButton>
                  </div>
                <EngineeringTextField
                  id="prc-sup-reason"
                  label="Justificativa da alteração de fornecedores"
                  value={supplierReason}
                  onChange={setSupplierReason}
                  required
                  maxLength={500}
                  disabled={busy}
                />
              </>
            ) : null}
          </div>

          {formError ? (
            <EngineeringStateBanner variant="error">
              {formError}
            </EngineeringStateBanner>
          ) : null}

          <EngineeringFormActions align="end">
            <EngineeringActionButton
              variant="ghost"
              softDisabled={busy}
              onClick={onCancelEdit}
            >
              Cancelar
            </EngineeringActionButton>
            <EngineeringActionButton
              variant="primary"
              softDisabled={busy}
              onClick={save}
            >
              Salvar alterações
            </EngineeringActionButton>
          </EngineeringFormActions>
        </EngineeringDetailCard>
      )}
    </div>
  );
}
