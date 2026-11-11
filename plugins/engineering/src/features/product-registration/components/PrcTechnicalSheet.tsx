/** Ficha técnica — leitura agrupada por assunto + edição seletiva
 * (PATCH campo-a-campo com motivo e CAS). `suppliers` é delta de
 * relação produto×fornecedor: a lista completa editada é enviada como
 * valor proposto do path `suppliers`, conforme contrato de draft. */

import { useEffect, useMemo, useState } from "react";

import { PrcTechnicalSheetView } from "@delpi/plugin-ui/index";

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
      changedPaths={Array.from(changedPaths).map((p) => ({
        path: p,
        reason: changedReasons.get(p) || "",
      }))}
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

  /* PRC-REF-022-FIX-01 — granularidade por vínculo+atributo: mapa
   * `code|store` → atributos devolvidos + motivo por alvo. Alvo sem
   * `targetAttribute` (link integral) libera PN e Catálogo. */
  const returnedSupplierAttrs = useMemo(() => {
    const map = new Map<string, Set<string>>();
    for (const t of openReturn?.targets || []) {
      if (t.targetType !== "SUPPLIER_LINK" || !t.supplierKey) continue;
      const key = `${String(t.supplierKey.supplierCode || "").trim()}|${String(
        t.supplierKey.store || "",
      ).trim()}`;
      const set = map.get(key) || new Set<string>();
      if (t.targetAttribute) {
        set.add(t.targetAttribute);
      } else {
        set.add("partNumber");
        set.add("catalogNumber");
      }
      map.set(key, set);
    }
    return map;
  }, [openReturn]);
  const supplierAttrReasons = useMemo(() => {
    const map = new Map<string, string>();
    for (const t of openReturn?.targets || []) {
      if (t.targetType !== "SUPPLIER_LINK" || !t.supplierKey) continue;
      const key = `${String(t.supplierKey.supplierCode || "").trim()}|${String(
        t.supplierKey.store || "",
      ).trim()}|${t.targetAttribute || "link"}`;
      map.set(key, t.reason);
    }
    return map;
  }, [openReturn]);
  const supplierRowKey = (code: string, store: string) =>
    `${String(code || "").trim()}|${String(store || "").trim()}`;
  const supplierAttrEditable = (
    row: SupplierRow,
    attr: "partNumber" | "catalogNumber",
  ) =>
    !correctionMode ||
    Boolean(
      returnedSupplierAttrs
        .get(supplierRowKey(row.supplierCode, row.store))
        ?.has(attr),
    );

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
        /* PRC-REF-022-FIX-01 — somente atributos devolvidos podem mudar;
         * vínculo alterado exige Part Number válido. */
        const pnMissing = suppliersDraft.findIndex((r, i) => {
          const attrs = returnedSupplierAttrs.get(
            supplierRowKey(r.supplierCode, r.store),
          );
          const current = (toSupplierRows(draft.suppliers) || [])[i];
          const willChange = Boolean(
            attrs &&
              (Array.from(attrs) as Array<"partNumber" | "catalogNumber">)
                .some(
                  (attr) =>
                    String(r[attr] ?? "").trim() !==
                    String(current?.[attr] ?? "").trim(),
                ),
          );
          return willChange && !r.partNumber.trim();
        });
        if (pnMissing >= 0) {
          setFormError(
            `Fornecedor ${pnMissing + 1}: Part Number é obrigatório para alterar o vínculo.`,
          );
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
                {suppliersDraft.map((row, index) => {
                  const rowKey = supplierRowKey(
                    row.supplierCode,
                    row.store,
                  );
                  const returnedAttrs = correctionMode
                    ? returnedSupplierAttrs.get(rowKey)
                    : undefined;
                  const rowReasons =
                    correctionMode && returnedAttrs
                      ? (["partNumber", "catalogNumber"] as const)
                          .filter((a) => returnedAttrs.has(a))
                          .map(
                            (a) =>
                              `${PRC_SUPPLIER_LABELS[a]}: ${supplierAttrReasons.get(
                                `${rowKey}|${a}`,
                              ) || supplierAttrReasons.get(`${rowKey}|link`) || ""}`,
                          )
                          .filter((s) => !s.endsWith(": "))
                      : [];
                  return (
                    <div
                      key={index}
                      className="engineering-prc__supplier-row"
                    >
                      {rowReasons.length ? (
                        <p className="engineering-prc__change-notes">
                          Correção solicitada — {rowReasons.join(" · ")}
                        </p>
                      ) : null}
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
                        disabled={busy || correctionMode}
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
                        disabled={busy || correctionMode}
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
                        disabled={busy || correctionMode}
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
                        disabled={
                          busy || !supplierAttrEditable(row, "partNumber")
                        }
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
                        disabled={
                          busy || !supplierAttrEditable(row, "catalogNumber")
                        }
                      />
                      {!correctionMode ? (
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
                      ) : null}
                    </div>
                  );
                })}
                {!correctionMode ? (
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
                ) : null}
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
