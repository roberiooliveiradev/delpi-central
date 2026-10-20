import { useMemo, useState } from "react";

import { navigatePluginView } from "../../app/pluginNavigation";
import { buildPluginPath } from "../../app/pluginRoutes";
import {
  SuppliesActionButton,
  SuppliesModal,
  SuppliesPageHero,
  SuppliesPagePath,
  SuppliesSectionCard,
  SuppliesSectionHintLabel,
  SuppliesStateBanner,
  SuppliesTextField,
} from "../../app/suppliesUi";
import { ApiRequestError } from "../../api/httpClient";
import { SP_HELP } from "../../content/helpTooltips";
import { createSupplier } from "./api";
import { SUPPLIERS_CONTENT as C } from "./content";
import { classifyWriteOutcome } from "./query";
import type {
  SupplierCreateDraft,
  SupplierWriteOutcome,
} from "./types";

type SupplierCreatePageProps = {
  basePath: string;
};

const EMPTY_DRAFT: SupplierCreateDraft = {
  supplier_name: "",
  supplier_short_name: "",
  tax_id: "",
  state: "",
};

const CREATE_FIELD_LABELS: Record<keyof SupplierCreateDraft, string> = {
  supplier_name: "Razão social",
  supplier_short_name: "Nome fantasia",
  tax_id: "CNPJ/CPF",
  state: "UF",
};

export function SupplierCreatePage({ basePath }: SupplierCreatePageProps) {
  const [draft, setDraft] = useState<SupplierCreateDraft>(EMPTY_DRAFT);
  const [reviewing, setReviewing] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [writeOutcome, setWriteOutcome] = useState<SupplierWriteOutcome | null>(
    null,
  );
  const [writeMessage, setWriteMessage] = useState<string | null>(null);

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
    createSupplier(draft)
      .then((response) => {
        setWriteOutcome(classifyWriteOutcome(response, 200));
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
          {C.outcomePersistenceMessage}
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

      <SuppliesSectionCard
        title={C.sectionIdentification}
        hint={SP_HELP.suppliersCreateFields}
      >
        <div className="sp-supplier-create__form">
          <SuppliesTextField
            label={CREATE_FIELD_LABELS.supplier_name}
            hint={SP_HELP.suppliersEditName}
            value={draft.supplier_name}
            onChange={(value) => patchDraft({ supplier_name: value })}
            disabled={submitting}
          />
          <SuppliesTextField
            label={CREATE_FIELD_LABELS.supplier_short_name}
            hint={SP_HELP.suppliersEditShortName}
            value={draft.supplier_short_name}
            onChange={(value) => patchDraft({ supplier_short_name: value })}
            disabled={submitting}
          />
          <SuppliesTextField
            label={CREATE_FIELD_LABELS.tax_id}
            hint={SP_HELP.suppliersColTaxId}
            value={draft.tax_id}
            onChange={(value) => patchDraft({ tax_id: value })}
            disabled={submitting}
          />
          <SuppliesTextField
            label={CREATE_FIELD_LABELS.state}
            hint={SP_HELP.suppliersState}
            value={draft.state}
            onChange={(value) =>
              patchDraft({ state: value.toUpperCase().slice(0, 2) })
            }
            disabled={submitting}
          />
          <div className="sp-supplier-create__actions">
            <SuppliesActionButton
              type="button"
              variant="primary"
              onClick={() => setReviewing(true)}
              disabled={!filledEntries.length || submitting}
            >
              {C.createSubmit}
            </SuppliesActionButton>
            <SuppliesActionButton
              type="button"
              variant="ghost"
              onClick={() => goBack()}
              disabled={submitting}
            >
              {C.createBack}
            </SuppliesActionButton>
          </div>
        </div>
      </SuppliesSectionCard>

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
        <table className="sp-supplier-diff">
          <thead>
            <tr>
              <th>Campo</th>
              <th>Valor</th>
            </tr>
          </thead>
          <tbody>
            {filledEntries.map(([field, value]) => (
              <tr key={field}>
                <td>{CREATE_FIELD_LABELS[field]}</td>
                <td>{value}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </SuppliesModal>
    </div>
  );
}
