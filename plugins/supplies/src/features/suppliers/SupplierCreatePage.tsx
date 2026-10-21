import { useMemo, useState } from "react";

import {
  navigatePluginPath,
  navigatePluginView,
} from "../../app/pluginNavigation";
import {
  buildPluginPath,
  buildSupplierDetailPath,
} from "../../app/pluginRoutes";
import {
  SuppliesActionButton,
  SuppliesModal,
  SuppliesPageHero,
  SuppliesPagePath,
  SuppliesSectionCard,
  SuppliesSectionHintLabel,
  SuppliesStateBanner,
} from "../../app/suppliesUi";
import { ApiRequestError } from "../../api/httpClient";
import { SP_HELP } from "../../content/helpTooltips";
import { createSupplier } from "./api";
import { SUPPLIERS_CONTENT as C } from "./content";
import { classifyWriteOutcome } from "./query";
import {
  SupplierCatalogField,
  SupplierFieldInput,
  SupplierFieldGrid,
  SupplierFormActions,
  SupplierProtectedField,
  SupplierReviewTable,
} from "./SupplierFormFields";
import {
  supplierCatalogValueText,
  supplierFieldItemClass,
} from "./query";
import {
  SUPPLIER_CREATE_SECTIONS,
  SUPPLIER_FIELD_REGISTRY,
  type SupplierCreateDraft,
  type SupplierWriteOutcome,
} from "./types";

type SupplierCreatePageProps = {
  basePath: string;
};

const EMPTY_DRAFT: SupplierCreateDraft = {
  supplier_store: "",
  person_type: "",
  tax_id: "",
  supplier_name: "",
  supplier_short_name: "",
  address: "",
  district: "",
  postal_code: "",
  state: "",
  city: "",
  city_code: "",
  area_code: "",
  phone: "",
  contact_name: "",
  email: "",
  state_registration: "",
  municipal_registration: "",
  country_code: "",
  bacen_country_code: "",
  rohs_indicator: "",
  payment_condition_code: "",
  payment_method_code: "",
  accounting_account: "",
  financial_nature_code: "",
};

const CREATE_SECTION_TITLES = {
  identification: C.sectionIdentification,
  address: C.sectionAddress,
  contact: C.sectionContact,
  fiscal: C.sectionFiscal,
  purchasing: C.sectionPurchasing,
} as const;

