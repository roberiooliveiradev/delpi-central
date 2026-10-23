import { useEffect, useMemo, useState } from "react";
import { Pencil } from "lucide-react";

import { navigatePluginView } from "../../app/pluginNavigation";
import { buildPluginPath } from "../../app/pluginRoutes";
import {
  SuppliesActionButton,
  SuppliesEmptyState,
  SuppliesLoadingCard,
  SuppliesModal,
  SuppliesPageHero,
  SuppliesPagePath,
  SuppliesSectionCard,
  SuppliesSectionHintLabel,
  SuppliesStateBanner,
  SuppliesStatusBadge,
} from "../../app/suppliesUi";
import { ApiRequestError } from "../../api/httpClient";
import { SP_HELP } from "../../content/helpTooltips";
import { getSupplier, updateSupplier } from "./api";
import { EnrichmentSection } from "./enrichment/EnrichmentSection";
import {
  SUPPLIERS_CONTENT as C,
  supplierPendingChangesLabel,
} from "./content";
import {
  SupplierCatalogField,
  SupplierCatalogViewValue,
  SupplierFieldInput,
  SupplierFieldGrid,
  SupplierFormActions,
  SupplierPostalCodeAssistant,
  SupplierProtectedField,
  SupplierReviewTable,
} from "./SupplierFormFields";
import {
  classifyWriteOutcome,
  diffEditableFields,
  draftFromDetail,
  formatTaxIdMasked,
  getSupplierFieldValue,
  groupChangesBySection,
  isSupplierFieldAvailable,
  personTypeLabel,
  supplierCatalogValueText,
  supplierFieldItemClass,
} from "./query";
import {
  SUPPLIER_FIELD_REGISTRY,
  SUPPLIER_FORM_SECTIONS,
  type SupplierDetail,
  type SupplierEditDraft,
  type SupplierEditableFieldKey,
  type SupplierWriteOutcome,
} from "./types";

type SupplierDetailPageProps = {
  basePath: string;
  code: string;
  store: string;
};

type WriteState = {
  outcome: SupplierWriteOutcome;
  message?: string;
  /** Changes sent on the last write — used by the post-write GET check. */
  submitted?: ReadonlyArray<{
    field: SupplierEditableFieldKey;
    after: string;
  }>;
  verifying?: boolean;
} | null;

const SECTION_LABELS: Record<string, string> = {
  identification: C.sectionIdentification,
  address: C.sectionAddress,
  contact: C.sectionContact,
  fiscal: C.sectionFiscal,
  purchasing: C.sectionPurchasing,
};

