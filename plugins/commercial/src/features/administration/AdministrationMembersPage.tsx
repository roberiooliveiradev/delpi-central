import { EmptyState } from "@delpi/plugin-ui/index";
import { BriefcaseBusiness, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  getSellerPortfoliosLoadSummary,
  listSellerPortfolios,
} from "../../api/commercialPortfolioApi";
import {
  cmEmptyStateClassNames,
  CommercialActionButton,
  CommercialLoadingCard,
  CommercialPageHero,
  CommercialPagePath,
  CommercialStateBanner,
  CommercialStatusBadge,
  type DataTableColumn,
} from "../../app/commercialUi";
import { CommercialDataTableSection } from "../../app/dataTableUi";
import { navigatePluginPath, navigatePluginView } from "../../app/pluginNavigation";
import { useDirectoryUserLabels } from "../../app/useDirectoryUserLabels";
import { ADMINISTRATION_CONTENT } from "../../content/administration";
import type { SellerPortfolio } from "../../types/portfolio";
import {
  buildAdministrationMembersRoster,
  type AdministrationMemberRow,
} from "../../utils/buildAdministrationMembersRoster";
import { buildSellerPortfolioDetailPath } from "../../utils/sellerPortfoliosDeepLink";
import { personLoadByUserId } from "../../utils/portfolioLoad";
import { AdministrationSubNav } from "./AdministrationSubNav";

type AdministrationMembersPageProps = {
  basePath: string;
};

export function AdministrationMembersPage({ basePath }: AdministrationMembersPageProps) {
  const copy = ADMINISTRATION_CONTENT;
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [portfolios, setPortfolios] = useState<SellerPortfolio[]>([]);
  const [loadByPerson, setLoadByPerson] = useState<ReturnType<typeof personLoadByUserId>>(
    () => new Map(),
  );

  const load = useCallback(async (mode: "initial" | "refresh" = "initial") => {
    if (mode === "refresh") setRefreshing(true);
    else setLoading(true);
    setError(null);
    try {
      const [list, summary] = await Promise.all([
        listSellerPortfolios(),
        getSellerPortfoliosLoadSummary(),
      ]);
      setPortfolios(list);
      setLoadByPerson(personLoadByUserId(summary));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : copy.members.loadError);
      setPortfolios([]);
      setLoadByPerson(new Map());
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [copy.members.loadError]);

  useEffect(() => {
    void load("initial");
  }, [load]);

  const roster = useMemo(() => buildAdministrationMembersRoster(portfolios), [portfolios]);
  const userIds = useMemo(() => roster.map((row) => row.userId), [roster]);
  const { byId, labelFor } = useDirectoryUserLabels(userIds);

  const openPortfolio = (portfolioId: string) => {
    const target = buildSellerPortfolioDetailPath(basePath, portfolioId);
    if (target) navigatePluginPath(target);
  };

  const columns: DataTableColumn<AdministrationMemberRow>[] = [
    {
      key: "person",
      header: copy.members.colPerson,
      render: (row) => labelFor(row.userId, byId[row.userId]?.name ?? null),
    },
    {
      key: "email",
      header: copy.members.colEmail,
      render: (row) => byId[row.userId]?.email?.trim() || "—",
    },
    {
      key: "portfolios",
      header: copy.members.colPortfolios,
      render: (row) => (
        <span className="cm-row-actions">
          {row.portfolios.map((portfolio) => (
            <CommercialStatusBadge
              key={portfolio.portfolioId}
              label={portfolio.displayName}
              variant={portfolio.active ? "info" : "neutral"}
            />
          ))}
        </span>
      ),
    },
    {
      key: "role",
      header: copy.members.colRole,
      render: (row) =>
        row.primaryRole === "owner" ? copy.members.roleOwner : copy.members.roleMember,
    },
    {
      key: "actions",
      header: "",
      align: "right",
      render: (row) => {
        const first = row.portfolios[0];
        if (!first) return null;
        const personLoad = loadByPerson.get(row.userId);
        const preferredId = personLoad?.portfolio_ids?.[0] ?? first.portfolioId;
        return (
          <CommercialActionButton variant="ghost" onClick={() => openPortfolio(preferredId)}>
            {copy.members.openPortfolio}
          </CommercialActionButton>
        );
      },
    },
  ];

  const hasActivePortfolio = portfolios.some((item) => item.active);

  return (
    <section className="cm-page-stack cm-administration-members">
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
            label: copy.breadcrumbRoot,
            href: `${basePath}/administration`,
            onNavigate: (event) => {
              event.preventDefault();
              navigatePluginView("administration", { basePath });
            },
          },
        ]}
        current={copy.members.navLabel}
      />

      <AdministrationSubNav basePath={basePath} active="members" />

      <CommercialPageHero
        aria-label={copy.members.title}
        eyebrow={copy.members.eyebrow}
        title={copy.members.title}
        description={loading ? copy.members.loading : copy.members.description}
        actions={
          <CommercialActionButton
            variant="ghost"
            onClick={() => void load("refresh")}
            disabled={loading || refreshing}
          >
            <RefreshCw size={16} strokeWidth={1.75} aria-hidden="true" />
            {copy.members.refresh}
          </CommercialActionButton>
        }
      />

      {error ? (
        <CommercialStateBanner variant="error">{error}</CommercialStateBanner>
      ) : null}

      {loading ? <CommercialLoadingCard title={copy.members.loading} /> : null}

      {!loading && (!hasActivePortfolio || roster.length === 0) ? (
        <EmptyState
          classNames={{ ...cmEmptyStateClassNames, withTitle: true }}
          defaultTitle={copy.members.emptyTitle}
          defaultMessage={copy.members.emptyDescription}
        >
          <CommercialActionButton
            variant="primary"
            onClick={() => navigatePluginView("administration_portfolios", { basePath })}
          >
            <BriefcaseBusiness size={16} strokeWidth={1.75} aria-hidden="true" />
            {copy.members.openPortfolios}
          </CommercialActionButton>
        </EmptyState>
      ) : null}

      {!loading && hasActivePortfolio && roster.length > 0 ? (
        <CommercialDataTableSection
          title={`${copy.members.title} (${roster.length.toLocaleString("pt-BR")})`}
          rows={roster}
          columns={columns}
          rowKey={(row) => row.userId}
          loading={false}
          emptyMessage={copy.members.emptyDescription}
          columnPreferencesKey="commercial:administration-members:columns:v1"
          fontSizePreferencesKey="commercial:administration-members:table-font-size:v1"
          getSearchText={(row) =>
            [
              labelFor(row.userId, byId[row.userId]?.name ?? null),
              byId[row.userId]?.email ?? "",
              ...row.portfolios.map((item) => item.displayName),
            ].join(" ")
          }
        />
      ) : null}
    </section>
  );
}
