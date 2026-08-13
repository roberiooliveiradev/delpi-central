import { useCallback, useEffect, useMemo, useState } from "react";
import { RefreshCw, UsersRound } from "lucide-react";

import {
  listTeamRoster,
  type TeamRosterPersonDto,
} from "../../api/administrationTeamApi";
import { listCommercialGroups } from "../../api/commercialGroupsApi";
import { listSellerPortfolios } from "../../api/commercialPortfolioApi";
import {
  useCommercialPresenceSync,
} from "../../app/CommercialRealtimeProvider";
import {
  CommercialActionButton,
  CommercialEmptyState,
  CommercialFilterBarShell,
  CommercialLoadingCard,
  CommercialOrgMembershipFlow,
  CommercialPageHero,
  CommercialPagePath,
  CommercialSectionCard,
  CommercialSegmentToggle,
  CommercialSelectField,
  CommercialStateBanner,
  CommercialStatusBadge,
  CommercialTextField,
  type DataTableColumn,
} from "../../app/commercialUi";
import { CommercialDataTableSection } from "../../app/dataTableUi";
import { navigatePluginView, navigateUserProfile } from "../../app/pluginNavigation";
import type { CommercialPresenceUpdatedEvent } from "../../constants/realtime";
import { ADMINISTRATION_CONTENT } from "../../content/administration";
import type { SellerPortfolio } from "../../types/portfolio";
import {
  parseCommercialTeamView,
  replaceCommercialTeamViewInUrl,
  type CommercialTeamView,
} from "../../utils/commercialTeamDeepLink";
import { buildCommercialGroupsOrgFlowModel } from "../../utils/commercialTeamOrgFlow";
import { AdministrationSubNav } from "./AdministrationSubNav";

type AdministrationTeamPageProps = {
  basePath: string;
};

type OnlineFilter = "all" | "online" | "offline";

type TeamRow = TeamRosterPersonDto & { online: boolean };

