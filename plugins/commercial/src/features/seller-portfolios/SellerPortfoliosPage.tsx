import { Plus, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  addSellerCustomer,
  createSellerPortfolio,
  deactivateSellerPortfolio,
  getSellerPortfolio,
  listSellerPortfolios,
  purgeSellerPortfolio,
  removeSellerCustomer,
  transferSellerCustomers,
  updateSellerPortfolio,
} from "../../api/commercialPortfolioApi";
import { useCommercialConfirm } from "../../app/CommercialConfirmDialogProvider";
import {
  useCommercialFloatingNotice,
  FORM_VALIDATION_AUTO_DISMISS_MS,
} from "../../app/CommercialFloatingNoticeProvider";
import { navigatePluginView } from "../../app/pluginNavigation";
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
} from "../../app/commercialUi";
import { CM_HELP } from "../../content/helpTooltips";
import { customerKey } from "../../shared/format";
import type { SellerPortfolio, TotvsCustomerHit } from "../../types/portfolio";
import {
  parseSellerPortfoliosRouteState,
  replaceSellerPortfoliosSearch,
  type SellerPortfoliosDeepLink,
  type SellerPortfoliosFilter,
} from "../../utils/sellerPortfoliosDeepLink";
import { SellerPortfolioCreateDialog } from "./SellerPortfolioCreateDialog";
import { SellerPortfolioDetail } from "./SellerPortfolioDetail";
import { SellerPortfoliosList } from "./SellerPortfoliosList";
import { SellerPortfolioTransferDialog } from "./SellerPortfolioTransferDialog";

const FILTER_META: Record<SellerPortfoliosFilter, { label: string; emptyHint: string }> = {
  all: { label: "Todas", emptyHint: "Cadastre a primeira carteira." },
  active: { label: "Ativas", emptyHint: "Nenhuma carteira ativa neste filtro." },
  inactive: { label: "Inativas", emptyHint: "Nenhuma carteira inativa neste filtro." },
};

const DEFAULT_LINK: SellerPortfoliosDeepLink = { q: "", filter: "all", id: null };

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
  const hay = [
    portfolio.display_name,
    portfolio.user_id,
    labelFor(portfolio.user_id, portfolio.display_name),
  ]
    .join(" ")
    .toLowerCase();
  return hay.includes(normalized);
}

