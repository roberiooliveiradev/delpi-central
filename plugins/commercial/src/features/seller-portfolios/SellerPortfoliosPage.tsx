import { HelpTooltip, SegmentToggle } from "@delpi/plugin-ui/index";
import { ArrowLeftRight, Download, Plus, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  createSellerPortfolio,
  getSellerPortfoliosCoverageAudit,
  getSellerPortfoliosLoadSummary,
  listSellerPortfolios,
  transferSellerCustomersBulk,
} from "../../api/commercialPortfolioApi";
import {
  useCommercialFloatingNotice,
} from "../../app/CommercialFloatingNoticeProvider";
import { useCommercialPortfolioSync } from "../../app/CommercialRealtimeProvider";
import { navigatePluginPath, navigatePluginView } from "../../app/pluginNavigation";
import { useDirectoryUserLabels } from "../../app/useDirectoryUserLabels";
import {
  CommercialActionButton,
  CommercialFilterBarShell,
  CommercialPageHero,
  CommercialPagePath,
  CommercialScopeChipBar,
  CommercialSectionHintLabel,
  CommercialStateBanner,
  CommercialStatusBadge,
  CommercialTextField,
  UI_PREFIX,
} from "../../app/commercialUi";
import { CM_HELP } from "../../content/helpTooltips";
import { PORTFOLIO_BULK_TRANSFER_CONTENT } from "../../content/portfolioBulkTransferContent";
import { PORTFOLIO_COVERAGE_CONTENT } from "../../content/portfolioCoverageContent";
import { PORTFOLIO_LOAD_CONTENT } from "../../content/portfolioLoadContent";
import type {
  SellerPortfolio,
  SellerPortfoliosCoverageAudit,
  SellerPortfoliosLoadSummary,
} from "../../types/portfolio";
import { customerKey } from "../../shared/format";
import { exportOrgMatrixExcel } from "../../utils/exportOrgMatrixExcel";
import { overlappingPortfolioIdSet } from "../../utils/portfolioCoverage";
import { personLoadByUserId, portfolioLoadById } from "../../utils/portfolioLoad";
import {
  buildSellerPortfolioDetailPath,
  migrateLegacySellerPortfolioIdParam,
  parseSellerPortfoliosRouteState,
  replaceSellerPortfoliosSearch,
  type SellerPortfoliosAxis,
  type SellerPortfoliosDeepLink,
  type SellerPortfoliosFilter,
  type SellerPortfoliosView,
} from "../../utils/sellerPortfoliosDeepLink";
import { SellerPortfolioBulkTransferWizard } from "./SellerPortfolioBulkTransferWizard";
import { SellerPortfolioCreateDialog } from "./SellerPortfolioCreateDialog";
import { SellerPortfoliosList } from "./SellerPortfoliosList";
import { SellerPortfoliosOrgView } from "./SellerPortfoliosOrgView";
import { UncoveredCustomersPanel } from "./UncoveredCustomersPanel";

const FILTER_META: Record<SellerPortfoliosFilter, { label: string; emptyHint: string }> = {
  all: { label: PORTFOLIO_COVERAGE_CONTENT.filterAll, emptyHint: "Cadastre a primeira carteira." },
  active: {
    label: PORTFOLIO_COVERAGE_CONTENT.filterActive,
    emptyHint: "Nenhuma carteira ativa neste filtro.",
  },
  inactive: {
    label: PORTFOLIO_COVERAGE_CONTENT.filterInactive,
    emptyHint: "Nenhuma carteira inativa neste filtro.",
  },
  overlapping: {
    label: PORTFOLIO_COVERAGE_CONTENT.filterOverlapping,
    emptyHint: PORTFOLIO_COVERAGE_CONTENT.filterOverlappingEmpty,
  },
  uncovered: {
    label: PORTFOLIO_COVERAGE_CONTENT.filterUncovered,
    emptyHint: PORTFOLIO_COVERAGE_CONTENT.filterUncoveredEmpty,
  },
};

const DEFAULT_LINK: SellerPortfoliosDeepLink = {
  q: "",
  filter: "all",
  view: "list",
  axis: "portfolio",
};

type SellerPortfoliosPageProps = {
  basePath: string;
};

