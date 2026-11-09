/** Ficha técnica — leitura agrupada por assunto + edição seletiva
 * (PATCH campo-a-campo com motivo e CAS). `suppliers` é delta de
 * relação produto×fornecedor: a lista completa editada é enviada como
 * valor proposto do path `suppliers`, conforme contrato de draft. */

import { useMemo, useState } from "react";

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
  onStartEdit,
  onCancelEdit,
  onSave,
}: {
  detail: PrcRequestDetail;
  fieldSpecs: PrcFieldSpec[] | null;
  editablePaths: string[] | null;
  editing: boolean;
  busy: boolean;
  onStartEdit: () => void;
  onCancelEdit: () => void;
  onSave: (
    changes: Array<{ path: string; proposedValue: unknown; reason: string }>,
  ) => void;
}) {
  const draft = detail.technicalDraft || {};
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
          [path]: scalarText(draft[path]) === "—" ? "" : String(draft[path] ?? ""),
        }));
      } else {
        next.delete(path);
      }
      return next;
    });
  };

  const isUpdate = detail.requestType === "update";

  const save = () => {
    const changes: Array<{
      path: string;
      proposedValue: unknown;
      reason: string;
    }> = [];
    for (const path of selected) {
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
        (r) => !r.supplierCode.trim() || !r.store.trim() || !r.supplierName.trim(),
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
      setFormError("Selecione ao menos um campo para alterar.");
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
      {!editing ? (
        <PrcAttendanceFlagsProvider requestId={detail.id}>
          <PrcAttendanceFlagsSummary />
          <PrcTechnicalSheetRead
            detail={detail}
            draft={draft}
            changedPaths={changedPaths}
            changedReasons={changedReasons}
            specByPath={specByPath}
            enterEdit={enterEdit}
          />
        </PrcAttendanceFlagsProvider>
      ) : (
        <EngineeringDetailCard
          title={isUpdate ? "Edição seletiva da ficha" : "Editar ficha técnica"}
          hint={
            isUpdate
              ? "Marque somente os campos a alterar — campos não marcados não são enviados."
              : "Ajuste os campos e informe a justificativa de cada alteração."
          }
        >
          <div className="engineering-prc__edit-list">
            {scalarPaths
              .filter((p) => p !== "officialProductCode")
              .map((p) => {
                const spec = specByPath.get(p);
                const allowed = editable.size ? editable.has(p) : true;
                const picked = selected.has(p);
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
                            label={`Novo valor — ${fieldLabel(p)}`}
                            value={editValues[p] ?? String(draft[p] ?? "")}
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
                            label={`Novo valor — ${fieldLabel(p)}`}
                            hint={prcFieldHelp(p, spec?.note)}
                            value={editValues[p] ?? ""}
                            onChange={(v) =>
                              setEditValues((s) => ({ ...s, [p]: v }))
                            }
                            maxLength={spec?.maxLength}
                            disabled={busy}
                          />
                        )}
                        <EngineeringTextField
                          id={`prc-edit-reason-${p}`}
                          label="Justificativa"
                          value={editReasons[p] ?? ""}
                          onChange={(v) =>
                            setEditReasons((s) => ({ ...s, [p]: v }))
                          }
                          required
                          maxLength={500}
                          disabled={busy}
                        />
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
