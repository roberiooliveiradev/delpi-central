import { Plus, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  createSatisfactionCampaign,
  listSatisfactionCampaigns,
} from "../../api/satisfactionSurveysApi";
import {
  CommercialActionButton,
  CommercialClearFiltersButton,
  CommercialEmptyState,
  CommercialInteractiveDataCard,
  CommercialLoadingCard,
  CommercialPageHero,
  CommercialSectionHintLabel,
  CommercialSelectField,
  CommercialStateBanner,
  CommercialTextField,
  type DataTableColumn,
} from "../../app/commercialUi";
import { useCommercialFloatingNotice } from "../../app/CommercialFloatingNoticeProvider";
import { CommercialDataTableSection } from "../../app/dataTableUi";
import { navigatePluginPath } from "../../app/pluginNavigation";
import { buildSatisfactionCampaignDetailPath } from "../../app/pluginRoutes";
import { usePortfolioScope } from "../../app/PortfolioScopeContext";
import { CM_HELP } from "../../content/helpTooltips";
import { SATISFACTION_CONTENT } from "../../content/satisfactionSurveysContent";
import type { SatisfactionCampaign } from "../../types/satisfactionSurvey";
import type { CampaignFormValues } from "./campaignForm";
import { CampaignFormDialog } from "./CampaignFormDialog";
import { formatSurveyPeriod } from "./satisfactionDates";
import {
  campaignYearOptions,
  EMPTY_CAMPAIGN_FILTERS,
  filterCampaigns,
  hasActiveCampaignFilters,
  type CampaignFilters,
} from "./satisfactionFilters";
import { SatisfactionPagePath } from "./SatisfactionPagePath";
import { campaignStatusLabel, SatisfactionStatusBadge } from "./SatisfactionStatusBadge";

type SatisfactionSurveysPageProps = {
  basePath: string;
};

const STATUS_OPTIONS = (["scheduled", "open", "closed"] as const).map((value) => ({
  value,
  label: campaignStatusLabel(value),
}));

