import { useCallback, useEffect, useMemo, useState } from "react";

import {
  addSatisfactionRecipients,
  listSatisfactionRecipients,
  SATISFACTION_ADD_RECIPIENTS_MAX_BATCH,
} from "../../api/satisfactionSurveysApi";
import {
  CommercialActionButton,
  CommercialClearFiltersButton,
  CommercialEmptyState,
  CommercialInteractiveDataCard,
  CommercialLoadingCard,
  CommercialMetricCard,
  CommercialSectionCard,
  CommercialSelectField,
  CommercialStateBanner,
  CommercialStatusBadge,
  CommercialTextField,
  type DataTableColumn,
} from "../../app/commercialUi";
import { useCommercialFloatingNotice } from "../../app/CommercialFloatingNoticeProvider";
import { CommercialDataTableSection } from "../../app/dataTableUi";
import { navigatePluginPath } from "../../app/pluginNavigation";
import { buildSatisfactionRecipientDetailPath } from "../../app/pluginRoutes";
import { customerKey } from "../../shared/format";
import { CM_HELP } from "../../content/helpTooltips";
import { SATISFACTION_CONTENT } from "../../content/satisfactionSurveysContent";
import type {
  SatisfactionCampaign,
  SatisfactionCounts,
  SatisfactionRecipient,
} from "../../types/satisfactionSurvey";
import { CustomerAvatar } from "../customers/components/CustomerAvatar";
import {
  CustomerSearchPicker,
  type CustomerSearchSelection,
} from "../customers/components/CustomerSearchPicker";
import { describeAddRecipientsResult } from "./addRecipientsResult";
import {
  EMPTY_RECIPIENT_FILTERS,
  filterRecipients,
  recipientCompanyLabel,
  recipientKeys,
  type RecipientFilters,
} from "./satisfactionFilters";

type CampaignParticipantsTabProps = {
  basePath: string;
  campaign: SatisfactionCampaign;
  /** Após incluir participantes, o detalhe recarrega os contadores da campanha. */
  onParticipantsChanged: () => void;
};

const EMPTY_COUNTS: SatisfactionCounts = { participants: 0, responded: 0, pending: 0 };

function statusBadge(recipient: SatisfactionRecipient) {
  const copy = SATISFACTION_CONTENT.participants;
  return recipient.status === "responded" ? (
    <CommercialStatusBadge label={copy.statusResponded} variant="success" />
  ) : (
    <CommercialStatusBadge label={copy.statusPending} variant="warning" />
  );
}

function contactLabel(recipient: SatisfactionRecipient): string {
  const parts = [recipient.contact_name, recipient.contact_email].filter(
    (part): part is string => Boolean(part && part.trim()),
  );
  return parts.length > 0 ? parts.join(" · ") : SATISFACTION_CONTENT.participants.noContact;
}

