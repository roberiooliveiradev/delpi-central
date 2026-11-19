import { Plus, RefreshCw } from "lucide-react";
import type { CSSProperties } from "react";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  HelpTooltip,
  SectionCard,
  SegmentToggle,
  useClientPagination,
  useTableColumnVisibility,
} from "@delpi/plugin-ui/index";

import {
  createSatisfactionCampaign,
  listSatisfactionCampaigns,
} from "../../api/satisfactionSurveysApi";
import {
  CommercialActionButton,
  CommercialClearFiltersButton,
  CommercialDataCardsGrid,
  CommercialDataCardsSortBar,
  CommercialDataListToolbar,
  CommercialDataTable,
  CommercialEmptyState,
  CommercialInteractiveDataCard,
  CommercialLoadingCard,
  CommercialPageHero,
  CommercialPagination,
  CommercialSectionHintLabel,
  CommercialSelectField,
  CommercialStateBanner,
  CommercialTableColumnVisibilityMenu,
  CommercialTableFontSizeControls,
  CommercialTextField,
  UI_PREFIX,
  cmSectionCardClassNames,
  cmSectionLabels,
  usePersistedViewLayout,
  useTableFontSize,
  type DataTableColumn,
} from "../../app/commercialUi";
import { TABLE_PAGE_SIZE_OPTIONS } from "../../app/dataTableUi";
import { useCommercialFloatingNotice } from "../../app/CommercialFloatingNoticeProvider";
import { navigatePluginPath } from "../../app/pluginNavigation";
import { buildSatisfactionCampaignDetailPath } from "../../app/pluginRoutes";
import { usePortfolioScope } from "../../app/PortfolioScopeContext";
import { CM_HELP } from "../../content/helpTooltips";
import { SATISFACTION_CONTENT } from "../../content/satisfactionSurveysContent";
import type { SatisfactionCampaign } from "../../types/satisfactionSurvey";
import type { CampaignFormValues } from "./campaignForm";
import { CampaignFormDialog } from "./CampaignFormDialog";
import { formatSurveyPeriod, formatSurveyUpdatedAt } from "./satisfactionDates";
import {
  campaignYearOptions,
  EMPTY_CAMPAIGN_FILTERS,
  filterCampaigns,
  hasActiveCampaignFilters,
  type CampaignFilters,
} from "./satisfactionFilters";
import {
  EMPTY_CAMPAIGN_SORT,
  isCampaignSortKey,
  nextCampaignSortState,
  sortCampaigns,
  type CampaignSortState,
} from "./satisfactionSort";
import { SatisfactionPagePath } from "./SatisfactionPagePath";
import { campaignStatusLabel, SatisfactionStatusBadge } from "./SatisfactionStatusBadge";

type SatisfactionSurveysPageProps = {
  basePath: string;
};

const STATUS_OPTIONS = (["scheduled", "open", "closed"] as const).map((value) => ({
  value,
  label: campaignStatusLabel(value),
}));

const VIEW_LAYOUT_STORAGE_KEY = "commercial:satisfaction-campaigns:layout";
const COLUMNS_STORAGE_KEY = "commercial:satisfaction-campaigns:columns:v1";
const FONT_SIZE_STORAGE_KEY = "commercial:satisfaction-campaigns:table-font-size:v1";
const DEFAULT_PAGE_SIZE = 20;

const PAGE_SIZE_OPTIONS = TABLE_PAGE_SIZE_OPTIONS.map((size) => ({
  value: String(size),
  label: String(size),
}));

