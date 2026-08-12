import { useCallback, useEffect, useMemo, useState } from "react";

import {
  addSellerCustomer,
  addSellerPortfolioMember,
  deactivateSellerPortfolio,
  getSellerPortfolio,
  getSellerPortfoliosCoverageAudit,
  listSellerPortfolioAudit,
  listSellerPortfolios,
  purgeSellerPortfolio,
  removeSellerCustomer,
  removeSellerPortfolioMember,
  setSellerPortfolioOwner,
  transferSellerCustomersBulk,
  updateSellerPortfolio,
} from "../../api/commercialPortfolioApi";
import { useCommercialConfirm } from "../../app/CommercialConfirmDialogProvider";
import {
  useCommercialFloatingNotice,
  FORM_VALIDATION_AUTO_DISMISS_MS,
} from "../../app/CommercialFloatingNoticeProvider";
import { useCommercialPortfolioSync } from "../../app/CommercialRealtimeProvider";
import { navigatePluginPath, navigatePluginView } from "../../app/pluginNavigation";
import { useDirectoryUserLabels } from "../../app/useDirectoryUserLabels";
import { usePortfolioScope } from "../../app/usePortfolioScope";
import {
  CommercialActionButton,
  CommercialLoadingCard,
  CommercialPageHero,
  CommercialPagePath,
  CommercialStateBanner,
} from "../../app/commercialUi";
import { PORTFOLIO_COVERAGE_CONTENT } from "../../content/portfolioCoverageContent";
import { customerKey } from "../../shared/format";
import type {
  SellerPortfolio,
  SellerPortfolioAuditEvent,
  SellerPortfoliosCoverageAudit,
  TotvsCustomerHit,
} from "../../types/portfolio";
import {
  overlappingCustomerKeySetForPortfolio,
  readCoverageLinkWarning,
  stripPortfolioCoverageFields,
} from "../../utils/portfolioCoverage";
import {
  buildSellerPortfoliosPath,
  parseSellerPortfoliosDeepLink,
  type SellerPortfoliosDeepLink,
} from "../../utils/sellerPortfoliosDeepLink";
import { SellerPortfolioAuditTimeline } from "./SellerPortfolioAuditTimeline";
import { SellerPortfolioBulkTransferWizard } from "./SellerPortfolioBulkTransferWizard";
import { SellerPortfolioDetail } from "./SellerPortfolioDetail";
import { PORTFOLIO_BULK_TRANSFER_CONTENT } from "../../content/portfolioBulkTransferContent";

type SellerPortfolioDetailPageProps = {
  basePath: string;
  portfolioId: string;
  search?: string;
};

function isNotFoundError(message: string): boolean {
  return /404|não encontrad/i.test(message);
}

