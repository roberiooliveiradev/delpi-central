import { useEffect, useMemo, useRef, useState } from "react";
import { Plus, Search, Trash2, X } from "lucide-react";
import {
  ActionButton,
  DataTable,
  EmptyState,
  SectionCard,
  StatusBadge,
  UserDirectoryPicker,
  type DataTableColumn,
  type DirectoryUserOption,
} from "@delpi/plugin-ui/index";

import {
  addSellerCustomer,
  createSellerPortfolio,
  deactivateSellerPortfolio,
  listSellerPortfolios,
  removeSellerCustomer,
  searchActiveCustomers,
  searchDirectoryUsers,
  transferSellerCustomers,
  updateSellerPortfolio,
} from "../../api/commercialPortfolioApi";
import { useCommercialFloatingNotice, FORM_VALIDATION_AUTO_DISMISS_MS } from "../../app/CommercialFloatingNoticeProvider";
import { useDirectoryUserLabels } from "../../app/useDirectoryUserLabels";
import { CM_HELP } from "../../content/helpTooltips";
import {
  CommercialLoadingCard,
  CommercialMultiSelectField,
  CommercialPageHero,
  CommercialScopeChipBar,
  CommercialSelectField,
  CommercialTextAreaField,
  CommercialTextField,
  CommercialTitleWithHelp,
  CommercialViewTransition,
  cmDataTableClassNames,
  cmDataTableLabels,
  cmEmptyStateClassNames,
  cmSectionCardClassNames,
  cmSectionLabels,
  cmStatusBadgeClassNames,
} from "../../app/commercialUi";
import type { SellerPortfolio, TotvsCustomerHit } from "../../types/portfolio";
import { customerKey } from "../../shared/format";

type PortfolioFilter = "all" | "active" | "inactive";

const FILTER_META: Record<PortfolioFilter, { label: string; emptyHint: string }> = {
  all: { label: "Todas", emptyHint: "Cadastre a primeira carteira abaixo." },
  active: { label: "Ativas", emptyHint: "Nenhuma carteira ativa neste filtro." },
  inactive: { label: "Inativas", emptyHint: "Nenhuma carteira inativa neste filtro." },
};

const cmEmptyCompactClassNames = {
  ...cmEmptyStateClassNames,
  root: `${cmEmptyStateClassNames.root} delpi-ui-state-box--compact cm-empty-compact`,
};

function portfolioHeroCopy(stats: {
  total: number;
  active: number;
  inactive: number;
  customers: number;
}) {
  if (stats.total === 0) {
    return {
      title: "Nenhuma carteira ainda",
      description: "Crie a primeira carteira e vincule clientes do TOTVS.",
    };
  }
  if (stats.inactive > 0 && stats.active === 0) {
    return {
      title: "Só carteiras inativas",
      description: "Reative uma carteira ou cadastre um novo vendedor.",
    };
  }
  return {
    title:
      stats.active === 1
        ? "1 carteira ativa"
        : `${stats.active.toLocaleString("pt-BR")} carteiras ativas`,
    description: "Cadastre vendedores, vincule clientes e transfira entre carteiras.",
  };
}

