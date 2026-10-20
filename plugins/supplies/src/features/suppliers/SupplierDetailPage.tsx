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
} from "./query";
import {
  SUPPLIERS_EDITABLE_FIELDS,
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
} | null;

const SECTION_LABELS: Record<string, string> = {
  identification: C.sectionIdentification,
  address: C.sectionAddress,
  contact: C.sectionContact,
  fiscal: C.sectionFiscal,
  purchasing: C.sectionPurchasing,
};

const FIELD_LABELS: Record<string, string> = {
  supplier_code: "Código",
  supplier_store: "Loja",
  supplier_name: "Razão social",
  supplier_short_name: "Nome fantasia",
  person_type: "Tipo de pessoa",
  address: "Endereço",
  district: "Bairro",
  postal_code: "CEP",
  city: "Cidade",
  city_code: "Código IBGE",
  state: "UF",
  contact_name: "Contato",
  area_code: "DDD",
  phone: "Telefone",
  email: "E-mail",
  state_registration: "Inscrição estadual",
  municipal_registration: "Inscrição municipal",
  rohs_indicator: "Indicador ROHS",
  payment_condition_code: "Condição de pagamento",
  payment_method_code: "Forma de pagamento",
  financial_nature_code: "Natureza financeira",
  accounting_account: "Conta contábil",
  country_code: "País",
  bacen_country_code: "País (BACEN)",
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
    updateSupplier(code, store, draft)
      .then((response) => {
        const outcome = classifyWriteOutcome(response, 200);
        setWriteState({ outcome });
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
        <WriteOutcomeBanner outcome={writeState.outcome} message={writeState.message} />
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

          <SuppliesSectionCard
            title={C.sectionIdentification}
            hint={SP_HELP.suppliersIdentification}
          >
            {editing ? (
              <div className="sp-supplier-detail__edit-grid">
                <dl className="sp-supplier-detail__identity">
                  <div>
                    <dt>{FIELD_LABELS.supplier_code}</dt>
                    <dd>{identification.supplier_code ?? code}</dd>
                  </div>
                  <div>
                    <dt>{FIELD_LABELS.supplier_store}</dt>
                    <dd>{identification.supplier_store ?? store}</dd>
                  </div>
                </dl>
                <SuppliesTextField
                  label={FIELD_LABELS.supplier_name}
                  hint={SP_HELP.suppliersEditName}
                  value={draft.supplier_name}
                  onChange={(value) =>
                    setDraft((d) => ({
                      ...d,
                      supplier_name: value.slice(
                        0,
                        SUPPLIERS_EDITABLE_FIELDS.supplier_name,
                      ),
                    }))
                  }
                  disabled={submitting}
                />
                <SuppliesTextField
                  label={FIELD_LABELS.supplier_short_name}
                  hint={SP_HELP.suppliersEditShortName}
                  value={draft.supplier_short_name}
                  onChange={(value) =>
                    setDraft((d) => ({
                      ...d,
                      supplier_short_name: value.slice(
                        0,
                        SUPPLIERS_EDITABLE_FIELDS.supplier_short_name,
                      ),
                    }))
                  }
                  disabled={submitting}
                />
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
              </div>
            ) : (
              <SectionFields section={identification} />
            )}
          </SuppliesSectionCard>

          {(["address", "contact", "fiscal", "purchasing"] as const).map(
            (name) =>
              detail.sections[name] ? (
                <SuppliesSectionCard key={name} title={SECTION_LABELS[name]}>
                  <SectionFields section={detail.sections[name]!} />
                </SuppliesSectionCard>
              ) : null,
          )}
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
                  <td>{FIELD_LABELS[change.field]}</td>
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

function SectionFields({
  section,
}: {
  section: Record<string, string | number | null>;
}) {
  const entries = Object.entries(section);
  if (!entries.length) return null;
  return (
    <dl className="sp-supplier-detail__identity">
      {entries.map(([field, value]) => (
        <div key={field}>
          <dt>{FIELD_LABELS[field] ?? field}</dt>
          <dd>{value?.toString() || "—"}</dd>
        </div>
      ))}
    </dl>
  );
}

function WriteOutcomeBanner({
  outcome,
  message,
}: {
  outcome: SupplierWriteOutcome;
  message?: string;
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
      <strong>{copy.title}</strong> {copy.message}
    </SuppliesStateBanner>
  );
}
