import { useEffect, useMemo, useRef, useState } from "react";

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
import { SUPPLIERS_CONTENT as C, supplierSectionDescriptions } from "./content";
import { CreationAssistedFlow } from "./creation/CreationAssistedFlow";
import { applyDraftPatchToEntries } from "./creation/stateMachine";
import type { SuggestionEntryMap } from "./creation/types";
import {
  classifyWriteOutcome,
  isIntegrationAuthErrorCode,
  supplierCreateFieldSection,
  supplierFieldAnchorId,
  validateCreateDraft,
} from "./query";
import {
  SupplierCatalogField,
  SupplierFieldInput,
  SupplierFieldShell,
  SupplierPostalCodeAssistant,
  SupplierFieldGrid,
  SupplierFormActions,
  SupplierProtectedField,
  SupplierReviewTable,
} from "./SupplierFormFields";
import { supplierCatalogValueText } from "./query";
import {
  SUPPLIER_CREATE_SECTIONS,
  SUPPLIER_FIELD_REGISTRY,
  type SupplierCreateDraft,
  type SupplierFieldError,
  type SupplierFieldKey,
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
  address_number: "",
  po_box: "",
  icms_contributor: "",
  simples_nacional: "",
  cnae_code: "",
  legal_entity_type: "",
  simp_regime_code: "",
  pb_regime_code: "",
  inss_withholding: "",
  iss_withholding: "",
  csll_withholding: "",
  cofins_withholding: "",
  pis_withholding: "",
  irf_calculation: "",
  inp_calculation: "",
  tax_group_code: "",
  commercial_contact_name: "",
  fax: "",
  website: "",
  responsible_name: "",
  risk_code: "",
  swift_code: "",
  purchase_price_table_code: "",
  carrier_code: "",
  segment_code: "",
  administrator_code: "",
  linked_customer_code: "",
  linked_customer_store: "",
  linked_employee_code: "",
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
  const [suggestionEntries, setSuggestionEntries] = useState<SuggestionEntryMap>(
    {},
  );
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
  // X4.PROD-C1.R6 — erros agregados por campo + resumo (local e 422 do backend).
  const [fieldErrors, setFieldErrors] = useState<
    Partial<Record<SupplierFieldKey, string>>
  >({});
  const [validationErrors, setValidationErrors] = useState<
    SupplierFieldError[] | null
  >(null);
  const validationSummaryRef = useRef<HTMLDivElement | null>(null);
  // R6-FE — seções colapsáveis: abertas por padrão; erros expandem a seção.
  const [openSections, setOpenSections] = useState<
    Partial<Record<string, boolean>>
  >({});

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

  const listHref = buildPluginPath("suppliers", basePath);
  const goBack = (event?: { preventDefault: () => void }) => {
    event?.preventDefault();
    if (dirty && !window.confirm(C.unsavedChangesWarning)) return;
    navigatePluginView("suppliers", { basePath });
  };

  useEffect(() => {
    if (validationErrors?.length) {
      validationSummaryRef.current?.focus();
    }
  }, [validationErrors]);

  const fieldLabel = (key: SupplierFieldKey): string =>
    SUPPLIER_FIELD_REGISTRY.find((spec) => spec.key === key)?.label ?? key;

  const applyFieldErrors = (errors: SupplierFieldError[]) => {
    setValidationErrors(errors);
    const next: Partial<Record<SupplierFieldKey, string>> = {};
    for (const error of errors) next[error.field] = error.message;
    setFieldErrors(next);
    // Seções com pendências ficam visíveis — nunca recolhidas sob o erro.
    setOpenSections((current) => {
      const open = { ...current };
      for (const error of errors) {
        const section = supplierCreateFieldSection(error.field);
        if (section) open[section] = true;
      }
      return open;
    });
  };

  /** Navegação do resumo: expande a seção, rola e foca o controle do campo. */
  const focusSupplierField = (key: SupplierFieldKey) => {
    const section = supplierCreateFieldSection(key);
    if (section) {
      setOpenSections((current) => ({ ...current, [section]: true }));
    }
    requestAnimationFrame(() => {
      const anchor = document.getElementById(supplierFieldAnchorId(key));
      if (!anchor) return;
      anchor.scrollIntoView({ behavior: "smooth", block: "center" });
      anchor
        .querySelector<HTMLElement>(
          "input, select, textarea, button, [tabindex]:not([tabindex=-1])",
        )
        ?.focus({ preventScroll: true });
    });
  };

  const patchDraft = (patch: Partial<SupplierCreateDraft>) => {
    setDraft((current) => ({ ...current, ...patch }));
    // Reconcilia edição manual com o estado de UX das sugestões externas.
    setSuggestionEntries((current) =>
      applyDraftPatchToEntries(current, patch as Record<string, string>),
    );
    // Campo corrigido limpa o próprio erro; o resumo sai quando não sobrar erro.
    setFieldErrors((current) => {
      const next = { ...current };
      for (const key of Object.keys(patch)) {
        delete next[key as SupplierFieldKey];
      }
      return next;
    });
    setValidationErrors((current) =>
      current
        ? current.filter(
            (error) => !(error.field in patch),
          )
        : current,
    );
  };

  /** Validação agregada pré-submit — bloqueia abertura da revisão e o POST. */
  const handleReview = () => {
    const errors = validateCreateDraft(draft);
    if (errors.length) {
      applyFieldErrors(errors);
      return;
    }
    setReviewing(true);
  };

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
          // 422 estruturado: associa cada erro ao campo e resume a lista.
          if (err.fields?.length) {
            applyFieldErrors(
              err.fields.map((item) => ({
                field: item.field as SupplierFieldKey,
                message: item.message,
                code: item.code,
              })),
            );
          }
          if (isIntegrationAuthErrorCode(err.code)) {
            setWriteMessage(C.validationAuthMessage);
          } else {
            // detail sanitizado da BFF — nunca texto bruto do ERP.
            setWriteMessage(err.detail || err.message);
          }
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

      <p className="sp-supplier-create__required-legend">
        {C.requiredFieldsLegend}
      </p>

      {validationErrors?.length ? (
        <SuppliesStateBanner variant="error">
          <div
            ref={validationSummaryRef}
            tabIndex={-1}
            role="alert"
          >
            <strong>{C.validationSummaryTitle}</strong>{" "}
            {validationErrors.every(
              (error) => error.code === "missing_required",
            )
              ? C.validationSummaryLead
              : C.validationSummaryLeadMixed}
            <ul className="sp-supplier-create__validation-list">
              {validationErrors.map((error) => (
                <li key={error.field}>
                  <button
                    type="button"
                    className="sp-supplier-create__validation-link"
                    onClick={() => focusSupplierField(error.field)}
                    aria-label={`${C.validationGoToField}: ${fieldLabel(error.field)}`}
                  >
                    {fieldLabel(error.field)}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </SuppliesStateBanner>
      ) : null}

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

      <CreationAssistedFlow
        basePath={basePath}
        draft={draft}
        disabled={submitting}
        entries={suggestionEntries}
        onEntriesChange={setSuggestionEntries}
        onApplyPatch={patchDraft}
      />

      {SUPPLIER_CREATE_SECTIONS.map((section) => {
        const sectionErrors = section.fields.filter(
          (field) => fieldErrors[field.key],
        ).length;
        return (
        <SuppliesSectionCard
          key={section.id}
          title={CREATE_SECTION_TITLES[section.id]}
          subtitle={supplierSectionDescriptions[section.id]}
          collapsible
          open={openSections[section.id] ?? true}
          onOpenChange={(open) =>
            setOpenSections((current) => ({
              ...current,
              [section.id]: open,
            }))
          }
          actions={
            sectionErrors ? (
              <span className="sp-supplier-section__error-badge">
                {sectionErrors === 1
                  ? C.validationSectionErrorOne
                  : C.validationSectionErrorMany.replace(
                      "{count}",
                      String(sectionErrors),
                    )}
              </span>
            ) : undefined
          }
        >
          <SupplierFieldGrid>
            {section.fields.map((field) => {
              const derivedActive =
                field.catalogDerivedFrom === "city" &&
                Boolean((draft.state ?? "").trim());
              const fieldError = fieldErrors[field.key];
              return (
                <SupplierFieldShell
                  key={field.key}
                  spec={field}
                  error={fieldError}
                  requiredMark
                >
                  {field.catalog ? (
                    <SupplierCatalogField
                      showRequiredMark
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
                      codeFilter={
                        field.catalogCodeParam
                          ? (draft[
                              field.catalogCodeParam as keyof SupplierCreateDraft
                            ] ?? "")
                          : undefined
                      }
                      onPick={(code, label, option) => {
                        if (field.key === "city") {
                          patchDraft({ city: label || code, city_code: code });
                        } else {
                          const patch: Partial<SupplierCreateDraft> = {
                            [field.key]: code,
                          };
                          if (field.catalogPairField && option?.store) {
                            patch[
                              field.catalogPairField as keyof SupplierCreateDraft
                            ] = option.store;
                          }
                          patchDraft(patch);
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
                  ) : field.key === "postal_code" ? (
                    <SupplierPostalCodeAssistant
                      spec={field}
                      value={draft.postal_code}
                      onChange={(value) =>
                        patchDraft({ postal_code: value })
                      }
                      onApply={(patch) => patchDraft(patch)}
                      current={{
                        address: draft.address,
                        district: draft.district,
                        city: draft.city,
                        state: draft.state,
                      }}
                      disabled={submitting}
                      showRequiredMark
                    />
                  ) : (
                    <SupplierFieldInput
                      spec={field}
                      value={draft[field.key]}
                      onChange={(value) => patchDraft({ [field.key]: value })}
                      disabled={submitting}
                      showRequiredMark
                      personType={draft.person_type}
                    />
                  )}
                </SupplierFieldShell>
              );
            })}
          </SupplierFieldGrid>
        </SuppliesSectionCard>
        );
      })}

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
          onClick={handleReview}
          disabled={!filledEntries.length || submitting}
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
