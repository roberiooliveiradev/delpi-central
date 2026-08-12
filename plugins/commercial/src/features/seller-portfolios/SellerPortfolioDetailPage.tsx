import { useCallback, useEffect, useMemo, useState } from "react";

import {
  addSellerCustomer,
  addSellerPortfolioMember,
  deactivateSellerPortfolio,
  getSellerPortfolio,
  getSellerPortfoliosCoverageAudit,
  listSellerPortfolios,
  purgeSellerPortfolio,
  removeSellerCustomer,
  removeSellerPortfolioMember,
  setSellerPortfolioOwner,
  transferSellerCustomers,
  updateSellerPortfolio,
} from "../../api/commercialPortfolioApi";
import { useCommercialConfirm } from "../../app/CommercialConfirmDialogProvider";
import {
  useCommercialFloatingNotice,
  FORM_VALIDATION_AUTO_DISMISS_MS,
} from "../../app/CommercialFloatingNoticeProvider";
import { navigatePluginPath, navigatePluginView } from "../../app/pluginNavigation";
import { useDirectoryUserLabels } from "../../app/useDirectoryUserLabels";
import {
  CommercialActionButton,
  CommercialLoadingCard,
  CommercialPagePath,
  CommercialStateBanner,
} from "../../app/commercialUi";
import { PORTFOLIO_COVERAGE_CONTENT } from "../../content/portfolioCoverageContent";
import { customerKey } from "../../shared/format";
import type {
  SellerPortfolio,
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
import { SellerPortfolioDetail } from "./SellerPortfolioDetail";
import { SellerPortfolioTransferDialog } from "./SellerPortfolioTransferDialog";

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
    return [...ids];
  }, [portfolio]);
  const { labelFor: directoryLabelFor } = useDirectoryUserLabels(directoryUserIds);

  const goToList = useCallback(
    (nextList?: SellerPortfoliosDeepLink) => {
      navigatePluginPath(buildSellerPortfoliosPath(basePath, nextList ?? listState));
    },
    [basePath, listState],
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
    return () => controller.abort();
  }, [reload]);

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
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Erro ao definir responsável.");
    } finally {
      setBusyMemberUserId(null);
    }
  }

  async function handleTransfer(input: {
    targetId: string;
    customerKeys: string[];
    reason: string;
  }) {
    if (!portfolio) return;
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
      const result = await transferSellerCustomers({
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
      notifySuccess(`Transferência concluída: ${result.transferred_count} cliente(s) movido(s).`);
      setTransferOpen(false);
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
      ) : null}

      <SellerPortfolioTransferDialog
        open={transferOpen}
        busy={transferring}
        error={transferError}
        source={portfolio}
        portfolios={allPortfolios}
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
