/** Ficha técnica — leitura agrupada por assunto + edição seletiva
 * (PATCH campo-a-campo com motivo e CAS). `suppliers` é delta de
 * relação produto×fornecedor: a lista completa editada é enviada como
 * valor proposto do path `suppliers`, conforme contrato de draft. */

import { useEffect, useMemo, useState } from "react";

import {
  EngineeringActionButton,
  EngineeringCheckboxControl,
  EngineeringDetailCard,
  EngineeringFieldLabel,
  EngineeringFormActions,
  EngineeringSelectField,
  EngineeringStateBanner,
  EngineeringTextField,
} from "../../../ui/engineeringUi";
import type { DataTableColumn } from "../../lmps/components/dataTableUi";
import { DataTableSection } from "../../lmps/components/DataTableSection";
import type {
  PrcFieldSpec,
  PrcRequestDetail,
  PrcReturnedFieldChange,
} from "../api/productRegistrationApi";
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
    <>
      {FIELD_GROUPS.map((group) => {
        const paths = group.paths.filter(
          (p) => p in draft || p === "officialProductCode",
        );
        if (!paths.length) return null;
        return (
          <EngineeringDetailCard key={group.title} title={group.title}>
            <div className="engineering-prc__flagged-grid">
              {paths.map((p) => {
                const openFlag =
                  p === "officialProductCode"
                    ? undefined
                    : findOpenFieldFlag(flags, p);
                const resolvedFlags =
                  p === "officialProductCode"
                    ? []
                    : findResolvedFieldFlags(flags, p);
                const label = fieldLabel(p);
                return (
                  <div
                    key={p}
                    id={`prc-field-${p}`}
                    tabIndex={-1}
                    className={
                      p === "description"
                        ? "engineering-prc__flagged-field engineering-prc__flagged-field--wide"
                        : "engineering-prc__flagged-field"
                    }
                  >
                    <div className="engineering-prc__flagged-field-label">
                      <EngineeringFieldLabel
                        label={label}
                        hint={prcFieldHelp(p, specByPath.get(p)?.note)}
                      />
                      {p !== "officialProductCode" ? (
                        <PrcFieldFlagTrigger
                          openFlag={openFlag}
                          resolvedFlags={resolvedFlags}
                          label={label}
                          onOpen={(flag) =>
                            openTarget(
                              {
                                subject: "FIELD",
                                targetPath: p,
                                fieldLabel: label,
                                currentValue: scalarText(draft[p]),
                              },
                              flag,
                            )
                          }
                        />
                      ) : null}
                    </div>
                    <div className="engineering-prc__flagged-field-value">
                      {scalarText(draft[p])}
                    </div>
                  </div>
                );
              })}
            </div>
            {group.paths.some((p) => changedPaths.has(p)) ? (
              <ul className="engineering-prc__change-notes">
                {group.paths
                  .filter((p) => changedPaths.has(p))
                  .map((p) => (
                    <li key={p}>
                      <strong>{fieldLabel(p)}</strong> — alterado:{" "}
                      {changedReasons.get(p)}
                    </li>
                  ))}
              </ul>
            ) : null}
          </EngineeringDetailCard>
        );
      })}

      <EngineeringDetailCard
        title="Fornecedores"
        headerActions={
          detail.allowedActions.includes("edit_draft") ? (
            <EngineeringActionButton variant="ghost" onClick={enterEdit}>
              Editar ficha
            </EngineeringActionButton>
          ) : undefined
        }
      >
        {toSupplierRows(draft.suppliers).length ? (
          <DataTableSection
            title="Vínculos produto × fornecedor"
            columns={
              [
                {
                  key: "supplierCode",
                  header: PRC_SUPPLIER_LABELS.supplierCode,
                  render: (r: SupplierRow) => r.supplierCode,
                },
                {
                  key: "store",
                  header: PRC_SUPPLIER_LABELS.store,
                  render: (r) => r.store,
                },
                {
                  key: "supplierName",
                  header: PRC_SUPPLIER_LABELS.supplierName,
                  render: (r) => r.supplierName,
                },
                {
                  key: "partNumber",
                  header: `${PRC_SUPPLIER_LABELS.partNumber} (opcional)`,
                  headerHint:
                    PRC_SUPPLIER_HELP.partNumberHint,
                  render: (r) => {
                    const openFlag = findOpenSupplierFlag(
                      flags,
                      r.supplierCode,
                      r.store,
                      "partNumber",
                    );
                    const resolvedFlags = findResolvedSupplierFlags(
                      flags,
                      r.supplierCode,
                      r.store,
                      "partNumber",
                    );
                    return (
                      <span
                        id={`prc-supplier-${r.supplierCode}-${r.store}-partNumber`}
                        className="engineering-prc__supplier-flag-cell"
                      >
                        {r.partNumber || "—"}
                        <PrcFieldFlagTrigger
                          openFlag={openFlag}
                          resolvedFlags={resolvedFlags}
                          label={`${PRC_SUPPLIER_LABELS.partNumber} ${r.supplierCode}`}
                          onOpen={(flag) =>
                            openTarget(
                              {
                                subject: "SUPPLIER_LINK",
                                targetAttribute: "partNumber",
                                supplierKey: {
                                  supplierCode: r.supplierCode,
                                  store: r.store,
                                },
                                currentValue: r.partNumber || "",
                              },
                              flag,
                            )
                          }
                        />
                      </span>
                    );
                  },
                },
                {
                  key: "catalogNumber",
                  header: PRC_SUPPLIER_LABELS.catalogNumber,
                  render: (r) => {
                    const openFlag = findOpenSupplierFlag(
                      flags,
                      r.supplierCode,
                      r.store,
                      "catalogNumber",
                    );
                    const resolvedFlags = findResolvedSupplierFlags(
                      flags,
                      r.supplierCode,
                      r.store,
                      "catalogNumber",
                    );
                    return (
                      <span
                        id={`prc-supplier-${r.supplierCode}-${r.store}-catalogNumber`}
                        className="engineering-prc__supplier-flag-cell"
                      >
                        {r.catalogNumber || "—"}
                        <PrcFieldFlagTrigger
                          openFlag={openFlag}
                          resolvedFlags={resolvedFlags}
                          label={`${PRC_SUPPLIER_LABELS.catalogNumber} ${r.supplierCode}`}
                          onOpen={(flag) =>
                            openTarget(
                              {
                                subject: "SUPPLIER_LINK",
                                targetAttribute: "catalogNumber",
                                supplierKey: {
                                  supplierCode: r.supplierCode,
                                  store: r.store,
                                },
                                currentValue: r.catalogNumber || "",
                              },
                              flag,
                            )
                          }
                        />
                      </span>
                    );
                  },
                },
              ] as DataTableColumn<SupplierRow>[]
            }
            rows={toSupplierRows(draft.suppliers)}
            rowKey={(r) => `${r.supplierCode}.${r.store}.${r.partNumber}`}
            hideSearch
            emptyMessage="Nenhum fornecedor vinculado."
          />
        ) : (
          <p className="engineering-prc__muted">
            Nenhum fornecedor vinculado.
          </p>
        )}
        {changedPaths.has("suppliers") ? (
          <p className="engineering-prc__change-notes">
            <strong>Fornecedores</strong> — alterado:{" "}
            {changedReasons.get("suppliers")}
          </p>
        ) : null}
      </EngineeringDetailCard>
    </>
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
}) {
  const draft = detail.technicalDraft || {};
  const correctionMode =
    detail.status === "needs_correction" &&
    Boolean(detail.correctionExchange?.canCorrect);
  const openReturn = detail.correctionExchange?.openReturn;
  const returnedPaths = useMemo(() => {
    const paths = new Set<string>();
    for (const t of openReturn?.targets || []) {
      if (t.targetType === "FIELD" && t.targetPath) paths.add(t.targetPath);
      if (t.targetType === "SUPPLIER_LINK") paths.add("suppliers");
    }
    return paths;
  }, [openReturn]);
  const returnReasonByPath = useMemo(() => {
    const map = new Map<string, string>();
    for (const t of openReturn?.targets || []) {
      if (t.targetType === "FIELD" && t.targetPath) {
        map.set(t.targetPath, t.reason);
      }
      if (t.targetType === "SUPPLIER_LINK") {
        map.set("suppliers", t.reason);
      }
    }
    return map;
  }, [openReturn]);

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

  useEffect(() => {
    if (!correctionMode) return;
    const values: Record<string, string> = {};
    for (const path of returnedPaths) {
      if (path === "suppliers") continue;
      values[path] =
        scalarText(draft[path]) === "—" ? "" : String(draft[path] ?? "");
    }
    setSelected(new Set(returnedPaths));
    setEditValues(values);
    setSuppliersDraft(
      returnedPaths.has("suppliers")
        ? toSupplierRows(draft.suppliers)
        : null,
    );
  }, [correctionMode, returnedPaths, detail.id, detail.caseVersion]);

  const enterEdit = () => {
    if (correctionMode) {
      const preselected = new Set(returnedPaths);
      const values: Record<string, string> = {};
      for (const path of preselected) {
        if (path === "suppliers") continue;
        values[path] =
          scalarText(draft[path]) === "—" ? "" : String(draft[path] ?? "");
      }
      setSelected(preselected);
      setEditValues(values);
      setEditReasons({});
      setSuppliersDraft(
        returnedPaths.has("suppliers")
          ? toSupplierRows(draft.suppliers)
          : null,
      );
      setSupplierReason("");
      setFormError("");
      onStartEdit();
      return;
    }
    setSelected(new Set());
    setEditValues({});
    setEditReasons({});
    setSuppliersDraft(null);
    setSupplierReason("");
    setFormError("");
    onStartEdit();
  };

  const togglePath = (path: string, checked: boolean) => {
    if (correctionMode) return;
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
    if (correctionMode) {
      const changes: PrcReturnedFieldChange[] = [];
      for (const path of selected) {
        if (path === "suppliers") continue;
        const reason =
          (editReasons[path] || "").trim() ||
          returnReasonByPath.get(path) ||
          "";
        const dirty = isDirty(path);
        if (!dirty) {
          if (reason.length < 3) {
            setFormError(
              `Confirme «${fieldLabel(path)}» com uma justificativa (mín. 3).`,
            );
            return;
          }
          changes.push({
            path,
            proposedValue: draft[path],
            reason,
            mode: "confirmed",
          });
          continue;
        }
        if (reason.length < 3) {
          setFormError(
            `Informe a justificativa para «${fieldLabel(path)}».`,
          );
          return;
        }
        changes.push({
          path,
          proposedValue: editValues[path] ?? "",
          reason,
          mode: "changed",
        });
      }
      if (suppliersDraft !== null && selected.has("suppliers")) {
        const reason =
          supplierReason.trim() || returnReasonByPath.get("suppliers") || "";
        if (reason.length < 3) {
          setFormError("Informe a justificativa dos fornecedores.");
          return;
        }
        changes.push({
          path: "suppliers",
          proposedValue: supplierRowsToPayload(suppliersDraft),
          reason,
          mode: "changed",
        });
      }
      if (!changes.length) {
        setFormError("Nenhuma correção para salvar.");
        return;
      }
      setFormError("");
      onSaveReturned?.(changes);
      return;
    }

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
          !r.supplierName.trim(),
      );
      if (missing >= 0) {
        setFormError(
          `Fornecedor ${missing + 1}: código, loja e nome são obrigatórios.`,
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
          {correctionMode ? (
            <EngineeringStateBanner variant="error">
              {`A Engenharia solicitou correção em ${returnedPaths.size} campo(s). Use Editar ficha técnica ou corrija abaixo.`}
              <EngineeringActionButton
                variant="primary"
                softDisabled={busy}
                onClick={enterEdit}
              >
                Corrigir campos devolvidos
              </EngineeringActionButton>
            </EngineeringStateBanner>
          ) : null}
          <PrcTechnicalSheetRead
            detail={detail}
            draft={draft}
            changedPaths={changedPaths}
            changedReasons={changedReasons}
            specByPath={specByPath}
            enterEdit={
              detail.allowedActions.includes("edit_draft") || correctionMode
                ? enterEdit
                : () => undefined
            }
          />
        </PrcAttendanceFlagsProvider>
      ) : (
        <EngineeringDetailCard
          title={
            correctionMode
              ? "Corrigir campos devolvidos"
              : isUpdate
                ? "Edição seletiva da ficha"
                : "Editar ficha técnica"
          }
          hint={
            correctionMode
              ? "Somente os campos devolvidos são editáveis. Confirme ou altere cada um."
              : isUpdate
                ? "Marque somente os campos a alterar — valores atuais já vêm preenchidos."
                : "Ajuste os campos com os valores atuais preenchidos. Justificativa só quando houver mudança."
          }
        >
          <div className="engineering-prc__edit-list">
            {scalarPaths
              .filter((p) => p !== "officialProductCode")
              .filter((p) => (correctionMode ? returnedPaths.has(p) : true))
              .map((p) => {
                const spec = specByPath.get(p);
                const allowed = editable.size ? editable.has(p) : true;
                const picked = selected.has(p);
                const dirty = isDirty(p);
                return (
                  <div key={p} className="engineering-prc__edit-row">
                    {isUpdate && !correctionMode ? (
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
                    {correctionMode && returnReasonByPath.get(p) ? (
                      <p className="engineering-prc__change-notes">
                        Motivo: {returnReasonByPath.get(p)}
                      </p>
                    ) : null}
                    {isUpdate && !correctionMode && !picked ? (
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
                        {dirty || correctionMode ? (
                          <EngineeringTextField
                            id={`prc-edit-reason-${p}`}
                            label={
                              correctionMode && !dirty
                                ? "Confirmação / justificativa"
                                : "Justificativa da alteração"
                            }
                            value={editReasons[p] ?? ""}
                            onChange={(v) =>
                              setEditReasons((s) => ({ ...s, [p]: v }))
                            }
                            required={dirty || correctionMode}
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
              {suppliersDraft === null && !correctionMode ? (
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
                {suppliersDraft.map((row, index) => (
                  <div key={index} className="engineering-prc__supplier-row">
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
                      label={`${PRC_SUPPLIER_LABELS.partNumber} (opcional)`}
                      hint={PRC_SUPPLIER_HELP.partNumberHint}
                      value={row.partNumber}
                      onChange={(v) =>
                        setSuppliersDraft((rows) =>
                          rows!.map((r, i) =>
                            i === index ? { ...r, partNumber: v } : r,
                          ),
                        )
                      }
                      disabled={busy}
                    />
                    <EngineeringTextField
                      id={`prc-sup-cat-${index}`}
                      label={PRC_SUPPLIER_LABELS.catalogNumber}
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
                ))}
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
            {!correctionMode ? (
              <EngineeringActionButton
                variant="ghost"
                softDisabled={busy}
                onClick={onCancelEdit}
              >
                Cancelar
              </EngineeringActionButton>
            ) : null}
            <EngineeringActionButton
              variant="primary"
              softDisabled={busy}
              onClick={save}
            >
              {correctionMode
                ? "Salvar alterações"
                : "Salvar alterações"}
            </EngineeringActionButton>
          </EngineeringFormActions>
        </EngineeringDetailCard>
      )}
    </div>
  );
}
