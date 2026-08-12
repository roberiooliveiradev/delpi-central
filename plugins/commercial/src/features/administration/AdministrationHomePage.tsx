import { ActionButton, EmptyState, SectionCard } from "@delpi/plugin-ui/index";
import {
  ArrowLeftRight,
  BriefcaseBusiness,
  Plus,
  RefreshCw,
  UserRoundX,
  Users,
  UsersRound,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  getSellerPortfoliosCoverageAudit,
  listSellerPortfolios,
} from "../../api/commercialPortfolioApi";
import {
  cmEmptyStateClassNames,
  cmSectionCardClassNames,
  cmSectionLabels,
  CommercialActionButton,
  CommercialLoadingCard,
  CommercialPageHero,
  CommercialPagePath,
  CommercialStateBanner,
} from "../../app/commercialUi";
import { navigatePluginView } from "../../app/pluginNavigation";
import { KpiCard } from "../../components/KpiCard";
import { ADMINISTRATION_CONTENT } from "../../content/administration";
import type { SellerPortfolio, SellerPortfoliosCoverageAudit } from "../../types/portfolio";
import { AdministrationSubNav } from "./AdministrationSubNav";

type AdministrationHomePageProps = {
  basePath: string;
};

export function AdministrationHomePage({ basePath }: AdministrationHomePageProps) {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [portfolios, setPortfolios] = useState<SellerPortfolio[]>([]);
  const [coverage, setCoverage] = useState<SellerPortfoliosCoverageAudit | null>(null);

  const load = useCallback(async (mode: "initial" | "refresh" = "initial") => {
    if (mode === "refresh") setRefreshing(true);
    else setLoading(true);
    setError(null);
    try {
      const [list, audit] = await Promise.all([
        listSellerPortfolios(),
        getSellerPortfoliosCoverageAudit(),
      ]);
      setPortfolios(list);
      setCoverage(audit);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : ADMINISTRATION_CONTENT.panel.loadError);
      setPortfolios([]);
      setCoverage(null);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void load("initial");
  }, [load]);

  const stats = useMemo(() => {
    const active = portfolios.filter((item) => item.active).length;
    return {
      total: portfolios.length,
      active,
      inactive: portfolios.length - active,
      customers: portfolios.reduce((sum, item) => sum + (item.customer_count ?? 0), 0),
      overlappingCustomers: coverage?.overlapping_count ?? 0,
      uncoveredCount: coverage?.gap?.available ? (coverage.gap.uncovered_count ?? 0) : null,
    };
  }, [coverage, portfolios]);

  const copy = ADMINISTRATION_CONTENT;

  const openPortfolios = (search?: string) =>
    navigatePluginView("administration_portfolios", { basePath, search });

  return (
    <section className="cm-page-stack cm-administration-home">
      <CommercialPagePath
        back={{
          label: "Portal Comercial",
          href: basePath,
          onNavigate: (event) => {
            event.preventDefault();
            navigatePluginView("home", { basePath });
          },
        }}
        items={[]}
        current={copy.breadcrumbRoot}
      />

      <AdministrationSubNav basePath={basePath} active="panel" />

      <CommercialPageHero
        aria-label={copy.panel.title}
        eyebrow={copy.panel.eyebrow}
        title={copy.panel.title}
        description={loading ? copy.panel.loading : copy.panel.description}
        actions={
          <CommercialActionButton
            variant="ghost"
            onClick={() => void load("refresh")}
            disabled={loading || refreshing}
          >
            <RefreshCw size={16} strokeWidth={1.75} aria-hidden="true" />
            {copy.panel.refresh}
          </CommercialActionButton>
        }
      />

      {error ? (
        <CommercialStateBanner variant="error">{error}</CommercialStateBanner>
      ) : null}

      {loading ? <CommercialLoadingCard label={copy.panel.loading} /> : null}

      {!loading ? (
        <div className="cm-home-kpi-grid" aria-label="Resumo de carteiras">
          <KpiCard
            title={copy.metrics.total}
            value={stats.total.toLocaleString("pt-BR")}
            icon={<BriefcaseBusiness size={22} />}
            onClick={() => openPortfolios()}
          />
          <KpiCard
            title={copy.metrics.active}
            value={stats.active.toLocaleString("pt-BR")}
            icon={<UsersRound size={22} />}
            onClick={() => openPortfolios("?filter=active")}
          />
          <KpiCard
            title={copy.metrics.inactive}
            value={stats.inactive.toLocaleString("pt-BR")}
            icon={<Users size={22} />}
            onClick={() => openPortfolios("?filter=inactive")}
          />
          <KpiCard
            title={copy.metrics.customers}
            value={stats.customers.toLocaleString("pt-BR")}
            icon={<Users size={22} />}
            onClick={() => openPortfolios()}
          />
          <KpiCard
            title={copy.metrics.overlapping}
            value={stats.overlappingCustomers.toLocaleString("pt-BR")}
            icon={<UsersRound size={22} />}
            onClick={() => openPortfolios("?filter=overlapping")}
          />
          <KpiCard
            title={copy.metrics.uncovered}
            value={
              stats.uncoveredCount === null ? "—" : stats.uncoveredCount.toLocaleString("pt-BR")
            }
            icon={<UserRoundX size={22} />}
            onClick={() => openPortfolios("?filter=uncovered")}
          />
        </div>
      ) : null}

      <SectionCard
        title={copy.panel.actionsTitle}
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        {stats.total === 0 && !loading ? (
          <EmptyState
            classNames={cmEmptyStateClassNames}
            title="Nenhuma carteira cadastrada"
            description="Cadastre a primeira carteira para começar a cobrir clientes."
            action={
              <ActionButton variant="primary" onClick={() => openPortfolios()}>
                <Plus size={16} strokeWidth={1.75} aria-hidden="true" />
                {copy.panel.newPortfolio}
              </ActionButton>
            }
          />
        ) : (
          <div className="cm-portfolios-page__actions">
            <CommercialActionButton variant="primary" onClick={() => openPortfolios()}>
              <Plus size={16} strokeWidth={1.75} aria-hidden="true" />
              {copy.panel.newPortfolio}
            </CommercialActionButton>
            <CommercialActionButton variant="ghost" onClick={() => openPortfolios()}>
              <ArrowLeftRight size={16} strokeWidth={1.75} aria-hidden="true" />
              {copy.panel.bulkTransfer}
            </CommercialActionButton>
            <CommercialActionButton variant="ghost" onClick={() => openPortfolios()}>
              {copy.panel.openPortfolios}
            </CommercialActionButton>
            <CommercialActionButton
              variant="ghost"
              onClick={() => navigatePluginView("administration_members", { basePath })}
            >
              <Users size={16} strokeWidth={1.75} aria-hidden="true" />
              {copy.panel.openMembers}
            </CommercialActionButton>
          </div>
        )}
      </SectionCard>
    </section>
  );
}
