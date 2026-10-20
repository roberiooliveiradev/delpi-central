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
  SuppliesTextField,
} from "../../app/suppliesUi";
import { ApiRequestError } from "../../api/httpClient";
import { SP_HELP } from "../../content/helpTooltips";
import { getSupplier, updateSupplier } from "./api";
import { SUPPLIERS_CONTENT as C } from "./content";
import {
  classifyWriteOutcome,
  diffEditableFields,
  formatTaxIdMasked,
  getSupplierFieldValue,
} from "./query";
import {
  SUPPLIER_FIELD_REGISTRY,
  SUPPLIER_FORM_SECTIONS,
  type SupplierDetail,
  type SupplierEditDraft,
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
    field: "supplier_name" | "supplier_short_name";
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
  const [draft, setDraft] = useState<SupplierEditDraft>({
    supplier_name: "",
    supplier_short_name: "",
  });
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
        setDraft({
          supplier_name:
            payload.sections.identification?.supplier_name?.toString() ?? "",
          supplier_short_name:
            payload.sections.identification?.supplier_short_name?.toString() ?? "",
        });
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
    () =>
      diffEditableFields(
        detail?.sections.identification ?? {},
        draft,
      ),
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
    setDraft({
      supplier_name:
        detail?.sections.identification?.supplier_name?.toString() ?? "",
      supplier_short_name:
        detail?.sections.identification?.supplier_short_name?.toString() ?? "",
    });
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
        const current = fresh.sections.identification ?? {};
        const reflected = writeState.submitted!.every(
          (change) =>
            (current[change.field]?.toString() ?? "") === change.after,
        );
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
          <SuppliesSectionHintLabel
            label={
              identification.supplier_name?.toString() || `${code}/${store}`
            }
            hint={SP_HELP.suppliers}
          />
        }
        description={`${C.detailTitle} · ${code}/${store}`}
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
          </div>

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
                <div className="sp-supplier-detail__edit-grid">
                  {section.fields.some((spec) => spec.put !== "editable") ? (
                    <dl className="sp-supplier-detail__identity">
                      {section.fields
                        .filter((spec) => spec.put !== "editable")
                        .map((spec) => (
                          <div key={spec.key} title={C.readonlyFieldHint}>
                            <dt>{spec.label}</dt>
                            <dd>
                              {getSupplierFieldValue(detail, spec) || "—"}
                            </dd>
                          </div>
                        ))}
                    </dl>
                  ) : null}
                  {section.fields
                    .filter((spec) => spec.put === "editable")
                    .map((spec) => (
                      <SuppliesTextField
                        key={spec.key}
                        label={spec.label}
                        hint={
                          spec.key === "supplier_name"
                            ? SP_HELP.suppliersEditName
                            : SP_HELP.suppliersEditShortName
                        }
                        value={draft[spec.key as keyof SupplierEditDraft]}
                        onChange={(value) =>
                          setDraft((d) => ({
                            ...d,
                            [spec.key]: value.slice(0, spec.maxLength),
                          }))
                        }
                        disabled={submitting}
                      />
                    ))}
                </div>
              ) : (
                <dl className="sp-supplier-detail__identity">
                  {section.fields.map((spec) => (
                    <div key={spec.key}>
                      <dt>{spec.label}</dt>
                      <dd>{getSupplierFieldValue(detail, spec) || "—"}</dd>
                    </div>
                  ))}
                </dl>
              )}
            </SuppliesSectionCard>
          ))}

          {editing ? (
            <>
              <p className="sp-supplier-detail__readonly-note">{C.editHint}</p>
              <div className="sp-supplier-detail__edit-actions">
                <SuppliesActionButton
                  type="button"
                  variant="primary"
                  onClick={() => setReviewing(true)}
                  disabled={!dirty || submitting}
                >
                  {C.reviewAction}
                </SuppliesActionButton>
                <SuppliesActionButton
                  type="button"
                  variant="ghost"
                  onClick={cancelEdit}
                  disabled={submitting}
                >
                  {C.cancelAction}
                </SuppliesActionButton>
              </div>
            </>
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
              {C.cancelAction}
            </SuppliesActionButton>
          </>
        }
      >
        {changes.length ? (
          <table className="sp-supplier-diff">
            <thead>
              <tr>
                <th>Campo</th>
                <th>Valor atual</th>
                <th>Novo valor</th>
              </tr>
            </thead>
            <tbody>
              {changes.map((change) => (
                <tr key={change.field}>
                  <td>
                    {SUPPLIER_FIELD_REGISTRY.find((s) => s.key === change.field)
                      ?.label ?? change.field}
                  </td>
                  <td>{change.before || "—"}</td>
                  <td>{change.after || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
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