export function SellerPortfoliosPage({ basePath }: SellerPortfoliosPageProps) {
  const { notifyError, notifySuccess, notifyMissingRequired } = useCommercialFloatingNotice();
  const confirm = useCommercialConfirm();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [portfolios, setPortfolios] = useState<SellerPortfolio[]>([]);
  const [lastSuccessAt, setLastSuccessAt] = useState<Date | null>(null);
  const [link, setLink] = useState<SellerPortfoliosDeepLink>(DEFAULT_LINK);
  const [createOpen, setCreateOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [transferOpen, setTransferOpen] = useState(false);
  const [transferring, setTransferring] = useState(false);
  const [transferError, setTransferError] = useState<string | null>(null);
  const [savingName, setSavingName] = useState(false);
  const [busyCustomerKey, setBusyCustomerKey] = useState<string | null>(null);

  const directoryUserIds = useMemo(
    () => portfolios.map((item) => item.user_id),
    [portfolios],
  );
  const { labelFor: directoryLabelFor } = useDirectoryUserLabels(directoryUserIds);

  const applyLink = useCallback(
    (next: SellerPortfoliosDeepLink) => {
      setLink(next);
      replaceSellerPortfoliosSearch(basePath, next);
    },
    [basePath],
  );

  useEffect(() => {
    if (typeof window === "undefined") return;
    const syncFromLocation = () => {
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
      listSellerPortfolios()
        .then((response) => {
          setPortfolios(response);
          setLastSuccessAt(new Date());
        })
        .catch((err: unknown) => {
          const message = err instanceof Error ? err.message : "Erro ao listar carteiras.";
          setError(message);
          notifyError(message);
          if (!options?.silent) setPortfolios([]);
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

  useEffect(() => {
    const selectedId = link.id;
    if (!selectedId || loading) return;
    if (portfolios.some((item) => item.id === selectedId)) return;
    const controller = new AbortController();
    getSellerPortfolio(selectedId, controller.signal)
      .then((detail) => {
        if (controller.signal.aborted) return;
        setPortfolios((current) =>
          current.some((item) => item.id === detail.id) ? current : [...current, detail],
        );
      })
      .catch(() => {
        if (controller.signal.aborted) return;
        applyLink({ ...link, id: null });
      });
    return () => controller.abort();
  }, [applyLink, link, loading, portfolios]);

  const stats = useMemo(() => {
    const active = portfolios.filter((item) => item.active).length;
    const inactive = portfolios.length - active;
    const customers = portfolios.reduce((sum, item) => sum + (item.customer_count ?? 0), 0);
    return { total: portfolios.length, active, inactive, customers };
  }, [portfolios]);

  const filteredPortfolios = useMemo(() => {
    return portfolios.filter((item) => {
      if (link.filter === "active" && !item.active) return false;
      if (link.filter === "inactive" && item.active) return false;
      return portfolioMatchesQuery(item, link.q, directoryLabelFor);
    });
  }, [directoryLabelFor, link.filter, link.q, portfolios]);

  const selectedPortfolio =
    portfolios.find((item) => item.id === link.id) ??
    filteredPortfolios.find((item) => item.id === link.id) ??
    null;

  const filterChips = (
    [
      ["all", stats.total] as const,
      ["active", stats.active] as const,
      ["inactive", stats.inactive] as const,
    ] as const
  ).map(([id, count]) => ({
    id,
    label: `${FILTER_META[id].label} (${count})`,
    active: link.filter === id,
    onSelect: () => applyLink({ ...link, filter: id }),
  }));

  async function handleCreate(input: { userId: string; displayName: string }) {
    setCreating(true);
    setCreateError(null);
    try {
      const created = await createSellerPortfolio({
        user_id: input.userId,
        display_name: input.displayName,
      });
      notifySuccess("Carteira criada com sucesso.");
      setCreateOpen(false);
      applyLink({ q: "", filter: "all", id: created.id });
      reload({ silent: true });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Erro ao criar carteira.";
      setCreateError(message);
      notifyError(message);
    } finally {
      setCreating(false);
    }
  }

  async function handleSaveName(displayName: string) {
    if (!selectedPortfolio) return;
    if (!notifyMissingRequired(displayName ? [] : ["Nome de exibição"])) return;
    setSavingName(true);
    try {
      await updateSellerPortfolio(selectedPortfolio.id, { display_name: displayName });
      notifySuccess("Carteira atualizada com sucesso.");
      reload({ silent: true });
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Erro ao atualizar carteira.");
    } finally {
      setSavingName(false);
    }
  }

  async function handleDeactivate() {
    if (!selectedPortfolio) return;
    const accepted = await confirm({
      title: "Inativar carteira",
      message: `${selectedPortfolio.display_name} sai do escopo operacional. Os clientes continuam vinculados.`,
      confirmLabel: "Inativar",
      variant: "default",
    });
    if (!accepted) return;
    try {
      await deactivateSellerPortfolio(selectedPortfolio.id);
      notifySuccess("Carteira desativada com sucesso.");
      reload({ silent: true });
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Erro ao desativar carteira.");
    }
  }

  async function handleReactivate() {
    if (!selectedPortfolio) return;
    try {
      await updateSellerPortfolio(selectedPortfolio.id, { active: true });
      notifySuccess("Carteira reativada com sucesso.");
      reload({ silent: true });
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Erro ao reativar carteira.");
    }
  }

  async function handlePurge() {
    if (!selectedPortfolio) return;
    const count = selectedPortfolio.customer_count;
    const accepted = await confirm({
      title: "Excluir carteira",
      message: `Apaga ${selectedPortfolio.display_name} em definitivo. ${count.toLocaleString("pt-BR")} cliente(s) serão desvinculados. O usuário poderá receber uma carteira nova depois.`,
      confirmLabel: "Excluir",
      variant: "danger",
    });
    if (!accepted) return;
    try {
      await purgeSellerPortfolio(selectedPortfolio.id);
      notifySuccess("Carteira excluída com sucesso.");
      applyLink({ ...link, id: null });
      reload({ silent: true });
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Erro ao excluir carteira.");
    }
  }

  async function handleAddCustomer(hit: TotvsCustomerHit) {
    if (!selectedPortfolio) return;
    const key = customerKey(hit.code, hit.store);
    setBusyCustomerKey(key);
    try {
      const updated = await addSellerCustomer(selectedPortfolio.id, {
        customer_code: hit.code,
        customer_store: hit.store,
        customer_name: hit.name,
      });
      setPortfolios((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      );
      notifySuccess(`Cliente ${hit.name} adicionado à carteira.`);
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Erro ao adicionar cliente.");
    } finally {
      setBusyCustomerKey(null);
    }
  }

  async function handleRemoveCustomer(code: string, store: string) {
    if (!selectedPortfolio) return;
    const key = customerKey(code, store);
    setBusyCustomerKey(key);
    try {
      const updated = await removeSellerCustomer(selectedPortfolio.id, code, store);
      setPortfolios((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      );
      notifySuccess("Cliente removido da carteira.");
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Erro ao remover cliente.");
    } finally {
      setBusyCustomerKey(null);
    }
  }

  async function handleTransfer(input: {
    targetId: string;
    customerKeys: string[];
    reason: string;
  }) {
    if (!selectedPortfolio) return;
    if (selectedPortfolio.id === input.targetId) {
      setTransferError("Origem e destino devem ser carteiras diferentes.");
      notifyError("Origem e destino devem ser carteiras diferentes.", {
        title: "Transferência inválida",
        autoDismissMs: FORM_VALIDATION_AUTO_DISMISS_MS,
      });
      return;
    }
    const customers = selectedPortfolio.customers
      .filter((customer) =>
        input.customerKeys.includes(customerKey(customer.customer_code, customer.customer_store)),
      )
      .map((customer) => ({
        customer_code: customer.customer_code,
        customer_store: customer.customer_store,
        customer_name: customer.customer_name,
      }));
    setTransferring(true);
    setTransferError(null);
    try {
      const result = await transferSellerCustomers({
        source_portfolio_id: selectedPortfolio.id,
        target_portfolio_id: input.targetId,
        customers,
        reason_note: input.reason,
      });
      notifySuccess(`Transferência concluída: ${result.transferred_count} cliente(s) movido(s).`);
      setTransferOpen(false);
      reload({ silent: true });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Erro ao transferir clientes.";
      setTransferError(message);
      notifyError(message);
    } finally {
      setTransferring(false);
    }
  }

  const emptyTitle =
    stats.total === 0
      ? "Nenhuma carteira cadastrada"
      : `Nenhuma em ${FILTER_META[link.filter].label.toLowerCase()}`;
  const emptyMessage =
    stats.total === 0 || link.filter === "all"
      ? FILTER_META[link.filter].emptyHint
      : FILTER_META[link.filter].emptyHint;

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
            href: `${basePath}/seller-portfolios`,
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

      <div className="cm-portfolios-layout">
        <SellerPortfoliosList
          portfolios={filteredPortfolios}
          selectedId={link.id}
          loading={loading && portfolios.length === 0}
          emptyTitle={emptyTitle}
          emptyMessage={emptyMessage}
          onSelect={(portfolio) => applyLink({ ...link, id: portfolio.id })}
          onCreate={() => setCreateOpen(true)}
          directoryLabelFor={directoryLabelFor}
        />
        <SellerPortfolioDetail
          portfolio={selectedPortfolio}
          userLabel={
            selectedPortfolio
              ? directoryLabelFor(selectedPortfolio.user_id, selectedPortfolio.display_name)
              : ""
          }
          savingName={savingName}
          busyCustomerKey={busyCustomerKey}
          onSaveName={handleSaveName}
          onAddCustomer={handleAddCustomer}
          onRemoveCustomer={handleRemoveCustomer}
          onDeactivate={() => void handleDeactivate()}
          onReactivate={() => void handleReactivate()}
          onPurge={() => void handlePurge()}
          onTransfer={() => {
            setTransferError(null);
            setTransferOpen(true);
          }}
        />
      </div>

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
      <SellerPortfolioTransferDialog
        open={transferOpen}
        busy={transferring}
        error={transferError}
        source={selectedPortfolio}
        portfolios={portfolios}
        onClose={() => {
          if (transferring) return;
          setTransferOpen(false);
          setTransferError(null);
        }}
        onTransfer={(input) => void handleTransfer(input)}
      />
    </section>
  );
}