export function AdministrationTeamPage({ basePath }: AdministrationTeamPageProps) {
  const copy = ADMINISTRATION_CONTENT.team;
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [roster, setRoster] = useState<TeamRosterPersonDto[]>([]);
  const [groups, setGroups] = useState<Array<{ id: string; name: string }>>([]);
  const [portfolios, setPortfolios] = useState<SellerPortfolio[]>([]);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [groupId, setGroupId] = useState("");
  const [portfolioId, setPortfolioId] = useState("");
  const [onlineFilter, setOnlineFilter] = useState<OnlineFilter>("all");
  const [onlineUserIds, setOnlineUserIds] = useState<Set<string>>(() => new Set());
  const [view, setView] = useState<CommercialTeamView>(() => parseCommercialTeamView());

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedSearch(search.trim()), 280);
    return () => window.clearTimeout(timer);
  }, [search]);

  useCommercialPresenceSync(
    useCallback((event: CommercialPresenceUpdatedEvent) => {
      setOnlineUserIds(new Set(event.onlineUserIds.map((id) => id.trim()).filter(Boolean)));
    }, []),
  );

  const applyView = useCallback((next: CommercialTeamView) => {
    setView(next);
    replaceCommercialTeamViewInUrl(next);
  }, []);

  const loadFilters = useCallback(async (signal?: AbortSignal) => {
    const [groupItems, portfolioItems] = await Promise.all([
      listCommercialGroups({ activeOnly: false, signal }),
      listSellerPortfolios({ signal }),
    ]);
    if (signal?.aborted) return;
    setGroups(
      groupItems
        .map((item) => ({ id: item.id, name: item.name }))
        .sort((a, b) => a.name.localeCompare(b.name, "pt-BR")),
    );
    setPortfolios(portfolioItems);
  }, []);

  const loadRoster = useCallback(
    async (mode: "initial" | "refresh" = "initial", signal?: AbortSignal) => {
      if (mode === "refresh") setRefreshing(true);
      else setLoading(true);
      setError(null);
      try {
        const items = await listTeamRoster({
          groupId: groupId || null,
          portfolioId: portfolioId || null,
          q: debouncedSearch || null,
          signal,
        });
        if (signal?.aborted) return;
        setRoster(items);
      } catch (err: unknown) {
        if (signal?.aborted) return;
        setError(err instanceof Error ? err.message : copy.loadError);
        setRoster([]);
      } finally {
        if (!signal?.aborted) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    },
    [copy.loadError, debouncedSearch, groupId, portfolioId],
  );

  useEffect(() => {
    const controller = new AbortController();
    void loadFilters(controller.signal).catch(() => {
      /* filtros auxiliares — roster ainda carrega */
    });
    return () => controller.abort();
  }, [loadFilters]);

  useEffect(() => {
    const controller = new AbortController();
    void loadRoster("initial", controller.signal);
    return () => controller.abort();
  }, [loadRoster]);

  const rows = useMemo<TeamRow[]>(() => {
    const mapped = roster.map((item) => ({
      ...item,
      online: onlineUserIds.has(item.user_id),
    }));
    if (onlineFilter === "online") return mapped.filter((row) => row.online);
    if (onlineFilter === "offline") return mapped.filter((row) => !row.online);
    return mapped;
  }, [onlineFilter, onlineUserIds, roster]);

  const orgFlowModel = useMemo(
    () => buildCommercialGroupsOrgFlowModel({ people: rows }),
    [rows],
  );

  const columns: DataTableColumn<TeamRow>[] = [
    {
      key: "person",
      header: copy.colPerson,
      render: (row) => row.name || row.user_id,
    },
    {
      key: "online",
      header: copy.colOnline,
      render: (row) => (
        <CommercialStatusBadge
          label={row.online ? copy.statusOnline : copy.statusOffline}
          variant={row.online ? "success" : "neutral"}
        />
      ),
    },
    {
      key: "email",
      header: copy.colEmail,
      render: (row) => row.email?.trim() || "—",
    },
    {
      key: "groups",
      header: copy.colGroups,
      render: (row) =>
        row.groups.length === 0 ? (
          "—"
        ) : (
          <span className="cm-row-actions">
            {row.groups.map((group) => (
              <CommercialStatusBadge
                key={group.id}
                label={group.name}
                variant={group.active ? "info" : "neutral"}
              />
            ))}
          </span>
        ),
    },
    {
      key: "portfolios",
      header: copy.colPortfolios,
      render: (row) =>
        row.portfolios.length === 0 ? (
          "—"
        ) : (
          <span className="cm-row-actions">
            {row.portfolios.map((portfolio) => (
              <CommercialStatusBadge
                key={portfolio.id}
                label={portfolio.name}
                variant={portfolio.active ? "info" : "neutral"}
              />
            ))}
          </span>
        ),
    },
    {
      key: "actions",
      header: "",
      align: "right",
      render: (row) => (
        <CommercialActionButton
          variant="ghost"
          onClick={() => navigateUserProfile(row.user_id, { basePath })}
        >
          {copy.viewProfile}
        </CommercialActionButton>
      ),
    },
  ];

  return (
    <section className="cm-page-stack cm-administration-team">
      <CommercialPagePath
        back={{
          label: "Portal Comercial",
          href: basePath,
          onNavigate: (event) => {
            event.preventDefault();
            navigatePluginView("home", { basePath });
          },
        }}
        items={[
          {
            id: "admin",
            label: ADMINISTRATION_CONTENT.breadcrumbRoot,
            href: `${basePath}/administration`,
            onNavigate: (event) => {
              event.preventDefault();
              navigatePluginView("administration", { basePath });
            },
          },
        ]}
        current={copy.navLabel}
      />

      <AdministrationSubNav basePath={basePath} active="team" />

      <CommercialPageHero
        aria-label={copy.title}
        eyebrow={copy.eyebrow}
        title={copy.title}
        description={loading ? copy.loading : copy.description}
        actions={
          <>
            <CommercialSegmentToggle
              size="sm"
              ariaLabel={copy.viewToggleAria}
              idPrefix="administration-team-view"
              value={view}
              onChange={(next) => applyView(next as CommercialTeamView)}
              options={[
                { value: "list", label: copy.viewList },
                { value: "org", label: copy.viewOrg },
              ]}
            />
            <CommercialActionButton
              variant="ghost"
              onClick={() => void loadRoster("refresh")}
              disabled={loading || refreshing}
            >
              <RefreshCw size={16} strokeWidth={1.75} aria-hidden="true" />
              {copy.refresh}
            </CommercialActionButton>
          </>
        }
      />

      <CommercialFilterBarShell embedded ariaLabel="Filtros da equipe">
        <CommercialTextField
          label={copy.filterSearch}
          type="search"
          value={search}
          onChange={setSearch}
          placeholder={copy.filterSearchPlaceholder}
        />
        <CommercialSelectField
          label={copy.filterGroup}
          value={groupId}
          onChange={setGroupId}
          options={groups.map((group) => ({ value: group.id, label: group.name }))}
          allowEmpty
          emptyLabel={copy.filterAllOption}
        />
        <CommercialSelectField
          label={copy.filterPortfolio}
          value={portfolioId}
          onChange={setPortfolioId}
          options={portfolios.map((portfolio) => ({
            value: portfolio.id,
            label: portfolio.display_name,
          }))}
          allowEmpty
          emptyLabel={copy.filterAllOption}
        />
        <CommercialSegmentToggle
          size="sm"
          ariaLabel={copy.filterOnline}
          idPrefix="administration-team-online"
          value={onlineFilter}
          onChange={(value) => setOnlineFilter(value as OnlineFilter)}
          options={[
            { value: "all", label: copy.filterOnlineAll },
            { value: "online", label: copy.filterOnlineOnly },
            { value: "offline", label: copy.filterOfflineOnly },
          ]}
        />
      </CommercialFilterBarShell>

      {error ? (
        <CommercialStateBanner variant="error">{error}</CommercialStateBanner>
      ) : null}

      {loading ? <CommercialLoadingCard title={copy.loading} /> : null}

      {!loading && rows.length === 0 ? (
        <CommercialEmptyState
          defaultTitle={copy.emptyTitle}
          defaultMessage={copy.emptyDescription}
        >
          <div className="cm-portfolios-page__actions">
            <CommercialActionButton
              variant="primary"
              onClick={() => navigatePluginView("administration_portfolios", { basePath })}
            >
              {copy.openPortfolios}
            </CommercialActionButton>
            <CommercialActionButton
              variant="ghost"
              onClick={() => navigatePluginView("administration_groups", { basePath })}
            >
              <UsersRound size={16} strokeWidth={1.75} aria-hidden="true" />
              {copy.openGroups}
            </CommercialActionButton>
          </div>
        </CommercialEmptyState>
      ) : null}

      {!loading && rows.length > 0 && view === "list" ? (
        <CommercialDataTableSection
          title={`${copy.title} (${rows.length.toLocaleString("pt-BR")})`}
          rows={rows}
          columns={columns}
          rowKey={(row) => row.user_id}
          loading={false}
          emptyMessage={copy.emptyDescription}
          columnPreferencesKey="commercial:administration-team:columns:v1"
          fontSizePreferencesKey="commercial:administration-team:table-font-size:v1"
          getSearchText={(row) =>
            [
              row.name,
              row.email,
              ...row.groups.map((item) => item.name),
              ...row.portfolios.map((item) => item.name),
            ].join(" ")
          }
        />
      ) : null}

      {!loading && rows.length > 0 && view === "org" ? (
        <CommercialSectionCard title={copy.orgTitle} subtitle={copy.orgSubtitle}>
          {orgFlowModel.edges.length === 0 &&
          orgFlowModel.nodes.every((node) => node.kind === "person") ? (
            <CommercialEmptyState defaultMessage={copy.orgEmpty} />
          ) : (
            <CommercialOrgMembershipFlow
              nodes={orgFlowModel.nodes}
              edges={orgFlowModel.edges}
              portalScopeClassName="dashboard-commercial"
              fullscreenTitle={copy.orgTitle}
              fullscreenSubtitle={copy.orgSubtitle}
              aria-label={copy.orgAriaLabel}
              emptyMessage={copy.orgEmpty}
              onNodeClick={(payload) => {
                if (payload.kind !== "person") return;
                navigateUserProfile(payload.entityId, { basePath });
              }}
            />
          )}
        </CommercialSectionCard>
      ) : null}
    </section>
  );
}