/** UI-02 P2 — lista de campanhas no molde visual de Clientes (ajustes 1–5 do plano). */
export function SatisfactionSurveysPage({ basePath }: SatisfactionSurveysPageProps) {
  const copy = SATISFACTION_CONTENT.list;
  const { canManageSatisfaction, loading: scopeLoading } = usePortfolioScope();
  const { notifySuccess } = useCommercialFloatingNotice();

  const [campaigns, setCampaigns] = useState<SatisfactionCampaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [lastSuccessAt, setLastSuccessAt] = useState<Date | null>(null);
  const [filters, setFilters] = useState<CampaignFilters>(EMPTY_CAMPAIGN_FILTERS);
  const [sort, setSort] = useState<CampaignSortState>(EMPTY_CAMPAIGN_SORT);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
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
        if (!controller.signal.aborted) {
          setCampaigns(items);
          setLastSuccessAt(new Date());
        }
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

  const refreshing = loading && campaigns.length > 0;

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
  const filteredRows = useMemo(
    () => filterCampaigns(campaigns, filters),
    [campaigns, filters],
  );
  const sortedRows = useMemo(
    () => sortCampaigns(filteredRows, sort.sortKey, sort.sortDirection),
    [filteredRows, sort],
  );
  const { page, setPage, slice, total } = useClientPagination(sortedRows, pageSize);

  const { layout, setLayout } = usePersistedViewLayout({
    storageKey: VIEW_LAYOUT_STORAGE_KEY,
    defaultMode: "table",
    mobileMaxWidthPx: 768,
  });

  const columns = useMemo<DataTableColumn<SatisfactionCampaign>[]>(
    () => [
      {
        key: "name",
        header: copy.colCampaign,
        headerHint: CM_HELP.satisfactionSurveys.colCampaign,
        sortable: true,
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
        sortable: true,
        render: (row) => <SatisfactionStatusBadge status={row.status} />,
      },
      {
        key: "participants",
        header: copy.colParticipants,
        headerHint: CM_HELP.satisfactionSurveys.colParticipants,
        sortable: true,
        align: "right",
        render: (row) => row.counts.participants.toLocaleString("pt-BR"),
      },
      {
        key: "responded",
        header: copy.colResponded,
        headerHint: CM_HELP.satisfactionSurveys.colResponded,
        sortable: true,
        align: "right",
        render: (row) => row.counts.responded.toLocaleString("pt-BR"),
      },
      {
        key: "response_rate",
        header: copy.colResponseRate,
        headerHint: CM_HELP.satisfactionSurveys.colResponseRate,
        sortable: true,
        align: "right",
        render: (row) =>
          row.response_rate == null
            ? copy.responseRateUnavailable
            : `${row.response_rate.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`,
      },
    ],
    [copy],
  );

  const columnCatalog = useMemo(
    () => columns.map((column) => ({ key: column.key, label: column.header })),
    [columns],
  );

  const {
    visibility,
    orderedColumns,
    setColumnVisible,
    reorderColumns,
    applyVisibleOrder,
    reset: resetColumnVisibility,
    filterColumns,
  } = useTableColumnVisibility({
    storageKey: COLUMNS_STORAGE_KEY,
    columns: columnCatalog,
  });

  const fontSizeControls = useTableFontSize({
    storageKey: FONT_SIZE_STORAGE_KEY,
  });

  const tableStyle = {
    "--delpi-ui-table-font-size": `${fontSizeControls.fontSize}px`,
  } as CSSProperties;

  const visibleColumns = useMemo(
    () => filterColumns(columns),
    [columns, filterColumns],
  );

  const sortOptions = useMemo(
    () => [
      { value: "name", label: copy.sortName },
      { value: "period", label: copy.sortPeriod },
      { value: "status", label: copy.colStatus },
      { value: "participants", label: copy.colParticipants },
      { value: "responded", label: copy.colResponded },
      { value: "response_rate", label: copy.colResponseRate },
    ],
    [copy],
  );

  const handleSortChange = useCallback((columnKey: string) => {
    if (isCampaignSortKey(columnKey)) {
      setSort((current) => nextCampaignSortState(current, columnKey));
    }
  }, []);

  const handleSortDirectionChange = useCallback((direction: string) => {
    if (direction === "asc" || direction === "desc") {
      setSort((current) => ({
        sortKey: current.sortKey ?? "name",
        sortDirection: direction,
      }));
    }
  }, []);

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

  const responseRateValue = (campaign: SatisfactionCampaign) =>
    campaign.response_rate == null
      ? copy.responseRateUnavailable
      : `${campaign.response_rate.toLocaleString("pt-BR", {
          maximumFractionDigits: 1,
        })}%`;

  const renderCampaignCard = (campaign: SatisfactionCampaign) => (
    <CommercialInteractiveDataCard
      ariaLabel={`${copy.cardOpenHint}: ${campaign.name}`}
      onActivate={() => openCampaign(campaign)}
      openHint={copy.cardOpenHint}
      fields={[
        { id: "name", label: copy.sortName, valueTone: "title", value: campaign.name },
        {
          id: "status",
          label: copy.colStatus,
          value: <SatisfactionStatusBadge status={campaign.status} />,
        },
        {
          id: "period",
          label: copy.cardPeriod,
          valueTone: "meta",
          value: formatSurveyPeriod(campaign.starts_at, campaign.ends_at),
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
          value: responseRateValue(campaign),
        },
      ]}
    />
  );

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
        eyebrow={copy.eyebrow}
        title={
          <CommercialSectionHintLabel
            label={copy.title}
            hint={CM_HELP.satisfactionSurveys.listPage}
          />
        }
        description={copy.description}
        actions={
          <div className="cm-satisfaction-actions">
            <HelpTooltip
              content={CM_HELP.satisfactionSurveys.updatedAt}
              ariaLabel={`Ajuda: ${SATISFACTION_CONTENT.updatedAt("…")}`}
              wrap
              placement="bottom"
            >
              <span className="delpi-ui-section-hint-label" aria-live="polite">
                {lastSuccessAt
                  ? SATISFACTION_CONTENT.updatedAt(formatSurveyUpdatedAt(lastSuccessAt))
                  : ""}
                {refreshing ? ` · ${SATISFACTION_CONTENT.updating}` : ""}
              </span>
            </HelpTooltip>
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
        <SectionCard
          title={copy.tableTitle}
          classNames={cmSectionCardClassNames}
          labels={cmSectionLabels}
          hint={CM_HELP.satisfactionSurveys.campaignsTable}
        >
          <CommercialDataListToolbar
            style={tableStyle}
            leading={
              <HelpTooltip
                content={CM_HELP.satisfactionSurveys.layoutToggle}
                ariaLabel={`Ajuda: ${copy.layoutToggle}`}
                wrap
                placement="bottom"
              >
                <SegmentToggle
                  prefix={UI_PREFIX}
                  size="sm"
                  ariaLabel={copy.layoutToggle}
                  idPrefix="satisfaction-campaigns-layout"
                  value={layout}
                  onChange={setLayout}
                  options={[
                    { value: "table", label: copy.layoutTable },
                    { value: "cards", label: copy.layoutCards },
                  ]}
                />
              </HelpTooltip>
            }
            hint={
              <span className="delpi-ui-section-hint-label">
                {copy.recordsCount(total)}
              </span>
            }
            actions={
              <>
                <CommercialSelectField
                  id="satisfaction-campaigns-page-size"
                  label={copy.pageSize}
                  hint={CM_HELP.satisfactionSurveys.pageSize}
                  value={String(pageSize)}
                  options={PAGE_SIZE_OPTIONS}
                  onChange={(value) => {
                    const next = Number(value);
                    if (Number.isFinite(next) && next > 0) setPageSize(next);
                  }}
                />
                <CommercialTableFontSizeControls
                  fontSize={fontSizeControls.fontSize}
                  onIncrease={fontSizeControls.increase}
                  onDecrease={fontSizeControls.decrease}
                  onReset={fontSizeControls.reset}
                  canIncrease={fontSizeControls.canIncrease}
                  canDecrease={fontSizeControls.canDecrease}
                  isDefault={fontSizeControls.isDefault}
                />
                <CommercialTableColumnVisibilityMenu
                  columns={orderedColumns}
                  visibility={visibility}
                  onToggleColumn={setColumnVisible}
                  onReorderColumns={reorderColumns}
                  onReset={resetColumnVisibility}
                  labels={{
                    trigger: copy.columnsMenu,
                    panelTitle: copy.columnsMenuTitle,
                    reset: copy.columnsMenuReset,
                    hint: CM_HELP.satisfactionSurveys.tableColumns,
                    columnAriaLabel: copy.columnAriaLabel,
                    reorderAriaLabel: copy.columnReorderAriaLabel,
                  }}
                />
              </>
            }
          />

          {layout === "cards" ? (
            <CommercialDataCardsSortBar
              style={tableStyle}
              sortField={
                <CommercialSelectField
                  id="satisfaction-campaigns-sort"
                  label={copy.sortBy}
                  hint={CM_HELP.satisfactionSurveys.sortBy}
                  value={sort.sortKey ?? "name"}
                  options={sortOptions}
                  onChange={handleSortChange}
                />
              }
              direction={
                <HelpTooltip
                  content={CM_HELP.satisfactionSurveys.sortDirection}
                  ariaLabel={`Ajuda: ${copy.sortDirection}`}
                  wrap
                  placement="bottom"
                >
                  <SegmentToggle
                    prefix={UI_PREFIX}
                    size="sm"
                    ariaLabel={copy.sortDirection}
                    idPrefix="satisfaction-campaigns-sort-dir"
                    value={sort.sortDirection}
                    onChange={handleSortDirectionChange}
                    options={[
                      { value: "asc", label: copy.sortAsc },
                      { value: "desc", label: copy.sortDesc },
                    ]}
                  />
                </HelpTooltip>
              }
            />
          ) : null}

          {layout === "cards" ? (
            <CommercialDataCardsGrid
              style={tableStyle}
              ariaLabel={copy.tableTitle}
              empty={slice.length === 0 ? copy.emptyFiltered : undefined}
            >
              {slice.map((campaign) => (
                <div key={campaign.id}>{renderCampaignCard(campaign)}</div>
              ))}
            </CommercialDataCardsGrid>
          ) : (
            <div style={tableStyle}>
              <CommercialDataTable
                rows={slice}
                columns={visibleColumns}
                rowKey={(campaign) => campaign.id}
                layout="section"
                emptyMessage={copy.emptyFiltered}
                sortKey={sort.sortKey}
                sortDirection={sort.sortDirection}
                onSortChange={handleSortChange}
                onRowClick={openCampaign}
                rowClickRole="button"
                enableColumnReorder
                onColumnOrderChange={applyVisibleOrder}
              />
            </div>
          )}

          <CommercialPagination
            page={page}
            pageSize={pageSize}
            total={total}
            onPageChange={setPage}
          />
        </SectionCard>
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