export function SellerPortfolioDetailPage({
  basePath,
  portfolioId,
  search,
}: SellerPortfolioDetailPageProps) {
  const { notifyError, notifySuccess, notifyWarning, notifyMissingRequired } =
    useCommercialFloatingNotice();
  const { reloadScope } = usePortfolioScope();
  const confirm = useCommercialConfirm();
  const listState = useMemo(
    () => parseSellerPortfoliosDeepLink(search ?? (typeof window !== "undefined" ? window.location.search : "")),
    [search],
  );
  const listHref = useMemo(
    () => buildSellerPortfoliosPath(basePath, listState),
    [basePath, listState],
  );

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [portfolio, setPortfolio] = useState<SellerPortfolio | null>(null);
  const [allPortfolios, setAllPortfolios] = useState<SellerPortfolio[]>([]);
  const [coverageAudit, setCoverageAudit] = useState<SellerPortfoliosCoverageAudit | null>(null);
  const [auditEvents, setAuditEvents] = useState<SellerPortfolioAuditEvent[]>([]);
  const [auditLoading, setAuditLoading] = useState(true);
  const [auditError, setAuditError] = useState<string | null>(null);
  const [savingName, setSavingName] = useState(false);
  const [busyCustomerKey, setBusyCustomerKey] = useState<string | null>(null);
  const [busyMemberUserId, setBusyMemberUserId] = useState<string | null>(null);
  const [transferOpen, setTransferOpen] = useState(false);
  const [transferring, setTransferring] = useState(false);
  const [transferError, setTransferError] = useState<string | null>(null);

  const directoryUserIds = useMemo(() => {
    if (!portfolio) return [];
    const ids = new Set<string>();
    const owner = (portfolio.owner_user_id ?? portfolio.user_id).trim();
    if (owner) ids.add(owner);
    for (const member of portfolio.members ?? []) {
      if (member.user_id.trim()) ids.add(member.user_id.trim());
    }
    for (const event of auditEvents) {
      const actor = event.actor_user_id?.trim();
      if (actor) ids.add(actor);
      const payloadUser = typeof event.payload?.user_id === "string" ? event.payload.user_id.trim() : "";
      if (payloadUser) ids.add(payloadUser);
    }
    return [...ids];
  }, [auditEvents, portfolio]);
  const { labelFor: directoryLabelFor } = useDirectoryUserLabels(directoryUserIds);

  const goToList = useCallback(
    (nextList?: SellerPortfoliosDeepLink) => {
      navigatePluginPath(buildSellerPortfoliosPath(basePath, nextList ?? listState));
    },
    [basePath, listState],
  );

  const reloadAudit = useCallback(
    (options?: { signal?: AbortSignal }) => {
      setAuditLoading(true);
      setAuditError(null);
      listSellerPortfolioAudit(portfolioId, { page: 1, pageSize: 50, signal: options?.signal })
        .then((page) => {
          if (options?.signal?.aborted) return;
          setAuditEvents(page.items);
        })
        .catch((err: unknown) => {
          if (options?.signal?.aborted) return;
          setAuditError(err instanceof Error ? err.message : "Erro ao carregar histórico.");
        })
        .finally(() => {
          if (!options?.signal?.aborted) setAuditLoading(false);
        });
    },
    [portfolioId],
  );

  const reload = useCallback(
    (options?: { silent?: boolean; signal?: AbortSignal }) => {
      if (!options?.silent) setLoading(true);
      setError(null);
      setNotFound(false);
      Promise.all([
        getSellerPortfolio(portfolioId, options?.signal),
        listSellerPortfolios({ signal: options?.signal }),
        getSellerPortfoliosCoverageAudit(options?.signal),
      ])
        .then(([detail, items, audit]) => {
          if (options?.signal?.aborted) return;
          setPortfolio(detail);
          setAllPortfolios(items);
          setCoverageAudit(audit);
        })
        .catch((err: unknown) => {
          if (options?.signal?.aborted) return;
          const message = err instanceof Error ? err.message : "Erro ao carregar carteira.";
          if (isNotFoundError(message)) {
            setNotFound(true);
            setPortfolio(null);
            setError(null);
          } else {
            setError(message);
            notifyError(message);
          }
        })
        .finally(() => {
          if (!options?.signal?.aborted) setLoading(false);
        });
    },
    [notifyError, portfolioId],
  );

  useEffect(() => {
    const controller = new AbortController();
    reload({ signal: controller.signal });
    reloadAudit({ signal: controller.signal });
    return () => controller.abort();
  }, [reload, reloadAudit]);

  useCommercialPortfolioSync(
    () => {
      reload({ silent: true });
      reloadAudit();
      reloadScope();
    },
    { portfolioId },
  );

  async function handleSaveName(displayName: string) {
    if (!portfolio) return;
    if (!notifyMissingRequired(displayName ? [] : ["Nome de exibição"])) return;
    setSavingName(true);
    try {
      const updated = await updateSellerPortfolio(portfolio.id, { display_name: displayName });
      setPortfolio(updated);
      notifySuccess("Carteira atualizada com sucesso.");
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Erro ao atualizar carteira.");
    } finally {
      setSavingName(false);
    }
  }

  async function handleDeactivate() {
    if (!portfolio) return;
    const accepted = await confirm({
      title: "Inativar carteira",
      message: `${portfolio.display_name} sai do escopo operacional. Os clientes continuam vinculados.`,
      confirmLabel: "Inativar",
      variant: "default",
    });
    if (!accepted) return;
    try {
      const updated = await deactivateSellerPortfolio(portfolio.id);
      setPortfolio(updated);
      notifySuccess("Carteira desativada com sucesso.");
      reloadAudit();
      reloadScope();
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Erro ao desativar carteira.");
    }
  }

  async function handleReactivate() {
    if (!portfolio) return;
    try {
      const updated = await updateSellerPortfolio(portfolio.id, { active: true });
      setPortfolio(updated);
      notifySuccess("Carteira reativada com sucesso.");
      reloadAudit();
      reloadScope();
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Erro ao reativar carteira.");
    }
  }

  async function handlePurge() {
    if (!portfolio) return;
    const count = portfolio.customer_count;
    const accepted = await confirm({
      title: "Excluir carteira",
      message: `Apaga ${portfolio.display_name} em definitivo. ${count.toLocaleString("pt-BR")} cliente(s) serão desvinculados. O usuário poderá receber uma carteira nova depois.`,
      confirmLabel: "Excluir",
      variant: "danger",
    });
    if (!accepted) return;
    try {
      await purgeSellerPortfolio(portfolio.id);
      notifySuccess("Carteira excluída com sucesso.");
      reloadScope();
      goToList();
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Erro ao excluir carteira.");
    }
  }

  async function handleAddCustomer(hit: TotvsCustomerHit) {
    if (!portfolio) return;
    const key = customerKey(hit.code, hit.store);
    setBusyCustomerKey(key);
    try {
      const result = await addSellerCustomer(portfolio.id, {
        customer_code: hit.code,
        customer_store: hit.store,
        customer_name: hit.name,
      });
      setPortfolio(stripPortfolioCoverageFields(result));
      const warning = readCoverageLinkWarning(result);
      if (warning) {
        const others = warning.other_portfolios
          .map((item) => item.display_name.trim() || item.id)
          .filter(Boolean)
          .join(", ");
        notifyWarning(
          others
            ? `${warning.message} Também em: ${others}.`
            : warning.message,
          { title: PORTFOLIO_COVERAGE_CONTENT.linkWarningTitle },
        );
        void getSellerPortfoliosCoverageAudit()
          .then((audit) => setCoverageAudit(audit))
          .catch(() => undefined);
      } else {
        notifySuccess(`Cliente ${hit.name} adicionado à carteira.`);
      }
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Erro ao adicionar cliente.");
    } finally {
      setBusyCustomerKey(null);
    }
  }

  async function handleRemoveCustomer(code: string, store: string) {
    if (!portfolio) return;
    const key = customerKey(code, store);
    setBusyCustomerKey(key);
    try {
      const updated = await removeSellerCustomer(portfolio.id, code, store);
      setPortfolio(updated);
      notifySuccess("Cliente removido da carteira.");
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Erro ao remover cliente.");
    } finally {
      setBusyCustomerKey(null);
    }
  }

  async function handleAddMember(userId: string) {
    if (!portfolio) return;
    setBusyMemberUserId(userId);
    try {
      const updated = await addSellerPortfolioMember(portfolio.id, { user_id: userId });
      setPortfolio(updated);
      notifySuccess("Usuário adicionado à carteira.");
      reloadAudit();
      reloadScope();
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Erro ao adicionar usuário.");
    } finally {
      setBusyMemberUserId(null);
    }
  }

  async function handleRemoveMember(userId: string) {
    if (!portfolio) return;
    setBusyMemberUserId(userId);
    try {
      const updated = await removeSellerPortfolioMember(portfolio.id, userId);
      setPortfolio(updated);
      notifySuccess("Usuário removido da carteira.");
      reloadAudit();
      reloadScope();
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Erro ao remover usuário.");
    } finally {
      setBusyMemberUserId(null);
    }
  }

  async function handleSetOwner(userId: string) {
    if (!portfolio) return;
    setBusyMemberUserId(userId);
    try {
      const updated = await setSellerPortfolioOwner(portfolio.id, userId);
      setPortfolio(updated);
      notifySuccess("Responsável atualizado.");
      reloadAudit();
      reloadScope();
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Erro ao definir responsável.");
    } finally {
      setBusyMemberUserId(null);
    }
  }

  async function handleTransfer(input: {
    sourceId: string;
    targetId: string;
    customerKeys: string[];
    reason: string;
  }) {
    if (!portfolio) return;
    if (portfolio.id !== input.sourceId) {
      setTransferError("Origem inválida para esta carteira.");
      notifyError("Origem inválida para esta carteira.", {
        title: "Transferência inválida",
        autoDismissMs: FORM_VALIDATION_AUTO_DISMISS_MS,
      });
      return;
    }
    if (portfolio.id === input.targetId) {
      setTransferError("Origem e destino devem ser carteiras diferentes.");
      notifyError("Origem e destino devem ser carteiras diferentes.", {
        title: "Transferência inválida",
        autoDismissMs: FORM_VALIDATION_AUTO_DISMISS_MS,
      });
      return;
    }
    const customers = portfolio.customers
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
      const result = await transferSellerCustomersBulk({
        source_portfolio_id: portfolio.id,
        target_portfolio_id: input.targetId,
        customers,
        reason_note: input.reason,
      });
      setPortfolio(result.source);
      setAllPortfolios((current) =>
        current.map((item) => {
          if (item.id === result.source.id) return result.source;
          if (item.id === result.target.id) return result.target;
          return item;
        }),
      );
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
      setTransferOpen(false);
      reloadAudit();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Erro ao transferir clientes.";
      setTransferError(message);
      notifyError(message);
    } finally {
      setTransferring(false);
    }
  }

  const overlappingCustomerKeys = useMemo(
    () =>
      portfolio
        ? overlappingCustomerKeySetForPortfolio(coverageAudit, portfolio.id)
        : new Set<string>(),
    [coverageAudit, portfolio],
  );

  const otherPortfolioLabelsFor = useCallback(
    (code: string, store: string) => {
      if (!portfolio) return [];
      const key = customerKey(code, store);
      return allPortfolios
        .filter((item) => item.active && item.id !== portfolio.id)
        .filter((item) =>
          (item.customers ?? []).some(
            (customer) =>
              customerKey(customer.customer_code, customer.customer_store) === key,
          ),
        )
        .map((item) => item.display_name.trim() || item.id);
    },
    [allPortfolios, portfolio],
  );

  return (
    <section className="cm-page-stack cm-portfolios-page">
      <CommercialPagePath
        back={{
          label: "Carteiras",
          href: listHref,
          onNavigate: (event) => {
            event.preventDefault();
            goToList();
          },
        }}
        items={[
          {
            id: "home",
            label: "Portal Comercial",
            href: basePath,
            onNavigate: (event) => {
              event.preventDefault();
              navigatePluginView("home", { basePath });
            },
          },
          {
            id: "admin",
            label: "Administração",
            href: `${basePath}/administration`,
            onNavigate: (event) => {
              event.preventDefault();
              navigatePluginView("administration", { basePath });
            },
          },
          {
            id: "portfolios",
            label: "Carteiras",
            href: listHref,
            onNavigate: (event) => {
              event.preventDefault();
              goToList();
            },
          },
        ]}
        current={portfolio?.display_name ?? "Detalhe"}
      />

      <CommercialPageHero
        aria-label={portfolio?.display_name ?? "Detalhe da carteira"}
        title={portfolio?.display_name ?? "Detalhe da carteira"}
        description={
          portfolio
            ? `${portfolio.customer_count.toLocaleString("pt-BR")} cliente(s) · ${
                portfolio.active ? "Ativa" : "Inativa"
              }`
            : "Clientes, membros e ações da carteira."
        }
      />

      {loading && !portfolio ? (
        <CommercialLoadingCard title="Carregando carteira…" variant="panel" />
      ) : null}

      {notFound ? (
        <CommercialStateBanner variant="error">
          <p>Carteira não encontrada.</p>
          <CommercialActionButton variant="ghost" onClick={() => goToList()}>
            Voltar à lista
          </CommercialActionButton>
        </CommercialStateBanner>
      ) : null}

      {error ? (
        <CommercialStateBanner variant="error">
          <p>{error}</p>
          <CommercialActionButton variant="ghost" onClick={() => reload()}>
            Tentar novamente
          </CommercialActionButton>
        </CommercialStateBanner>
      ) : null}

      {portfolio ? (
        <>
          <SellerPortfolioDetail
            portfolio={portfolio}
            userLabel={directoryLabelFor(
              portfolio.owner_user_id ?? portfolio.user_id,
              portfolio.display_name,
            )}
            savingName={savingName}
            busyCustomerKey={busyCustomerKey}
            busyMemberUserId={busyMemberUserId}
            overlappingCustomerKeys={overlappingCustomerKeys}
            otherPortfolioLabelsFor={otherPortfolioLabelsFor}
            directoryLabelFor={directoryLabelFor}
            onSaveName={(name) => void handleSaveName(name)}
            onAddCustomer={(hit) => void handleAddCustomer(hit)}
            onRemoveCustomer={(code, store) => void handleRemoveCustomer(code, store)}
            onAddMember={(userId) => void handleAddMember(userId)}
            onRemoveMember={(userId) => void handleRemoveMember(userId)}
            onSetOwner={(userId) => void handleSetOwner(userId)}
            onDeactivate={() => void handleDeactivate()}
            onReactivate={() => void handleReactivate()}
            onPurge={() => void handlePurge()}
            onTransfer={() => {
              setTransferError(null);
              setTransferOpen(true);
            }}
          />
          <SellerPortfolioAuditTimeline
            loading={auditLoading}
            error={auditError}
            events={auditEvents}
            directoryLabelFor={directoryLabelFor}
            onRetry={() => reloadAudit()}
          />
        </>
      ) : null}

      <SellerPortfolioBulkTransferWizard
        open={transferOpen}
        busy={transferring}
        error={transferError}
        portfolios={allPortfolios}
        initialSourceId={portfolio?.id ?? null}
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