export function SupplierDetailPage({
  basePath,
  code,
  store,
}: SupplierDetailPageProps) {
  const [detail, setDetail] = useState<SupplierDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState<SupplierEditDraft>(
    {} as SupplierEditDraft,
  );
  const [reviewing, setReviewing] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [writeState, setWriteState] = useState<WriteState>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    setNotFound(false);
    getSupplier(code, store, controller.signal)
      .then((payload) => {
        setDetail(payload);
        setDraft(draftFromDetail(payload));
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setDetail(null);
        if (err instanceof ApiRequestError && err.status === 404) {
          setNotFound(true);
          return;
        }
        setError(err instanceof Error ? err.message : C.error);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [code, store, reloadKey]);

  const changes = useMemo(
    () => (detail ? diffEditableFields(detail, draft) : []),
    [detail, draft],
  );

  const dirty = changes.length > 0;

  const startEdit = () => {
    setWriteState(null);
    setEditing(true);
  };

  const cancelEdit = () => {
    setEditing(false);
    setReviewing(false);
    if (detail) setDraft(draftFromDetail(detail));
  };

  const confirmSubmit = () => {
    setReviewing(false);
    setSubmitting(true);
    const submitted = changes.map((c) => ({ field: c.field, after: c.after }));
    updateSupplier(code, store, changes)
      .then((response) => {
        const outcome = classifyWriteOutcome(response, 200);
        setWriteState({ outcome, submitted });
        if (outcome === "persistence_confirmed") {
          setEditing(false);
          setReloadKey((v) => v + 1);
        }
      })
      .catch((err: unknown) => {
        if (err instanceof ApiRequestError) {
          const outcome = classifyWriteOutcome(
            { outcome: err.outcome as SupplierWriteOutcome, code: err.code },
            err.status,
          );
          setWriteState({ outcome, message: err.message });
        } else {
          setWriteState({ outcome: "indeterminate" });
        }
      })
      .finally(() => setSubmitting(false));
  };

  /** GET posterior: compara os campos enviados com a ficha recarregada. */
  const verifyPersistence = () => {
    if (!writeState?.submitted?.length) return;
    setWriteState({ ...writeState, verifying: true });
    getSupplier(code, store)
      .then((fresh) => {
        const reflected = writeState.submitted!.every((change) => {
          const spec = SUPPLIER_FIELD_REGISTRY.find(
            (s) => s.key === change.field,
          );
          if (!spec) return false;
          return getSupplierFieldValue(fresh, spec).trim() === change.after;
        });
        setWriteState(
          reflected
            ? { outcome: "persistence_confirmed" }
            : {
                outcome: "acknowledged",
                submitted: writeState.submitted,
                message: C.verifyNotReflectedMessage,
              },
        );
        if (reflected) {
          setEditing(false);
          setReloadKey((v) => v + 1);
        }
      })
      .catch(() => setWriteState({ outcome: "indeterminate" }));
  };

  const listHref = buildPluginPath("suppliers", basePath);
  const goBack = (event?: { preventDefault: () => void }) => {
    event?.preventDefault();
    if (dirty && !window.confirm(C.unsavedChangesWarning)) return;
    navigatePluginView("suppliers", { basePath });
  };

  const identification = detail?.sections.identification ?? {};

  return (
    <div className="sp-page-stack sp-supplier-detail">
      <SuppliesPagePath
        back={{
          label: C.backToList,
          href: listHref,
          onNavigate: goBack,
        }}
        items={[]}
        current={
          detail
            ? `${code}/${store}`
            : C.detailTitle
        }
      />

      <SuppliesPageHero
        eyebrow={C.eyebrow}
        title={
          editing ? (
            C.editModeTitle
          ) : (
            <SuppliesSectionHintLabel
              label={
                identification.supplier_name?.toString() || `${code}/${store}`
              }
              hint={SP_HELP.suppliers}
            />
          )
        }
        description={
          editing
            ? `${identification.supplier_name?.toString() || C.detailTitle} · ${code}/${store}`
            : `${C.detailTitle} · ${code}/${store}`
        }
        actions={
          !editing && detail ? (
            <SuppliesActionButton
              type="button"
              variant="primary"
              onClick={startEdit}
              title={SP_HELP.suppliersEdit}
            >
              <Pencil size={16} aria-hidden="true" />
              <span>{C.editAction}</span>
            </SuppliesActionButton>
          ) : undefined
        }
      />

      {writeState ? (
        <WriteOutcomeBanner
          outcome={writeState.outcome}
          message={writeState.message}
          onVerify={
            writeState.outcome === "acknowledged" && writeState.submitted?.length
              ? verifyPersistence
              : undefined
          }
          verifying={writeState.verifying}
        />
      ) : null}

      {error ? (
        <div className="sp-supplier-detail__error">
          <SuppliesStateBanner variant="error">{error}</SuppliesStateBanner>
          <SuppliesActionButton
            type="button"
            variant="primary"
            onClick={() => setReloadKey((v) => v + 1)}
          >
            {C.retry}
          </SuppliesActionButton>
        </div>
      ) : null}

      {loading ? (
        <SuppliesLoadingCard title={C.detailLoading} variant="panel" />
      ) : null}

      {notFound ? (
        <SuppliesEmptyState
          title={C.detailNotFoundTitle}
          message={C.detailNotFoundMessage}
        />
      ) : null}

      {!loading && !error && detail ? (
        <>
          <div className="sp-supplier-detail__meta">
            <SuppliesStatusBadge
              variant={detail.blocked ? "danger" : "success"}
              label={detail.blocked ? "Bloqueado" : "Ativo"}
            />
            <span className="sp-supplier-detail__doc" title={SP_HELP.suppliersColTaxId}>
              {formatTaxIdMasked(detail.tax_id, detail.tax_id_masked)}
            </span>
            {personTypeLabel(
              identification.person_type?.toString() ?? "",
            ) ? (
              <span className="sp-supplier-detail__doc">
                {personTypeLabel(identification.person_type?.toString() ?? "")}
              </span>
            ) : null}
          </div>

          {editing ? (
            <p className="sp-supplier-detail__readonly-note">{C.editHint}</p>
          ) : null}

          {SUPPLIER_FORM_SECTIONS.map((section) => (
            <SuppliesSectionCard
              key={section.id}
              title={SECTION_LABELS[section.id]}
              hint={
                section.id === "identification"
                  ? SP_HELP.suppliersIdentification
                  : undefined
              }
            >
              {editing ? (
                <SupplierFieldGrid>
                  {section.fields.map((spec) => {
                    if (spec.put !== "editable") {
                      return (
                        <div
                          key={spec.key}
                          className={supplierFieldItemClass(spec)}
                        >
                          <SupplierProtectedField
                            label={spec.label}
                            value={getSupplierFieldValue(detail, spec)}
                            emptyLabel={C.fieldNotProvided}
                            unavailable={
                              !isSupplierFieldAvailable(detail, spec)
                            }
                            hint={[
                              spec.help,
                              spec.put === "protected"
                                ? C.protectedFieldHint
                                : C.readonlyFieldHint,
                            ]
                              .filter(Boolean)
                              .join(" ")}
                            protected={spec.put === "protected"}
                          />
                        </div>
                      );
                    }
                    const key = spec.key as SupplierEditableFieldKey;
                    const changed = changes.some((c) => c.field === key);
                    const derivedActive =
                      spec.catalogDerivedFrom === "city" &&
                      Boolean((draft.state ?? "").trim());
                    return (
                      <div
                        key={spec.key}
                        className={supplierFieldItemClass(spec, { changed })}
                      >
                        {spec.catalog ? (
                          <SupplierCatalogField
                            spec={spec}
                            value={
                              spec.key === "city"
                                ? (draft.city_code ?? "")
                                : (draft[key] ?? "")
                            }
                            currentLabel={
                              spec.key === "city" ? draft.city : undefined
                            }
                            dependsOnValue={
                              spec.catalogDependsOn
                                ? (draft[
                                    spec.catalogDependsOn as SupplierEditableFieldKey
                                  ] ?? "")
                                : undefined
                            }
                            codeFilter={
                              spec.catalogCodeParam
                                ? (
                                    getSupplierFieldValue(
                                      detail,
                                      SUPPLIER_FIELD_REGISTRY.find(
                                        (f) =>
                                          f.key === spec.catalogCodeParam,
                                      )!,
                                    ) ||
                                    (draft[
                                      spec.catalogCodeParam as SupplierEditableFieldKey
                                    ] ?? "")
                                  ).trim()
                                : undefined
                            }
                            onPick={(code, label, option) =>
                              setDraft((d) => {
                                const next = { ...d };
                                if (spec.key === "city") {
                                  next.city = label || code;
                                  next.city_code = code;
                                } else {
                                  next[key] = code;
                                }
                                if (
                                  spec.catalogPairField &&
                                  option?.store &&
                                  (spec.catalogPairField as SupplierEditableFieldKey) in
                                    next
                                ) {
                                  next[
                                    spec.catalogPairField as SupplierEditableFieldKey
                                  ] = option.store;
                                }
                                return next;
                              })
                            }
                            disabled={submitting}
                          />
                        ) : derivedActive ? (
                          <SupplierProtectedField
                            label={spec.label}
                            value={draft[key] ?? ""}
                            emptyLabel={C.fieldNotProvided}
                            hint={spec.help}
                          />
                        ) : spec.key === "postal_code" ? (
                          <SupplierPostalCodeAssistant
                            spec={spec}
                            value={draft.postal_code ?? ""}
                            onChange={(value) =>
                              setDraft((d) => ({
                                ...d,
                                postal_code: value,
                              }))
                            }
                            onApply={(patch) =>
                              setDraft((d) => ({ ...d, ...patch }))
                            }
                            current={{
                              address: draft.address ?? "",
                              district: draft.district ?? "",
                              city: draft.city ?? "",
                              state: draft.state ?? "",
                            }}
                            disabled={submitting}
                          />
                        ) : (
                          <SupplierFieldInput
                            spec={spec}
                            hint={
                              spec.key === "supplier_name"
                                ? SP_HELP.suppliersEditName
                                : spec.key === "supplier_short_name"
                                  ? SP_HELP.suppliersEditShortName
                                  : undefined
                            }
                            value={draft[key] ?? ""}
                            onChange={(value) =>
                              setDraft((d) => ({
                                ...d,
                                [key]: value,
                              }))
                            }
                            disabled={submitting}
                          />
                        )}
                      </div>
                    );
                  })}
                </SupplierFieldGrid>
              ) : (
                <dl className="sp-supplier-fields">
                  {section.fields.map((spec) => {
                    const value = getSupplierFieldValue(detail, spec);
                    const unavailable = !isSupplierFieldAvailable(
                      detail,
                      spec,
                    );
                    return (
                      <div
                        key={spec.key}
                        className={supplierFieldItemClass(spec)}
                      >
                        <dt>
                          {spec.help ? (
                            <SuppliesSectionHintLabel
                              label={spec.label}
                              hint={spec.help}
                            />
                          ) : (
                            spec.label
                          )}
                        </dt>
                        <dd
                          className={
                            unavailable ? "sp-supplier-value--unavailable" : ""
                          }
                        >
                          {value ? (
                            spec.catalog ? (
                              <SupplierCatalogViewValue
                                spec={spec}
                                value={value}
                                dependsOnValue={
                                  spec.catalogDependsOn
                                    ? getSupplierFieldValue(
                                        detail,
                                        SUPPLIER_FIELD_REGISTRY.find(
                                          (s) => s.key === spec.catalogDependsOn,
                                        )!,
                                      )
                                    : undefined
                                }
                              />
                            ) : (
                              value
                            )
                          ) : unavailable ? (
                            C.fieldUnavailable
                          ) : (
                            C.fieldNotProvided
                          )}
                        </dd>
                      </div>
                    );
                  })}
                </dl>
              )}
            </SuppliesSectionCard>
          ))}

          {editing ? (
            <SupplierFormActions
              counter={dirty ? supplierPendingChangesLabel(changes.length) : ""}
            >
              <SuppliesActionButton
                type="button"
                variant="ghost"
                onClick={cancelEdit}
                disabled={submitting}
              >
                {C.cancelAction}
              </SuppliesActionButton>
              <SuppliesActionButton
                type="button"
                variant="primary"
                onClick={() => setReviewing(true)}
                disabled={!dirty || submitting}
                title={dirty ? undefined : C.noChangesMessage}
              >
                {C.reviewAction}
              </SuppliesActionButton>
            </SupplierFormActions>
          ) : null}

          {!editing ? (
            <EnrichmentSection code={code} store={store} />
          ) : null}
        </>
      ) : null}

      <SuppliesModal
        open={reviewing}
        title={C.reviewTitle}
        onClose={() => setReviewing(false)}
        footer={
          <>
            <SuppliesActionButton
              type="button"
              variant="primary"
              onClick={confirmSubmit}
              disabled={submitting}
            >
              {C.confirmAction}
            </SuppliesActionButton>
            <SuppliesActionButton
              type="button"
              variant="ghost"
              onClick={() => setReviewing(false)}
              disabled={submitting}
            >
              {C.reviewBackAction}
            </SuppliesActionButton>
          </>
        }
      >
        {changes.length ? (
          <>
            <p className="sp-supplier-detail__readonly-note">
              {C.reviewEditDescription}
            </p>
            <SupplierReviewTable
              groups={groupChangesBySection(changes).map((group) => ({
                section: group.section,
                title: SECTION_LABELS[group.section],
                rows: group.changes.map((change) => {
                  const spec = SUPPLIER_FIELD_REGISTRY.find(
                    (s) => s.key === change.field,
                  );
                  return {
                    label: spec?.label ?? change.field,
                    before: supplierCatalogValueText(spec, change.before),
                    after: supplierCatalogValueText(spec, change.after),
                    help: spec?.help,
                  };
                }),
              }))}
              showBefore
            />
          </>
        ) : (
          <p>{C.noChangesMessage}</p>
        )}
      </SuppliesModal>
    </div>
  );
}

function WriteOutcomeBanner({
  outcome,
  message,
  onVerify,
  verifying,
}: {
  outcome: SupplierWriteOutcome;
  message?: string;
  onVerify?: () => void;
  verifying?: boolean;
}) {
  const copy = {
    write_disabled: {
      variant: "default" as const,
      title: C.writeDisabledTitle,
      message: C.writeDisabledMessage,
    },
    acknowledged: {
      variant: "default" as const,
      title: C.outcomeAcknowledgedTitle,
      message: C.outcomeAcknowledgedMessage,
    },
    persistence_confirmed: {
      variant: "success" as const,
      title: C.outcomePersistenceTitle,
      message: C.outcomePersistenceMessage,
    },
    rejected: {
      variant: "error" as const,
      title: C.outcomeRejectedTitle,
      message: message || C.outcomeRejectedMessage,
    },
    indeterminate: {
      variant: "default" as const,
      title: C.outcomeIndeterminateTitle,
      message: C.outcomeIndeterminateMessage,
    },
  }[outcome];

  return (
    <SuppliesStateBanner variant={copy.variant}>
      <strong>{copy.title}</strong> {copy.message}{" "}
      {onVerify ? (
        <SuppliesActionButton
          type="button"
          variant="ghost"
          onClick={onVerify}
          disabled={verifying}
        >
          {C.verifyAction}
        </SuppliesActionButton>
      ) : null}
    </SuppliesStateBanner>
  );
}