/** UI-02A — lista de campanhas + diálogo «Nova campanha» (escopo parcial A/B). */
export function SatisfactionSurveysPage({ basePath }: SatisfactionSurveysPageProps) {
  const copy = SATISFACTION_CONTENT.list;
  const { canManageSatisfaction, loading: scopeLoading } = usePortfolioScope();
  const { notifySuccess } = useCommercialFloatingNotice();

  const [campaigns, setCampaigns] = useState<SatisfactionCampaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [filters, setFilters] = useState<CampaignFilters>(EMPTY_CAMPAIGN_FILTERS);
  const [createOpen, setCreateOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  useEffect(() => {
    if (!canManageSatisfaction) {
      setLoading(false);
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    listSatisfactionCampaigns(controller.signal)
      .then((items) => {
        if (!controller.signal.aborted) setCampaigns(items);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setCampaigns([]);
        setError(err instanceof Error ? err.message : copy.loadError);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [canManageSatisfaction, copy.loadError, reloadKey]);

  const openCampaign = useCallback(
    (campaign: SatisfactionCampaign) => {
      const href = buildSatisfactionCampaignDetailPath(basePath, campaign.id);
      if (href) navigatePluginPath(href);
    },
    [basePath],
  );

  const yearOptions = useMemo(
    () => campaignYearOptions(campaigns).map((year) => ({ value: year, label: year })),
    [campaigns],
  );
  const rows = useMemo(() => filterCampaigns(campaigns, filters), [campaigns, filters]);

  const submitCreate = async (values: CampaignFormValues) => {
    setCreating(true);
    setCreateError(null);
    try {
      const created = await createSatisfactionCampaign({
        name: values.name,
        starts_at: values.startsAtIso,
        ends_at: values.endsAtIso,
      });
      notifySuccess(SATISFACTION_CONTENT.campaignForm.createSuccess);
      setCreateOpen(false);
      openCampaign(created);
    } catch (err: unknown) {
      setCreateError(err instanceof Error ? err.message : copy.loadError);
    } finally {
      setCreating(false);
    }
  };

  const columns: DataTableColumn<SatisfactionCampaign>[] = [
    {
      key: "name",
      header: copy.colCampaign,
      headerHint: CM_HELP.satisfactionSurveys.colCampaign,
      render: (row) => (
        <span>
          <strong>{row.name}</strong>
          <br />
          <small>{formatSurveyPeriod(row.starts_at, row.ends_at)}</small>
        </span>
      ),
    },
    {
      key: "status",
      header: copy.colStatus,
      headerHint: CM_HELP.satisfactionSurveys.colStatus,
      render: (row) => <SatisfactionStatusBadge status={row.status} />,
    },
    {
      key: "participants",
      header: copy.colParticipants,
      headerHint: CM_HELP.satisfactionSurveys.colParticipants,
      align: "right",
      render: (row) => row.counts.participants.toLocaleString("pt-BR"),
    },
    {
      key: "responded",
      header: copy.colResponded,
      headerHint: CM_HELP.satisfactionSurveys.colResponded,
      align: "right",
      render: (row) => row.counts.responded.toLocaleString("pt-BR"),
    },
    {
      key: "response_rate",
      header: copy.colResponseRate,
      headerHint: CM_HELP.satisfactionSurveys.colResponseRate,
      align: "right",
      render: (row) =>
        row.response_rate == null
          ? copy.responseRateUnavailable
          : `${row.response_rate.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`,
    },
  ];

  if (!scopeLoading && !canManageSatisfaction) {
    return (
      <section className="cm-page-stack">
        <SatisfactionPagePath basePath={basePath} ariaLabel={copy.title} current={SATISFACTION_CONTENT.breadcrumbRoot} />
        <CommercialEmptyState title={copy.forbiddenTitle} message={copy.forbiddenMessage} />
      </section>
    );
  }

  return (
    <section className="cm-page-stack cm-satisfaction-surveys">
      <SatisfactionPagePath basePath={basePath} ariaLabel={copy.title} current={SATISFACTION_CONTENT.breadcrumbRoot} />
      <CommercialPageHero
        aria-label={copy.title}
        title={
          <CommercialSectionHintLabel
            label={copy.title}
            hint={CM_HELP.satisfactionSurveys.listPage}
          />
        }
        description={copy.description}
        actions={
          <div className="cm-satisfaction-actions">
            <CommercialActionButton variant="ghost" onClick={() => setReloadKey((v) => v + 1)}>
              <RefreshCw size={16} aria-hidden="true" /> {copy.refresh}
            </CommercialActionButton>
            <CommercialActionButton
              variant="primary"
              onClick={() => {
                setCreateError(null);
                setCreateOpen(true);
              }}
            >
              <Plus size={16} aria-hidden="true" /> {copy.newCampaign}
            </CommercialActionButton>
          </div>
        }
      >
        <div className="cm-satisfaction-filters">
          <CommercialSelectField
            label={copy.filterYear}
            hint={CM_HELP.satisfactionSurveys.filterYear}
            value={filters.year}
            options={yearOptions}
            allowEmpty
            emptyLabel={copy.filterYearAll}
            onChange={(year) => setFilters((prev) => ({ ...prev, year }))}
          />
          <CommercialSelectField
            label={copy.filterStatus}
            hint={CM_HELP.satisfactionSurveys.filterStatus}
            value={filters.status}
            options={STATUS_OPTIONS}
            allowEmpty
            emptyLabel={copy.filterStatusAll}
            onChange={(status) =>
              setFilters((prev) => ({
                ...prev,
                status: status === "scheduled" || status === "open" || status === "closed" ? status : "",
              }))
            }
          />
          <CommercialTextField
            label={copy.filterSearch}
            hint={CM_HELP.satisfactionSurveys.filterSearch}
            type="search"
            placeholder={copy.filterSearchPlaceholder}
            value={filters.search}
            onChange={(search) => setFilters((prev) => ({ ...prev, search }))}
          />
          {hasActiveCampaignFilters(filters) ? (
            <CommercialClearFiltersButton onClick={() => setFilters(EMPTY_CAMPAIGN_FILTERS)} />
          ) : null}
        </div>
      </CommercialPageHero>

      <CommercialStateBanner>{copy.partialScope}</CommercialStateBanner>

      {error ? (
        <CommercialStateBanner variant="error">
          {error}{" "}
          <CommercialActionButton variant="ghost" onClick={() => setReloadKey((v) => v + 1)}>
            {copy.refresh}
          </CommercialActionButton>
        </CommercialStateBanner>
      ) : null}

      {loading && campaigns.length === 0 ? (
        <CommercialLoadingCard title={copy.loading} variant="panel" />
      ) : null}

      {!loading && !error && campaigns.length === 0 ? (
        <CommercialEmptyState title={copy.emptyTitle} message={copy.emptyMessage} />
      ) : null}

      {campaigns.length > 0 ? (
        <CommercialDataTableSection
          title={copy.tableTitle}
          columns={columns}
          rows={rows}
          rowKey={(row) => row.id}
          loading={loading}
          hideSearch
          emptyMessage={copy.emptyFiltered}
          onRowClick={openCampaign}
          viewLayoutPreferencesKey="commercial:satisfaction-campaigns:layout"
          columnPreferencesKey="commercial:satisfaction-campaigns:columns:v1"
          fontSizePreferencesKey="commercial:satisfaction-campaigns:table-font-size:v1"
          renderCard={(campaign) => (
            <CommercialInteractiveDataCard
              ariaLabel={`${copy.cardOpenHint}: ${campaign.name}`}
              onActivate={() => openCampaign(campaign)}
              openHint={copy.cardOpenHint}
              fields={[
                { id: "name", label: copy.colCampaign, valueTone: "title", value: campaign.name },
                {
                  id: "period",
                  label: copy.colCampaign,
                  valueTone: "meta",
                  value: formatSurveyPeriod(campaign.starts_at, campaign.ends_at),
                },
                {
                  id: "status",
                  label: copy.colStatus,
                  value: <SatisfactionStatusBadge status={campaign.status} />,
                },
                {
                  id: "participants",
                  label: copy.colParticipants,
                  valueTone: "value",
                  value: campaign.counts.participants.toLocaleString("pt-BR"),
                },
                {
                  id: "responded",
                  label: copy.colResponded,
                  valueTone: "value",
                  value: campaign.counts.responded.toLocaleString("pt-BR"),
                },
                {
                  id: "response_rate",
                  label: copy.colResponseRate,
                  valueTone: "value",
                  value:
                    campaign.response_rate == null
                      ? copy.responseRateUnavailable
                      : `${campaign.response_rate.toLocaleString("pt-BR", {
                          maximumFractionDigits: 1,
                        })}%`,
                },
              ]}
            />
          )}
        />
      ) : null}

      <CampaignFormDialog
        open={createOpen}
        mode="create"
        busy={creating}
        submitError={createError}
        onClose={() => setCreateOpen(false)}
        onSubmit={(values) => void submitCreate(values)}
      />
    </section>
  );
}