export function SupplierCreatePage({ basePath }: SupplierCreatePageProps) {
  const [draft, setDraft] = useState<SupplierCreateDraft>(EMPTY_DRAFT);
  const [reviewing, setReviewing] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [writeOutcome, setWriteOutcome] = useState<SupplierWriteOutcome | null>(
    null,
  );
  const [writeMessage, setWriteMessage] = useState<string | null>(null);
  const [createdSupplier, setCreatedSupplier] = useState<{
    code: string;
    store: string;
  } | null>(null);

  const dirty = useMemo(
    () => Object.values(draft).some((value) => value.trim()),
    [draft],
  );

  const filledEntries = useMemo(
    () =>
      (Object.entries(draft) as [keyof SupplierCreateDraft, string][]).filter(
        ([, value]) => value.trim(),
      ),
    [draft],
  );

  const reviewGroups = useMemo(() => {
    const filled = new Map(filledEntries);
    return (Object.keys(CREATE_SECTION_TITLES) as Array<
      keyof typeof CREATE_SECTION_TITLES
    >)
      .map((id) => ({
        section: id,
        title: CREATE_SECTION_TITLES[id],
        rows: SUPPLIER_FIELD_REGISTRY.filter(
          (spec) =>
            spec.section === id &&
            filled.has(spec.key as keyof SupplierCreateDraft),
        ).map((spec) => ({
          label: spec.label,
          after: supplierCatalogValueText(
            spec,
            filled.get(spec.key as keyof SupplierCreateDraft)!,
          ),
          help: spec.help,
        })),
      }))
      .filter((group) => group.rows.length > 0);
  }, [filledEntries]);

  const storeValid = /^\d{2}$/.test(draft.supplier_store);

  const listHref = buildPluginPath("suppliers", basePath);
  const goBack = (event?: { preventDefault: () => void }) => {
    event?.preventDefault();
    if (dirty && !window.confirm(C.unsavedChangesWarning)) return;
    navigatePluginView("suppliers", { basePath });
  };

  const patchDraft = (patch: Partial<SupplierCreateDraft>) =>
    setDraft((current) => ({ ...current, ...patch }));

  const confirmSubmit = () => {
    setReviewing(false);
    setSubmitting(true);
    setWriteOutcome(null);
    setWriteMessage(null);
    setCreatedSupplier(null);
    createSupplier(draft)
      .then((response) => {
        const outcome = classifyWriteOutcome(response, 200);
        setWriteOutcome(outcome);
        const data = response.data ?? {};
        const code = data.supplier_code?.toString();
        const store = data.supplier_store?.toString();
        if (code && store) setCreatedSupplier({ code, store });
      })
      .catch((err: unknown) => {
        if (err instanceof ApiRequestError) {
          setWriteOutcome(
            classifyWriteOutcome(
              { outcome: err.outcome as SupplierWriteOutcome, code: err.code },
              err.status,
            ),
          );
          setWriteMessage(err.message);
        } else {
          setWriteOutcome("indeterminate");
        }
      })
      .finally(() => setSubmitting(false));
  };

  return (
    <div className="sp-page-stack sp-supplier-create">
      <SuppliesPagePath
        back={{
          label: C.backToList,
          href: listHref,
          onNavigate: goBack,
        }}
        items={[]}
        current={C.createTitle}
      />

      <SuppliesPageHero
        eyebrow={C.eyebrow}
        title={
          <SuppliesSectionHintLabel
            label={C.createTitle}
            hint={SP_HELP.suppliersCreate}
          />
        }
        description={C.createDescription}
      />

      {writeOutcome === "write_disabled" ? (
        <SuppliesStateBanner variant="default">
          <strong>{C.writeDisabledTitle}</strong> {C.writeDisabledMessage}
        </SuppliesStateBanner>
      ) : null}
      {writeOutcome === "acknowledged" ? (
        <SuppliesStateBanner variant="default">
          <strong>{C.outcomeAcknowledgedTitle}</strong>{" "}
          {C.outcomeAcknowledgedMessage}
        </SuppliesStateBanner>
      ) : null}
      {writeOutcome === "persistence_confirmed" ? (
        <SuppliesStateBanner variant="success">
          <strong>{C.outcomePersistenceTitle}</strong>{" "}
          {C.outcomePersistenceMessage}{" "}
          {createdSupplier ? (
            <a
              href={buildSupplierDetailPath(
                createdSupplier.code,
                createdSupplier.store,
                basePath,
              )}
              onClick={(event) => {
                event.preventDefault();
                navigatePluginPath(
                  buildSupplierDetailPath(
                    createdSupplier.code,
                    createdSupplier.store,
                    basePath,
                  ),
                );
              }}
            >
              {C.openCreatedDetail}
            </a>
          ) : null}
        </SuppliesStateBanner>
      ) : null}
      {writeOutcome === "rejected" ? (
        <SuppliesStateBanner variant="error">
          <strong>{C.outcomeRejectedTitle}</strong>{" "}
          {writeMessage || C.outcomeRejectedMessage}
        </SuppliesStateBanner>
      ) : null}
      {writeOutcome === "indeterminate" ? (
        <SuppliesStateBanner variant="default">
          <strong>{C.outcomeIndeterminateTitle}</strong>{" "}
          {C.outcomeIndeterminateMessage}
        </SuppliesStateBanner>
      ) : null}

      {SUPPLIER_CREATE_SECTIONS.map((section) => (
        <SuppliesSectionCard
          key={section.id}
          title={CREATE_SECTION_TITLES[section.id]}
          hint={SP_HELP.suppliersCreateFields}
        >
          <SupplierFieldGrid>
            {section.fields.map((field) => {
              const derivedActive =
                field.catalogDerivedFrom === "city" &&
                Boolean((draft.state ?? "").trim());
              return (
                <div
                  key={field.key}
                  className={supplierFieldItemClass(field)}
                >
                  {field.catalog ? (
                    <SupplierCatalogField
                      spec={field}
                      value={
                        field.key === "city"
                          ? (draft.city_code ?? "")
                          : (draft[field.key] ?? "")
                      }
                      currentLabel={
                        field.key === "city" ? draft.city : undefined
                      }
                      dependsOnValue={
                        field.catalogDependsOn
                          ? (draft[
                              field.catalogDependsOn as keyof SupplierCreateDraft
                            ] ?? "")
                          : undefined
                      }
                      onPick={(code, label) => {
                        if (field.key === "city") {
                          patchDraft({ city: label || code, city_code: code });
                        } else {
                          patchDraft({ [field.key]: code });
                        }
                      }}
                      disabled={submitting}
                    />
                  ) : derivedActive ? (
                    <SupplierProtectedField
                      label={field.label}
                      value={draft[field.key] ?? ""}
                      emptyLabel={C.fieldNotProvided}
                      hint={field.help}
                    />
                  ) : (
                    <SupplierFieldInput
                      spec={field}
                      value={draft[field.key]}
                      onChange={(value) => patchDraft({ [field.key]: value })}
                      disabled={submitting}
                      showRequiredMark
                    />
                  )}
                </div>
              );
            })}
          </SupplierFieldGrid>
        </SuppliesSectionCard>
      ))}

      <SupplierFormActions>
        <SuppliesActionButton
          type="button"
          variant="ghost"
          onClick={() => goBack()}
          disabled={submitting}
        >
          {C.createBack}
        </SuppliesActionButton>
        <SuppliesActionButton
          type="button"
          variant="primary"
          onClick={() => setReviewing(true)}
          disabled={!storeValid || !filledEntries.length || submitting}
        >
          {C.createSubmit}
        </SuppliesActionButton>
      </SupplierFormActions>

      <SuppliesModal
        open={reviewing}
        title={C.createReviewTitle}
        onClose={() => setReviewing(false)}
        footer={
          <>
            <SuppliesActionButton
              type="button"
              variant="primary"
              onClick={confirmSubmit}
              disabled={submitting}
            >
              {C.createConfirmAction}
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
        <p className="sp-supplier-create__review-note">
          {C.createReviewDescription}
        </p>
        <SupplierReviewTable
          groups={reviewGroups}
          showBefore={false}
        />
      </SuppliesModal>
    </div>
  );
}