/** UI-02B — aba Participantes: resumo, adição em lote e lista acumulada. */
export function CampaignParticipantsTab({
  basePath,
  campaign,
  onParticipantsChanged,
}: CampaignParticipantsTabProps) {
  const copy = SATISFACTION_CONTENT.participants;
  const detailCopy = SATISFACTION_CONTENT.detail;
  const { notifySuccess, notifyWarning, notifyError } = useCommercialFloatingNotice();

  const [recipients, setRecipients] = useState<SatisfactionRecipient[]>([]);
  const [counts, setCounts] = useState<SatisfactionCounts>(campaign.counts ?? EMPTY_COUNTS);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [filters, setFilters] = useState<RecipientFilters>(EMPTY_RECIPIENT_FILTERS);
  const [picked, setPicked] = useState<CustomerSearchSelection[]>([]);
  const [adding, setAdding] = useState(false);
  const [addExpanded, setAddExpanded] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    listSatisfactionRecipients(campaign.id, controller.signal)
      .then((list) => {
        if (controller.signal.aborted) return;
        setRecipients(list.items ?? []);
        setCounts(list.counts ?? EMPTY_COUNTS);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setRecipients([]);
        setError(err instanceof Error ? err.message : copy.loadError);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [campaign.id, copy.loadError, reloadKey]);

  const existingKeys = useMemo(() => recipientKeys(recipients), [recipients]);
  const rows = useMemo(() => filterRecipients(recipients, filters), [recipients, filters]);
  const campaignClosed = campaign.status === "closed";

  const openRecipient = useCallback(
    (recipient: SatisfactionRecipient) => {
      const href = buildSatisfactionRecipientDetailPath(basePath, campaign.id, recipient.id);
      if (href) navigatePluginPath(href);
    },
    [basePath, campaign.id],
  );

  const addSelected = async () => {
    if (picked.length === 0 || adding || campaignClosed) return;
    setAdding(true);
    try {
      const result = await addSatisfactionRecipients(
        campaign.id,
        picked.map((item) => ({
          customer_code: item.code,
          customer_store: item.store,
          customer_name: item.name || null,
        })),
      );
      const feedback = describeAddRecipientsResult(result);
      if (feedback.success) notifySuccess(feedback.success);
      if (feedback.info) notifyWarning(feedback.info);
      for (const failure of feedback.failures) notifyError(failure);
      if (!feedback.success && !feedback.info && feedback.failures.length === 0) {
        notifyWarning(copy.addNothing);
      }
      // Remove só o que o servidor aceitou/preservou; falhas continuam selecionadas para nova tentativa.
      const failedKeys = new Set(
        (result.failed ?? []).map((item) => customerKey(item.customer_code, item.customer_store)),
      );
      setPicked((current) =>
        current.filter((item) => failedKeys.has(customerKey(item.code, item.store))),
      );
      setReloadKey((value) => value + 1);
      onParticipantsChanged();
      if ((result.included?.length ?? 0) > 0 && (result.failed?.length ?? 0) === 0) {
        setAddExpanded(false);
        setPicked([]);
      }
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : copy.addNothing);
    } finally {
      setAdding(false);
    }
  };

  const collapseAdd = () => {
    setAddExpanded(false);
    setPicked([]);
  };

  const columns: DataTableColumn<SatisfactionRecipient>[] = [
    {
      key: "company",
      header: copy.colCompany,
      headerHint: CM_HELP.satisfactionSurveys.colCompany,
      render: (row) => (
        <span className="cm-row-actions">
          <CustomerAvatar
            code={row.customer_code}
            store={row.customer_store}
            name={(row.customer_name ?? "").trim() || row.customer_code}
            size="sm"
            previewable={false}
          />
          <span>{recipientCompanyLabel(row)}</span>
        </span>
      ),
    },
    {
      key: "contact",
      header: copy.colContact,
      headerHint: CM_HELP.satisfactionSurveys.colContact,
      render: (row) => contactLabel(row),
    },
    {
      key: "status",
      header: copy.colStatus,
      headerHint: CM_HELP.satisfactionSurveys.colRecipientStatus,
      render: (row) => statusBadge(row),
    },
  ];

  return (
    <div className="cm-satisfaction-stack">
      <div className="cm-satisfaction-metrics">
        <CommercialMetricCard
          label={detailCopy.metricParticipants}
          titleHint={CM_HELP.satisfactionSurveys.metricParticipants}
          value={counts.participants.toLocaleString("pt-BR")}
          loading={loading}
        />
        <CommercialMetricCard
          label={detailCopy.metricResponded}
          titleHint={CM_HELP.satisfactionSurveys.metricResponded}
          value={counts.responded.toLocaleString("pt-BR")}
          loading={loading}
        />
        <CommercialMetricCard
          label={detailCopy.metricPending}
          titleHint={CM_HELP.satisfactionSurveys.metricPending}
          hint={detailCopy.metricPendingHint}
          value={counts.pending.toLocaleString("pt-BR")}
          loading={loading}
        />
      </div>

      <CommercialSectionCard
        title={copy.addTitle}
        hint={CM_HELP.satisfactionSurveys.addCustomers}
        actions={
          campaignClosed ? undefined : addExpanded ? (
            <CommercialActionButton
              variant="ghost"
              disabled={adding}
              onClick={collapseAdd}
              aria-expanded={true}
            >
              {copy.addCollapse}
            </CommercialActionButton>
          ) : (
            <CommercialActionButton
              variant="primary"
              onClick={() => setAddExpanded(true)}
              aria-expanded={false}
            >
              {copy.addExpand}
            </CommercialActionButton>
          )
        }
      >
        <div className="cm-satisfaction-stack">
          {campaignClosed ? (
            <CommercialStateBanner>{copy.addClosed}</CommercialStateBanner>
          ) : !addExpanded ? (
            <p>{copy.addCollapsedHint}</p>
          ) : (
            <>
              <p>{copy.addIntro}</p>
              <CustomerSearchPicker
                value={picked}
                onChange={setPicked}
                includeBlocked={false}
                excludeKeys={existingKeys}
                maxSelected={SATISFACTION_ADD_RECIPIENTS_MAX_BATCH}
                disabled={adding}
                labels={{
                  title: copy.addPickerTitle,
                  hint: CM_HELP.satisfactionSurveys.addCustomers,
                  placeholder: copy.addPickerPlaceholder,
                }}
                renderOptionLeading={(hit) => (
                  <CustomerAvatar
                    code={hit.code}
                    store={hit.store}
                    name={(hit.name || "").trim() || hit.code}
                    size="sm"
                    previewable={false}
                  />
                )}
              />
              <div className="cm-satisfaction-actions">
                <CommercialActionButton
                  variant="ghost"
                  disabled={adding}
                  onClick={collapseAdd}
                >
                  {copy.addCancel}
                </CommercialActionButton>
                <CommercialActionButton
                  variant="primary"
                  disabled={picked.length === 0 || adding}
                  onClick={() => void addSelected()}
                >
                  {adding
                    ? copy.adding
                    : `${copy.addAction}${picked.length > 0 ? ` (${picked.length})` : ""}`}
                </CommercialActionButton>
              </div>
            </>
          )}
        </div>
      </CommercialSectionCard>

      <CommercialSectionCard title={copy.tableTitle}>
        <div className="cm-satisfaction-stack">
          <div className="cm-satisfaction-filters">
            <CommercialSelectField
              label={copy.filterStatus}
              hint={CM_HELP.satisfactionSurveys.recipientsFilterStatus}
              value={filters.status}
              allowEmpty
              emptyLabel={copy.filterStatusAll}
              options={[
                { value: "pending", label: copy.filterStatusPending },
                { value: "responded", label: copy.filterStatusResponded },
              ]}
              onChange={(status) =>
                setFilters((prev) => ({
                  ...prev,
                  status: status === "pending" || status === "responded" ? status : "",
                }))
              }
            />
            <CommercialTextField
              label={copy.filterSearch}
              hint={CM_HELP.satisfactionSurveys.recipientsSearch}
              type="search"
              placeholder={copy.filterSearchPlaceholder}
              value={filters.search}
              onChange={(search) => setFilters((prev) => ({ ...prev, search }))}
            />
            {filters.status || filters.search.trim() ? (
              <CommercialClearFiltersButton onClick={() => setFilters(EMPTY_RECIPIENT_FILTERS)} />
            ) : null}
          </div>

          {error ? (
            <CommercialStateBanner variant="error">
              {error}{" "}
              <CommercialActionButton variant="ghost" onClick={() => setReloadKey((v) => v + 1)}>
                {SATISFACTION_CONTENT.detail.refresh}
              </CommercialActionButton>
            </CommercialStateBanner>
          ) : null}

          {loading && recipients.length === 0 ? (
            <CommercialLoadingCard title={copy.loading} variant="panel" />
          ) : null}

          {!loading && !error && recipients.length === 0 ? (
            <CommercialEmptyState title={copy.tableTitle} message={copy.empty} />
          ) : null}

          {recipients.length > 0 ? (
            <CommercialDataTableSection
              title={copy.tableTitle}
              columns={columns}
              rows={rows}
              rowKey={(row) => row.id}
              loading={loading}
              hideSearch
              emptyMessage={copy.emptyFiltered}
              onRowClick={openRecipient}
              viewLayoutPreferencesKey="commercial:satisfaction-recipients:layout"
              columnPreferencesKey="commercial:satisfaction-recipients:columns:v1"
              fontSizePreferencesKey="commercial:satisfaction-recipients:table-font-size:v1"
              renderCard={(recipient) => (
                <CommercialInteractiveDataCard
                  ariaLabel={`${copy.cardOpenHint}: ${recipientCompanyLabel(recipient)}`}
                  onActivate={() => openRecipient(recipient)}
                  openHint={copy.cardOpenHint}
                  fields={[
                    {
                      id: "company",
                      label: copy.colCompany,
                      valueTone: "title",
                      value: recipientCompanyLabel(recipient),
                    },
                    {
                      id: "contact",
                      label: copy.colContact,
                      valueTone: "meta",
                      value: contactLabel(recipient),
                    },
                    { id: "status", label: copy.colStatus, value: statusBadge(recipient) },
                  ]}
                />
              )}
            />
          ) : null}
        </div>
      </CommercialSectionCard>
    </div>
  );
}