function formatUpdatedAt(value: Date | null): string {
  if (!value) return "—";
  return value.toLocaleString("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  });
}

function portfolioMatchesQuery(
  portfolio: SellerPortfolio,
  query: string,
  labelFor: (userId: string, fallback?: string | null) => string,
): boolean {
  const normalized = query.trim().toLowerCase();
  if (!normalized) return true;
  const memberIds = (portfolio.members ?? []).map((member) => member.user_id);
  const hay = [
    portfolio.display_name,
    portfolio.user_id,
    portfolio.owner_user_id,
    labelFor(portfolio.owner_user_id ?? portfolio.user_id, portfolio.display_name),
    ...memberIds.map((userId) => labelFor(userId)),
  ]
    .join(" ")
    .toLowerCase();
  return hay.includes(normalized);
}

export function SellerPortfoliosPage({ basePath }: SellerPortfoliosPageProps) {
  const { notifyError, notifySuccess } = useCommercialFloatingNotice();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [portfolios, setPortfolios] = useState<SellerPortfolio[]>([]);
  const [coverageAudit, setCoverageAudit] = useState<SellerPortfoliosCoverageAudit | null>(null);
  const [loadSummary, setLoadSummary] = useState<SellerPortfoliosLoadSummary | null>(null);
  const [lastSuccessAt, setLastSuccessAt] = useState<Date | null>(null);
  const [link, setLink] = useState<SellerPortfoliosDeepLink>(DEFAULT_LINK);
  const [createOpen, setCreateOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [bulkOpen, setBulkOpen] = useState(false);
  const [bulkBusy, setBulkBusy] = useState(false);
  const [bulkError, setBulkError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);

  const directoryUserIds = useMemo(() => {
    const ids = new Set<string>();
    for (const portfolio of portfolios) {
      const owner = (portfolio.owner_user_id ?? portfolio.user_id).trim();
      if (owner) ids.add(owner);
      for (const member of portfolio.members ?? []) {
        if (member.user_id.trim()) ids.add(member.user_id.trim());
      }
    }
    return [...ids];
  }, [portfolios]);
  const { labelFor: directoryLabelFor } = useDirectoryUserLabels(directoryUserIds);

  const applyLink = useCallback(
    (next: SellerPortfoliosDeepLink) => {
      setLink(next);
      replaceSellerPortfoliosSearch(basePath, next);
    },
    [basePath],
  );

  const openPortfolio = useCallback(
    (portfolio: SellerPortfolio, listState: SellerPortfoliosDeepLink = link) => {
      const target = buildSellerPortfolioDetailPath(basePath, portfolio.id, listState);
      if (!target) return;
      navigatePluginPath(target);
    },
    [basePath, link],
  );

  useEffect(() => {
    if (typeof window === "undefined") return;
    const syncFromLocation = () => {
      const migrated = migrateLegacySellerPortfolioIdParam(
        window.location.pathname,
        window.location.search,
        basePath,
      );
      if (migrated) {
        navigatePluginPath(migrated, { replace: true });
        return;
      }
      const parsed = parseSellerPortfoliosRouteState(
        window.location.pathname,
        window.location.search,
        basePath,
      );
      if (!parsed) return;
      setLink(parsed);
      replaceSellerPortfoliosSearch(basePath, parsed);
    };
    syncFromLocation();
    window.addEventListener("popstate", syncFromLocation);
    return () => window.removeEventListener("popstate", syncFromLocation);
  }, [basePath]);

  const reload = useCallback(
    (options?: { silent?: boolean }) => {
      if (options?.silent) setRefreshing(true);
      else setLoading(true);
      setError(null);
      Promise.all([
        listSellerPortfolios(),
        getSellerPortfoliosCoverageAudit(),
        getSellerPortfoliosLoadSummary(),
      ])
        .then(([response, audit, load]) => {
          setPortfolios(response);
          setCoverageAudit(audit);
          setLoadSummary(load);
          setLastSuccessAt(new Date());
        })
        .catch((err: unknown) => {
          const message = err instanceof Error ? err.message : "Erro ao listar carteiras.";
          setError(message);
          notifyError(message);
          if (!options?.silent) {
            setPortfolios([]);
            setCoverageAudit(null);
            setLoadSummary(null);
          }
        })
        .finally(() => {
          setLoading(false);
          setRefreshing(false);
        });
    },
    [notifyError],
  );

  useEffect(() => {
    reload();
  }, [reload]);

  useCommercialPortfolioSync(() => {
    reload({ silent: true });
  });

  const overlapIds = useMemo(
    () => overlappingPortfolioIdSet(coverageAudit),
    [coverageAudit],
  );

  const loadByPortfolioId = useMemo(
    () => portfolioLoadById(loadSummary),
    [loadSummary],
  );

  const loadByPersonId = useMemo(
    () => personLoadByUserId(loadSummary),
    [loadSummary],
  );

  const stats = useMemo(() => {
    const active = portfolios.filter((item) => item.active).length;
    const inactive = portfolios.length - active;
    const customers = portfolios.reduce((sum, item) => sum + (item.customer_count ?? 0), 0);
    const overlapping = portfolios.filter(
      (item) => item.active && overlapIds.has(item.id),
    ).length;
    const uncoveredCount = coverageAudit?.gap?.available
      ? coverageAudit.gap.uncovered_count ?? 0
      : null;
    return {
      total: portfolios.length,
      active,
      inactive,
      customers,
      overlapping,
      overlappingCustomers: coverageAudit?.overlapping_count ?? 0,
      uncoveredCount,
    };
  }, [coverageAudit?.gap, coverageAudit?.overlapping_count, overlapIds, portfolios]);

  const filteredPortfolios = useMemo(() => {
    if (link.filter === "uncovered") return [];
    return portfolios.filter((item) => {
      if (link.filter === "active" && !item.active) return false;
      if (link.filter === "inactive" && item.active) return false;
      if (link.filter === "overlapping") {
        if (!item.active || !overlapIds.has(item.id)) return false;
      }
      return portfolioMatchesQuery(item, link.q, directoryLabelFor);
    });
  }, [directoryLabelFor, link.filter, link.q, overlapIds, portfolios]);

  const filterChips = (
    [
      ["all", stats.total] as const,
      ["active", stats.active] as const,
      ["inactive", stats.inactive] as const,
      ["overlapping", stats.overlapping] as const,
      [
        "uncovered",
        stats.uncoveredCount ?? 0,
      ] as const,
    ] as const
  ).map(([id, count]) => ({
    id,
    label: `${FILTER_META[id].label} (${count})`,
    active: link.filter === id,
    onSelect: () =>
      applyLink({
        ...link,
        filter: id,
        view: id === "uncovered" ? "list" : link.view,
      }),
  }));

  async function handleCreate(input: { userIds: string[]; displayName: string }) {
    setCreating(true);
    setCreateError(null);
    try {
      const created = await createSellerPortfolio({
        user_ids: input.userIds,
        user_id: input.userIds[0],
        display_name: input.displayName,
      });
      notifySuccess("Carteira criada com sucesso.");
      setCreateOpen(false);
      const nextList: SellerPortfoliosDeepLink = { q: "", filter: "all", view: "list", axis: "portfolio" };
      applyLink(nextList);
      openPortfolio(created, nextList);
      reload({ silent: true });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Erro ao criar carteira.";
      setCreateError(message);
      notifyError(message);
    } finally {
      setCreating(false);
    }
  }

  async function handleBulkTransfer(input: {
    sourceId: string;
    targetId: string;
    customerKeys: string[];
    reason: string;
  }) {
    const source = portfolios.find((item) => item.id === input.sourceId);
    if (!source) {
      setBulkError("Carteira de origem não encontrada.");
      notifyError("Carteira de origem não encontrada.");
      return;
    }
    const customers = source.customers
      .filter((customer) =>
        input.customerKeys.includes(customerKey(customer.customer_code, customer.customer_store)),
      )
      .map((customer) => ({
        customer_code: customer.customer_code,
        customer_store: customer.customer_store,
        customer_name: customer.customer_name,
      }));
    setBulkBusy(true);
    setBulkError(null);
    try {
      const result = await transferSellerCustomersBulk({
        source_portfolio_id: input.sourceId,
        target_portfolio_id: input.targetId,
        customers,
        reason_note: input.reason,
      });
      if (result.failed_count > 0) {
        notifySuccess(
          PORTFOLIO_BULK_TRANSFER_CONTENT.successPartial
            .replace("{ok}", String(result.transferred_count))
            .replace("{failed}", String(result.failed_count)),
        );
      } else {
        notifySuccess(
          PORTFOLIO_BULK_TRANSFER_CONTENT.successAll.replace(
            "{count}",
            String(result.transferred_count),
          ),
        );
      }
      setBulkOpen(false);
      reload({ silent: true });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Erro na transferência em massa.";
      setBulkError(message);
      notifyError(message);
    } finally {
      setBulkBusy(false);
    }
  }

  async function handleExportMatrix() {
    if (filteredPortfolios.length === 0) {
      notifyError(PORTFOLIO_LOAD_CONTENT.exportEmpty);
      return;
    }
    setExporting(true);
    try {
      const ok = await exportOrgMatrixExcel(
        filteredPortfolios,
        loadByPortfolioId,
        directoryLabelFor,
      );
      if (!ok) notifyError(PORTFOLIO_LOAD_CONTENT.exportEmpty);
      else notifySuccess("Matriz exportada.");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Erro ao exportar matriz.";
      notifyError(message);
    } finally {
      setExporting(false);
    }
  }

  const emptyTitle =
    stats.total === 0
      ? "Nenhuma carteira cadastrada"
      : `Nenhuma em ${FILTER_META[link.filter].label.toLowerCase()}`;
  const emptyMessage = FILTER_META[link.filter].emptyHint;

  return (
    <section className="cm-page-stack cm-portfolios-page">
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
            label: "Administração",
            href: `${basePath}/administration/seller-portfolios`,
            onNavigate: (event) => event.preventDefault(),
          },
        ]}
        current="Carteiras"
      />

      <CommercialPageHero
        aria-label="Resumo das carteiras"
        eyebrow="Administração"
        title="Carteiras"
        description={
          loading
            ? "Buscando carteiras cadastradas."
            : "Cadastre vendedores, vincule clientes e transfira entre carteiras."
        }
        badge={
          <CommercialStatusBadge
            label={`${stats.active} ativa${stats.active === 1 ? "" : "s"}`}
            variant={stats.total === 0 ? "neutral" : stats.active === 0 ? "warning" : "info"}
          />
        }
        highlights={[
          {
            id: "total",
            label: "Carteiras",
            value: loading ? "—" : stats.total.toLocaleString("pt-BR"),
          },
          {
            id: "active",
            label: "Ativas",
            value: loading ? "—" : stats.active.toLocaleString("pt-BR"),
          },
          {
            id: "inactive",
            label: "Inativas",
            value: loading ? "—" : stats.inactive.toLocaleString("pt-BR"),
          },
          {
            id: "customers",
            label: "Clientes",
            value: loading ? "—" : stats.customers.toLocaleString("pt-BR"),
          },
          {
            id: "overlapping",
            label: PORTFOLIO_COVERAGE_CONTENT.heroOverlapping,
            value: loading ? "—" : stats.overlappingCustomers.toLocaleString("pt-BR"),
          },
          {
            id: "uncovered",
            label: PORTFOLIO_COVERAGE_CONTENT.heroUncovered,
            value:
              loading || stats.uncoveredCount === null
                ? "—"
                : stats.uncoveredCount.toLocaleString("pt-BR"),
          },
        ]}
        actions={
          <div className="cm-portfolios-page__actions">
            <span className="cm-portfolios-page__freshness" aria-live="polite">
              Atualizado em {formatUpdatedAt(lastSuccessAt)}
              {refreshing ? " · Atualizando…" : ""}
            </span>
            <CommercialActionButton variant="primary" onClick={() => setCreateOpen(true)}>
              <Plus size={16} strokeWidth={1.75} aria-hidden="true" />
              Nova carteira
            </CommercialActionButton>
            <HelpTooltip
              content={CM_HELP.sellerPortfolios.bulkTransferWizard}
              ariaLabel={PORTFOLIO_BULK_TRANSFER_CONTENT.openWizardHint}
              wrap
              placement="bottom"
            >
              <CommercialActionButton
                variant="ghost"
                onClick={() => {
                  setBulkError(null);
                  setBulkOpen(true);
                }}
                disabled={loading || portfolios.length === 0}
              >
                <ArrowLeftRight size={16} strokeWidth={1.75} aria-hidden="true" />
                {PORTFOLIO_BULK_TRANSFER_CONTENT.openWizard}
              </CommercialActionButton>
            </HelpTooltip>
            <HelpTooltip
              content={CM_HELP.sellerPortfolios.exportOrgMatrix}
              ariaLabel={PORTFOLIO_LOAD_CONTENT.exportMatrixHint}
              wrap
              placement="bottom"
            >
              <CommercialActionButton
                variant="ghost"
                onClick={() => void handleExportMatrix()}
                disabled={loading || exporting || filteredPortfolios.length === 0}
                aria-busy={exporting}
              >
                <Download size={16} strokeWidth={1.75} aria-hidden="true" />
                {exporting ? "Exportando…" : PORTFOLIO_LOAD_CONTENT.exportMatrixButton}
              </CommercialActionButton>
            </HelpTooltip>
            <CommercialActionButton
              variant="ghost"
              onClick={() => reload({ silent: true })}
              disabled={loading || refreshing}
              aria-busy={refreshing || loading}
            >
              <RefreshCw
                size={16}
                aria-hidden="true"
                className={refreshing ? "cm-spin" : undefined}
              />
              {refreshing || loading ? "Atualizando…" : "Atualizar"}
            </CommercialActionButton>
          </div>
        }
      >
        <div className="cm-portfolios-page__view-toggle">
          <HelpTooltip
            content={CM_HELP.sellerPortfolios.shellViewToggle}
            ariaLabel="Ajuda: Lista ou Organização"
            wrap
            placement="bottom"
          >
            <SegmentToggle
              prefix={UI_PREFIX}
              size="sm"
              ariaLabel="Modo Lista ou Organização"
              idPrefix="seller-portfolios-shell-view"
              value={link.view}
              onChange={(next) =>
                applyLink({ ...link, view: next as SellerPortfoliosView })
              }
              options={[
                { value: "list", label: "Lista" },
                { value: "org", label: "Organização" },
              ]}
            />
          </HelpTooltip>
        </div>
        <CommercialScopeChipBar
          label={
            <CommercialSectionHintLabel
              label="Situação"
              hint={CM_HELP.sellerPortfolios.filter}
            />
          }
          aria-label="Filtro de carteiras"
          chips={filterChips}
        />
        <CommercialFilterBarShell embedded ariaLabel="Busca de carteiras">
          <CommercialTextField
            label="Buscar vendedor, usuário ou e-mail"
            hint={CM_HELP.sellerPortfolios.list}
            type="search"
            value={link.q}
            onChange={(q) => applyLink({ ...link, q })}
            placeholder="Nome, usuário ou e-mail"
          />
        </CommercialFilterBarShell>
      </CommercialPageHero>

      {error ? (
        <CommercialStateBanner variant="error">
          <p>{error}</p>
          <CommercialActionButton variant="ghost" onClick={() => reload()}>
            Tentar novamente
          </CommercialActionButton>
        </CommercialStateBanner>
      ) : null}

      {link.filter === "uncovered" ? (
        <UncoveredCustomersPanel
          items={coverageAudit?.gap?.uncovered ?? []}
          uncoveredCount={coverageAudit?.gap?.uncovered_count ?? 0}
          available={Boolean(coverageAudit?.gap?.available)}
          loading={loading && !coverageAudit}
        />
      ) : link.view === "org" ? (
        <SellerPortfoliosOrgView
          portfolios={filteredPortfolios}
          axis={link.axis}
          loading={loading && portfolios.length === 0}
          emptyTitle={emptyTitle}
          emptyMessage={emptyMessage}
          loadByPortfolioId={loadByPortfolioId}
          loadByPersonId={loadByPersonId}
          onAxisChange={(axis: SellerPortfoliosAxis) => applyLink({ ...link, axis })}
          onOpenPortfolio={(portfolio) => openPortfolio(portfolio)}
          onCreate={() => setCreateOpen(true)}
          directoryLabelFor={directoryLabelFor}
        />
      ) : (
        <SellerPortfoliosList
          portfolios={filteredPortfolios}
          overlappingPortfolioIds={overlapIds}
          loadByPortfolioId={loadByPortfolioId}
          loading={loading && portfolios.length === 0}
          emptyTitle={emptyTitle}
          emptyMessage={emptyMessage}
          onSelect={(portfolio) => openPortfolio(portfolio)}
          onCreate={() => setCreateOpen(true)}
          directoryLabelFor={directoryLabelFor}
        />
      )}

      <SellerPortfolioCreateDialog
        open={createOpen}
        busy={creating}
        error={createError}
        onClose={() => {
          if (creating) return;
          setCreateOpen(false);
          setCreateError(null);
        }}
        onCreate={(input) => void handleCreate(input)}
      />

      <SellerPortfolioBulkTransferWizard
        open={bulkOpen}
        busy={bulkBusy}
        error={bulkError}
        portfolios={portfolios}
        onClose={() => {
          if (bulkBusy) return;
          setBulkOpen(false);
          setBulkError(null);
        }}
        onTransfer={(input) => void handleBulkTransfer(input)}
      />
    </section>
  );
}