export function SellerPortfoliosPage() {
  const { notifyError, notifySuccess, notifyMissingRequired } = useCommercialFloatingNotice();
  const [loading, setLoading] = useState(true);
  const [portfolios, setPortfolios] = useState<SellerPortfolio[]>([]);
  const [filter, setFilter] = useState<PortfolioFilter>("all");

  const directoryUserIds = useMemo(
    () => portfolios.map((item) => item.user_id),
    [portfolios],
  );
  const { labelFor: directoryLabelFor } = useDirectoryUserLabels(directoryUserIds);

  const [createUser, setCreateUser] = useState<DirectoryUserOption[]>([]);
  const [createDisplayName, setCreateDisplayName] = useState("");
  const [creating, setCreating] = useState(false);
  const [highlightCreateForm, setHighlightCreateForm] = useState(false);
  const createFormRef = useRef<HTMLDivElement | null>(null);

  const [editingPortfolioId, setEditingPortfolioId] = useState<string | null>(null);
  const [editDisplayName, setEditDisplayName] = useState("");
  const [savingEdit, setSavingEdit] = useState(false);
  const [confirmingDeactivateId, setConfirmingDeactivateId] = useState<string | null>(null);

  const [manageDataPortfolioId, setManageDataPortfolioId] = useState("");
  const [customerQuery, setCustomerQuery] = useState("");
  const [linkedFilter, setLinkedFilter] = useState("");
  const [customerHits, setCustomerHits] = useState<TotvsCustomerHit[]>([]);
  const [searchingCustomers, setSearchingCustomers] = useState(false);
  const [customerSearchError, setCustomerSearchError] = useState<string | null>(null);
  const [busyCustomerKey, setBusyCustomerKey] = useState<string | null>(null);

  const [transferSourceId, setTransferSourceId] = useState("");
  const [transferTargetId, setTransferTargetId] = useState("");
  const [transferCustomerKeys, setTransferCustomerKeys] = useState<string[]>([]);
  const [transferReason, setTransferReason] = useState("");
  const [transferring, setTransferring] = useState(false);

  function reload() {
    setLoading(true);
    listSellerPortfolios()
      .then((response) => setPortfolios(response))
      .catch((err: unknown) => {
        notifyError(err instanceof Error ? err.message : "Erro ao listar carteiras.");
        setPortfolios([]);
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- carga inicial
  }, []);

  useEffect(() => {
    const normalized = customerQuery.trim();
    if (normalized.length < 2) {
      setCustomerHits([]);
      setCustomerSearchError(null);
      setSearchingCustomers(false);
      return;
    }
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => {
      setSearchingCustomers(true);
      setCustomerSearchError(null);
      searchActiveCustomers(normalized, { signal: controller.signal })
        .then((result) => {
          if (!controller.signal.aborted) {
            setCustomerHits(result.items);
            setCustomerSearchError(null);
          }
        })
        .catch((err: unknown) => {
          if (controller.signal.aborted) return;
          setCustomerHits([]);
          const message =
            err instanceof Error && err.message.trim()
              ? err.message
              : "Não foi possível buscar clientes no TOTVS.";
          setCustomerSearchError(message);
          notifyError(message, {
            title: "Busca de clientes",
            id: "cm-customer-search-error",
            autoDismissMs: FORM_VALIDATION_AUTO_DISMISS_MS,
          });
        })
        .finally(() => {
          if (!controller.signal.aborted) setSearchingCustomers(false);
        });
    }, 300);
    return () => {
      controller.abort();
      window.clearTimeout(timeoutId);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- notifyError estável o bastante; evita refetch por identidade
  }, [customerQuery]);

  const stats = useMemo(() => {
    const active = portfolios.filter((item) => item.active).length;
    const inactive = portfolios.length - active;
    const customers = portfolios.reduce((sum, item) => sum + (item.customer_count ?? 0), 0);
    return { total: portfolios.length, active, inactive, customers };
  }, [portfolios]);

  const filteredPortfolios = useMemo(() => {
    if (filter === "active") return portfolios.filter((item) => item.active);
    if (filter === "inactive") return portfolios.filter((item) => !item.active);
    return portfolios;
  }, [portfolios, filter]);

  const hero = portfolioHeroCopy(stats);

  function focusCreateForm() {
    setHighlightCreateForm(true);
    createFormRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    window.setTimeout(() => setHighlightCreateForm(false), 2200);
  }

  async function handleCreate() {
    const user = createUser[0];
    if (!notifyMissingRequired(user ? [] : ["Usuário (Minha Delpi)"])) return;

    const displayName =
      createDisplayName.trim() ||
      user.name.trim() ||
      user.email.trim() ||
      "Usuário";

    setCreating(true);
    try {
      await createSellerPortfolio({
        user_id: user.id,
        display_name: displayName,
      });
      setCreateUser([]);
      setCreateDisplayName("");
      notifySuccess("Carteira criada com sucesso.");
      setFilter("all");
      reload();
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Erro ao criar carteira.");
    } finally {
      setCreating(false);
    }
  }

  function startEdit(portfolio: SellerPortfolio) {
    setEditingPortfolioId(portfolio.id);
    setEditDisplayName(portfolio.display_name);
  }

  async function handleSaveEdit() {
    if (!editingPortfolioId) return;
    if (!notifyMissingRequired(editDisplayName.trim() ? [] : ["Nome de exibição"])) return;
    setSavingEdit(true);
    try {
      await updateSellerPortfolio(editingPortfolioId, { display_name: editDisplayName.trim() });
      notifySuccess("Carteira atualizada com sucesso.");
      setEditingPortfolioId(null);
      reload();
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Erro ao atualizar carteira.");
    } finally {
      setSavingEdit(false);
    }
  }

  async function handleToggleActive(portfolio: SellerPortfolio) {
    if (portfolio.active) {
      if (confirmingDeactivateId !== portfolio.id) {
        setConfirmingDeactivateId(portfolio.id);
        return;
      }
      try {
        await deactivateSellerPortfolio(portfolio.id);
        notifySuccess("Carteira desativada com sucesso.");
        reload();
      } catch (err: unknown) {
        notifyError(err instanceof Error ? err.message : "Erro ao desativar carteira.");
      } finally {
        setConfirmingDeactivateId(null);
      }
      return;
    }

    try {
      await updateSellerPortfolio(portfolio.id, { active: true });
      notifySuccess("Carteira reativada com sucesso.");
      reload();
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Erro ao reativar carteira.");
    }
  }

  const manageDataPortfolio = portfolios.find((item) => item.id === manageDataPortfolioId) ?? null;

  const linkedCustomers = useMemo(() => {
    const rows = manageDataPortfolio?.customers ?? [];
    const q = linkedFilter.trim().toLowerCase();
    if (!q) return rows;
    return rows.filter((customer) => {
      const hay = `${customer.customer_code} ${customer.customer_store} ${customer.customer_name ?? ""}`
        .trim()
        .toLowerCase();
      return hay.includes(q);
    });
  }, [linkedFilter, manageDataPortfolio]);

  const customerQueryTrimmed = customerQuery.trim();
  const customerSearchReady = customerQueryTrimmed.length >= 2;

  async function handleAddCustomer(hit: TotvsCustomerHit) {
    if (!manageDataPortfolio) {
      notifyMissingRequired(["Carteira"]);
      return;
    }
    const key = customerKey(hit.code, hit.store);
    setBusyCustomerKey(key);
    try {
      await addSellerCustomer(manageDataPortfolio.id, {
        customer_code: hit.code,
        customer_store: hit.store,
        customer_name: hit.name,
      });
      notifySuccess(`Cliente ${hit.name} adicionado à carteira.`);
      reload();
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Erro ao adicionar cliente.");
    } finally {
      setBusyCustomerKey(null);
    }
  }

  async function handleRemoveCustomer(code: string, store: string) {
    if (!manageDataPortfolio) return;
    const key = customerKey(code, store);
    setBusyCustomerKey(key);
    try {
      await removeSellerCustomer(manageDataPortfolio.id, code, store);
      notifySuccess("Cliente removido da carteira.");
      reload();
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Erro ao remover cliente.");
    } finally {
      setBusyCustomerKey(null);
    }
  }

  const transferSourcePortfolio = portfolios.find((item) => item.id === transferSourceId) ?? null;

  const transferCustomerOptions = useMemo(
    () =>
      (transferSourcePortfolio?.customers ?? []).map((customer) => ({
        value: customerKey(customer.customer_code, customer.customer_store),
        label: `${customer.customer_code}/${customer.customer_store} · ${customer.customer_name?.trim() || "—"}`,
      })),
    [transferSourcePortfolio],
  );

  async function handleTransfer() {
    const missing: string[] = [];
    if (!transferSourceId) missing.push("Carteira de origem");
    if (!transferTargetId) missing.push("Carteira de destino");
    if (transferCustomerKeys.length === 0) missing.push("Clientes");
    if (!transferReason.trim()) missing.push("Motivo");
    if (!notifyMissingRequired(missing)) return;
    if (transferSourceId === transferTargetId) {
      notifyError("Origem e destino devem ser carteiras diferentes.", {
        title: "Transferência inválida",
        autoDismissMs: FORM_VALIDATION_AUTO_DISMISS_MS,
      });
      return;
    }

    const customers = (transferSourcePortfolio?.customers ?? [])
      .filter((customer) =>
        transferCustomerKeys.includes(customerKey(customer.customer_code, customer.customer_store)),
      )
      .map((customer) => ({
        customer_code: customer.customer_code,
        customer_store: customer.customer_store,
        customer_name: customer.customer_name,
      }));

    setTransferring(true);
    try {
      const result = await transferSellerCustomers({
        source_portfolio_id: transferSourceId,
        target_portfolio_id: transferTargetId,
        customers,
        reason_note: transferReason.trim(),
      });
      notifySuccess(`Transferência concluída: ${result.transferred_count} cliente(s) movido(s).`);
      setTransferCustomerKeys([]);
      setTransferReason("");
      reload();
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Erro ao transferir clientes.");
    } finally {
      setTransferring(false);
    }
  }

  const portfolioOptions = useMemo(
    () => portfolios.map((item) => ({ value: item.id, label: item.display_name })),
    [portfolios],
  );

  const filterChips = (
    [
      ["all", stats.total] as const,
      ["active", stats.active] as const,
      ["inactive", stats.inactive] as const,
    ] as const
  ).map(([id, count]) => ({
    id,
    label: `${FILTER_META[id].label} (${count})`,
    active: filter === id,
    onSelect: () => setFilter(id),
  }));

  const columns = useMemo<DataTableColumn<SellerPortfolio>[]>(
    () => [
      {
        key: "display_name",
        header: "Carteira",
        headerHint: CM_HELP.sellerPortfolios.colDisplayName,
        render: (row) => row.display_name,
      },
      {
        key: "user_id",
        header: "Usuário",
        headerHint: CM_HELP.sellerPortfolios.colUserId,
        render: (row) => directoryLabelFor(row.user_id, row.display_name),
      },
      {
        key: "customer_count",
        header: "Clientes",
        headerHint: CM_HELP.sellerPortfolios.colCustomerCount,
        align: "right",
        render: (row) => row.customer_count.toLocaleString("pt-BR"),
      },
      {
        key: "status",
        header: "Status",
        headerHint: CM_HELP.sellerPortfolios.colStatus,
        render: (row) => (
          <StatusBadge
            label={row.active ? "Ativa" : "Inativa"}
            variant={row.active ? "success" : "neutral"}
            classNames={cmStatusBadgeClassNames}
          />
        ),
      },
      {
        key: "actions",
        header: "Ações",
        headerHint: CM_HELP.sellerPortfolios.colActions,
        render: (row) => (
          <div className="cm-row-actions">
            <ActionButton variant="ghost" onClick={() => startEdit(row)}>
              Editar
            </ActionButton>
            <ActionButton
              variant="ghost"
              onClick={() => {
                setManageDataPortfolioId(row.id);
                document
                  .getElementById("cm-manage-customers")
                  ?.scrollIntoView({ behavior: "smooth", block: "start" });
              }}
            >
              Gerenciar clientes
            </ActionButton>
            <ActionButton variant="ghost" onClick={() => handleToggleActive(row)}>
              {row.active
                ? confirmingDeactivateId === row.id
                  ? "Confirmar?"
                  : "Desativar"
                : "Reativar"}
            </ActionButton>
          </div>
        ),
      },
    ],
    [confirmingDeactivateId, directoryLabelFor],
  );

  return (
    <section className="cm-page-stack">
      <CommercialPageHero
        aria-label="Resumo das carteiras"
        eyebrow="Admin"
        title={loading ? "Carregando carteiras…" : hero.title}
        description={
          loading
            ? "Buscando carteiras cadastradas na commercial-api."
            : hero.description
        }
        badge={
          !loading && stats.total === 0 ? (
            <StatusBadge
              classNames={cmStatusBadgeClassNames}
              label="Vazio"
              variant="neutral"
            />
          ) : !loading && stats.inactive > 0 && stats.active === 0 ? (
            <StatusBadge
              classNames={cmStatusBadgeClassNames}
              label="Inativas"
              variant="warning"
            />
          ) : (
            <StatusBadge
              classNames={cmStatusBadgeClassNames}
              label={`${stats.active} ativa${stats.active === 1 ? "" : "s"}`}
              variant="info"
            />
          )
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
      />

      <SectionCard
        title="Carteiras"
        subtitle="Usuário Minha Delpi + nome de exibição no portal."
        hint={CM_HELP.sellerPortfolios.list}
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
        actions={
          <ActionButton variant="ghost" onClick={() => reload()}>
            Atualizar
          </ActionButton>
        }
      >
        <div className="cm-portfolios-toolbar">
          <CommercialScopeChipBar
            label={
              <CommercialTitleWithHelp
                title="Filtro"
                hint={CM_HELP.sellerPortfolios.filter}
              />
            }
            aria-label="Filtro de carteiras"
            chips={filterChips}
          />
        </div>

        {loading ? <CommercialLoadingCard title="Carregando carteiras" variant="panel" /> : null}

        {!loading ? (
          <CommercialViewTransition transitionKey={`filter-${filter}`} tone="panel">
            {filteredPortfolios.length === 0 ? (
              <EmptyState
                classNames={cmEmptyCompactClassNames}
                defaultTitle={
                  stats.total === 0
                    ? "Nenhuma carteira cadastrada"
                    : `Nenhuma em ${FILTER_META[filter].label.toLowerCase()}`
                }
                defaultMessage={FILTER_META[filter].emptyHint}
              >
                {stats.total === 0 || filter === "all" ? (
                  <ActionButton variant="primary" onClick={focusCreateForm}>
                    Criar carteira
                  </ActionButton>
                ) : null}
              </EmptyState>
            ) : (
              <DataTable
                rows={filteredPortfolios}
                columns={columns}
                rowKey={(row: SellerPortfolio) => row.id}
                classNames={cmDataTableClassNames}
                labels={cmDataTableLabels}
                layout="section"
              />
            )}
          </CommercialViewTransition>
        ) : null}
      </SectionCard>

      <div
        ref={createFormRef}
        className={
          highlightCreateForm
            ? "cm-portfolios-create cm-portfolios-create--focus"
            : "cm-portfolios-create"
        }
      >
        <SectionCard
          title="Nova carteira"
          subtitle="Vincule um usuário do diretório e defina o nome no seletor de escopo."
          hint={CM_HELP.sellerPortfolios.create}
          classNames={cmSectionCardClassNames}
          labels={cmSectionLabels}
        >
          <div className="cm-portfolios-form">
            <div className="cm-portfolios-form__user">
              <UserDirectoryPicker
                value={createUser}
                onChange={(users) => {
                  setCreateUser(users);
                  const next = users[0];
                  if (next && !createDisplayName.trim()) {
                    const fallback = next.name.trim() || next.email.trim();
                    if (fallback) setCreateDisplayName(fallback);
                  }
                  if (users.length === 0) setCreateDisplayName("");
                }}
                searchUsers={searchDirectoryUsers}
                maxSelected={1}
                labels={{
                  title: "Usuário (Minha Delpi)",
                  hint: CM_HELP.sellerPortfolios.directoryUser,
                  placeholder: "Buscar usuário…",
                }}
              />
            </div>
            <div className="cm-portfolios-form__display-name">
              <CommercialTextField
                label="Nome de exibição"
                hint={CM_HELP.sellerPortfolios.displayName}
                value={createDisplayName}
                onChange={setCreateDisplayName}
                placeholder="Ex.: João Silva (padrão = nome do usuário)"
              />
            </div>
            <div className="cm-portfolios-form__actions">
              <ActionButton variant="primary" onClick={handleCreate} disabled={creating}>
                <Plus size={16} strokeWidth={1.75} aria-hidden="true" />
                {creating ? "Salvando…" : "Criar carteira"}
              </ActionButton>
            </div>
          </div>
        </SectionCard>
      </div>

      {editingPortfolioId ? (
        <SectionCard
          title="Editar carteira"
          hint={CM_HELP.sellerPortfolios.edit}
          classNames={cmSectionCardClassNames}
          labels={cmSectionLabels}
        >
          <div className="cm-portfolios-form">
            <div className="cm-portfolios-form__user">
              <CommercialTextField
                label="Nome de exibição"
                hint={CM_HELP.sellerPortfolios.displayName}
                value={editDisplayName}
                onChange={setEditDisplayName}
                required
              />
            </div>
            <div className="cm-portfolios-form__actions cm-row-actions">
              <ActionButton variant="primary" onClick={handleSaveEdit} disabled={savingEdit}>
                {savingEdit ? "Salvando…" : "Salvar"}
              </ActionButton>
              <ActionButton variant="ghost" onClick={() => setEditingPortfolioId(null)}>
                Cancelar
              </ActionButton>
            </div>
          </div>
        </SectionCard>
      ) : null}

      <div id="cm-manage-customers">
      <SectionCard
        title="Gerenciar clientes"
        subtitle="Escolha a carteira, busque no TOTVS e vincule — ou remova quem já está na lista."
        hint={CM_HELP.sellerPortfolios.customers}
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        <div className="cm-manage-customers-toolbar">
          <CommercialSelectField
            label="Carteira"
            hint={CM_HELP.sellerPortfolios.managePortfolio}
            value={manageDataPortfolioId}
            onChange={(value) => {
              setManageDataPortfolioId(value);
              setCustomerQuery("");
              setCustomerHits([]);
              setCustomerSearchError(null);
              setLinkedFilter("");
            }}
            options={portfolioOptions}
            allowEmpty
            emptyLabel="Selecione uma carteira"
            searchable
          />
          {manageDataPortfolio ? (
            <StatusBadge
              classNames={cmStatusBadgeClassNames}
              label={`${manageDataPortfolio.customers.length} vinculado${
                manageDataPortfolio.customers.length === 1 ? "" : "s"
              }`}
              variant={manageDataPortfolio.customers.length > 0 ? "info" : "neutral"}
            />
          ) : null}
        </div>

        <CommercialViewTransition
          transitionKey={manageDataPortfolioId || "none"}
          tone="panel"
        >
          {!manageDataPortfolio ? (
            <EmptyState
              classNames={cmEmptyCompactClassNames}
              defaultTitle="Selecione uma carteira"
              defaultMessage="Escolha acima ou use Gerenciar clientes na lista."
            />
          ) : (
            <div className="cm-manage-customers-grid">
              <section
                className="cm-manage-panel cm-manage-panel--search"
                aria-label="Buscar e adicionar clientes"
              >
                <header className="cm-manage-panel__header">
                  <CommercialTitleWithHelp
                    title="Buscar e adicionar"
                    hint={CM_HELP.sellerPortfolios.searchCustomers}
                  />
                  <p className="cm-manage-panel__subtitle">
                    Clientes ativos no TOTVS · mínimo 2 caracteres
                  </p>
                </header>

                <div className="cm-manage-search">
                  <div className="cm-manage-search__field">
                    <CommercialTextField
                      label="Buscar no TOTVS"
                      hint={CM_HELP.sellerPortfolios.searchCustomers}
                      value={customerQuery}
                      onChange={setCustomerQuery}
                      placeholder="Código ou nome do cliente"
                    />
                  </div>
                  {customerQuery ? (
                    <ActionButton
                      variant="ghost"
                      onClick={() => {
                        setCustomerQuery("");
                        setCustomerHits([]);
                        setCustomerSearchError(null);
                      }}
                      aria-label="Limpar busca"
                    >
                      <X size={16} strokeWidth={1.75} aria-hidden="true" />
                      Limpar
                    </ActionButton>
                  ) : null}
                </div>

                <div className="cm-manage-panel__body" aria-live="polite">
                  {!customerSearchReady ? (
                    <EmptyState
                      classNames={cmEmptyCompactClassNames}
                      defaultTitle="Digite para buscar"
                      defaultMessage="Informe código ou nome (ao menos 2 caracteres) para listar clientes ativos."
                    >
                      <span className="cm-manage-search-hint" aria-hidden="true">
                        <Search size={18} strokeWidth={1.75} />
                      </span>
                    </EmptyState>
                  ) : searchingCustomers ? (
                    <CommercialLoadingCard title="Buscando no TOTVS…" variant="panel" />
                  ) : customerSearchError ? (
                    <EmptyState
                      classNames={cmEmptyCompactClassNames}
                      defaultTitle="Falha na busca"
                      defaultMessage={customerSearchError}
                      role="alert"
                    />
                  ) : customerHits.length === 0 ? (
                    <EmptyState
                      classNames={cmEmptyCompactClassNames}
                      defaultTitle="Nenhum cliente encontrado"
                      defaultMessage={`Nada para “${customerQueryTrimmed}”. Tente outro código ou nome.`}
                    />
                  ) : (
                    <ul className="cm-customer-chip-list cm-customer-chip-list--manage">
                      {customerHits.map((hit, index) => {
                        const key = customerKey(hit.code, hit.store) || `hit-${index}`;
                        const alreadyLinked = manageDataPortfolio.customers.some(
                          (customer) =>
                            customerKey(customer.customer_code, customer.customer_store) === key,
                        );
                        return (
                          <li key={key}>
                            <div className="cm-customer-chip-list__meta">
                              <strong>
                                {hit.code}/{hit.store}
                              </strong>
                              <span>{hit.name}</span>
                            </div>
                            {alreadyLinked ? (
                              <StatusBadge
                                classNames={cmStatusBadgeClassNames}
                                label="Já vinculado"
                                variant="success"
                              />
                            ) : (
                              <ActionButton
                                variant="primary"
                                disabled={busyCustomerKey === key}
                                onClick={() => handleAddCustomer(hit)}
                              >
                                <Plus size={14} strokeWidth={1.75} aria-hidden="true" />
                                {busyCustomerKey === key ? "Adicionando…" : "Adicionar"}
                              </ActionButton>
                            )}
                          </li>
                        );
                      })}
                    </ul>
                  )}
                </div>
              </section>

              <section
                className="cm-manage-panel cm-manage-panel--linked"
                aria-label="Clientes vinculados"
              >
                <header className="cm-manage-panel__header">
                  <CommercialTitleWithHelp
                    title={`Na carteira (${manageDataPortfolio.customers.length})`}
                    hint={CM_HELP.sellerPortfolios.customers}
                  />
                  <p className="cm-manage-panel__subtitle">
                    {manageDataPortfolio.display_name}
                  </p>
                </header>

                {manageDataPortfolio.customers.length > 5 ? (
                  <div className="cm-manage-search">
                    <div className="cm-manage-search__field">
                      <CommercialTextField
                        label="Filtrar vinculados"
                        value={linkedFilter}
                        onChange={setLinkedFilter}
                        placeholder="Filtrar por código ou nome"
                      />
                    </div>
                  </div>
                ) : null}

                <div className="cm-manage-panel__body">
                  {manageDataPortfolio.customers.length === 0 ? (
                    <EmptyState
                      classNames={cmEmptyCompactClassNames}
                      defaultTitle="Carteira vazia"
                      defaultMessage="Use a busca ao lado para vincular o primeiro cliente."
                    />
                  ) : linkedCustomers.length === 0 ? (
                    <EmptyState
                      classNames={cmEmptyCompactClassNames}
                      defaultTitle="Nenhum no filtro"
                      defaultMessage="Ajuste o filtro ou limpe o texto."
                    />
                  ) : (
                    <ul className="cm-customer-chip-list cm-customer-chip-list--manage">
                      {linkedCustomers.map((customer, index) => {
                        const key =
                          customerKey(customer.customer_code, customer.customer_store) ||
                          `linked-${index}`;
                        return (
                          <li key={key}>
                            <div className="cm-customer-chip-list__meta">
                              <strong>
                                {customer.customer_code}/{customer.customer_store}
                              </strong>
                              <span>{customer.customer_name?.trim() || "—"}</span>
                            </div>
                            <ActionButton
                              variant="ghost"
                              disabled={busyCustomerKey === key}
                              onClick={() =>
                                handleRemoveCustomer(
                                  customer.customer_code,
                                  customer.customer_store,
                                )
                              }
                              aria-label={`Remover ${customer.customer_name ?? customer.customer_code}`}
                            >
                              <Trash2 size={14} strokeWidth={1.75} aria-hidden="true" />
                              Remover
                            </ActionButton>
                          </li>
                        );
                      })}
                    </ul>
                  )}
                </div>
              </section>
            </div>
          )}
        </CommercialViewTransition>
      </SectionCard>
      </div>

      <SectionCard
        title="Transferir clientes"
        subtitle="Origem, destino, clientes e motivo — com auditoria."
        hint={CM_HELP.sellerPortfolios.transfer}
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        <div className="cm-portfolios-form">
          <CommercialSelectField
            label="Carteira origem"
            hint={CM_HELP.sellerPortfolios.transferSource}
            value={transferSourceId}
            onChange={(value: string) => {
              setTransferSourceId(value);
              setTransferCustomerKeys([]);
            }}
            options={portfolioOptions}
            allowEmpty
            emptyLabel="Selecione…"
            searchable
          />
          <CommercialSelectField
            label="Carteira destino"
            hint={CM_HELP.sellerPortfolios.transferTarget}
            value={transferTargetId}
            onChange={setTransferTargetId}
            options={portfolioOptions}
            allowEmpty
            emptyLabel="Selecione…"
            searchable
          />
          <div className="cm-portfolios-form__user">
            <CommercialMultiSelectField
              label="Clientes a transferir"
              hint={CM_HELP.sellerPortfolios.transferCustomers}
              options={transferCustomerOptions}
              selectedValues={transferCustomerKeys}
              onChange={setTransferCustomerKeys}
              searchable
              showSelectedTags
            />
          </div>
          <div className="cm-portfolios-form__user">
            <CommercialTextAreaField
              label="Motivo da transferência"
              hint={CM_HELP.sellerPortfolios.transferReason}
              value={transferReason}
              onChange={setTransferReason}
              placeholder="Ex.: Reorganização de carteira regional"
              required
            />
          </div>
          <div className="cm-portfolios-form__actions">
            <ActionButton variant="primary" onClick={handleTransfer} disabled={transferring}>
              {transferring ? "Transferindo…" : "Transferir clientes"}
            </ActionButton>
          </div>
        </div>
      </SectionCard>
    </section>
  );
}
