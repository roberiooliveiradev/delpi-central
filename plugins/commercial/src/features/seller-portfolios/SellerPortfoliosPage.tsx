import { useEffect, useMemo, useRef, useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import {
  ActionButton,
  DataTable,
  EmptyState,
  SectionCard,
  StateBanner,
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
  cmStateBannerClassNames,
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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [portfolios, setPortfolios] = useState<SellerPortfolio[]>([]);
  const [filter, setFilter] = useState<PortfolioFilter>("all");

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
  const [customerHits, setCustomerHits] = useState<TotvsCustomerHit[]>([]);
  const [searchingCustomers, setSearchingCustomers] = useState(false);
  const [busyCustomerKey, setBusyCustomerKey] = useState<string | null>(null);

  const [transferSourceId, setTransferSourceId] = useState("");
  const [transferTargetId, setTransferTargetId] = useState("");
  const [transferCustomerKeys, setTransferCustomerKeys] = useState<string[]>([]);
  const [transferReason, setTransferReason] = useState("");
  const [transferring, setTransferring] = useState(false);

  function reload() {
    setLoading(true);
    setError(null);
    listSellerPortfolios()
      .then((response) => setPortfolios(response))
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Erro ao listar carteiras.");
        setPortfolios([]);
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    reload();
  }, []);

  useEffect(() => {
    const normalized = customerQuery.trim();
    if (normalized.length < 2) {
      setCustomerHits([]);
      return;
    }
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => {
      setSearchingCustomers(true);
      searchActiveCustomers(normalized, { signal: controller.signal })
        .then((result) => {
          if (!controller.signal.aborted) setCustomerHits(result.items);
        })
        .catch(() => {
          if (!controller.signal.aborted) setCustomerHits([]);
        })
        .finally(() => {
          if (!controller.signal.aborted) setSearchingCustomers(false);
        });
    }, 300);
    return () => {
      controller.abort();
      window.clearTimeout(timeoutId);
    };
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
    if (!user || !createDisplayName.trim()) {
      setError("Selecione um usuário e informe o nome de exibição.");
      return;
    }

    setCreating(true);
    setMessage(null);
    setError(null);
    try {
      await createSellerPortfolio({
        user_id: user.id,
        display_name: createDisplayName.trim(),
      });
      setCreateUser([]);
      setCreateDisplayName("");
      setMessage("Carteira criada com sucesso.");
      setFilter("all");
      reload();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro ao criar carteira.");
    } finally {
      setCreating(false);
    }
  }

  function startEdit(portfolio: SellerPortfolio) {
    setEditingPortfolioId(portfolio.id);
    setEditDisplayName(portfolio.display_name);
    setMessage(null);
    setError(null);
  }

  async function handleSaveEdit() {
    if (!editingPortfolioId || !editDisplayName.trim()) return;
    setSavingEdit(true);
    setMessage(null);
    setError(null);
    try {
      await updateSellerPortfolio(editingPortfolioId, { display_name: editDisplayName.trim() });
      setMessage("Carteira atualizada com sucesso.");
      setEditingPortfolioId(null);
      reload();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro ao atualizar carteira.");
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
      setMessage(null);
      setError(null);
      try {
        await deactivateSellerPortfolio(portfolio.id);
        setMessage("Carteira desativada com sucesso.");
        reload();
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Erro ao desativar carteira.");
      } finally {
        setConfirmingDeactivateId(null);
      }
      return;
    }

    setMessage(null);
    setError(null);
    try {
      await updateSellerPortfolio(portfolio.id, { active: true });
      setMessage("Carteira reativada com sucesso.");
      reload();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro ao reativar carteira.");
    }
  }

  const manageDataPortfolio = portfolios.find((item) => item.id === manageDataPortfolioId) ?? null;

  async function handleAddCustomer(hit: TotvsCustomerHit) {
    if (!manageDataPortfolio) return;
    const key = customerKey(hit.code, hit.store);
    setBusyCustomerKey(key);
    setMessage(null);
    setError(null);
    try {
      await addSellerCustomer(manageDataPortfolio.id, {
        customer_code: hit.code,
        customer_store: hit.store,
        customer_name: hit.name,
      });
      setMessage(`Cliente ${hit.name} adicionado à carteira.`);
      reload();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro ao adicionar cliente.");
    } finally {
      setBusyCustomerKey(null);
    }
  }

  async function handleRemoveCustomer(code: string, store: string) {
    if (!manageDataPortfolio) return;
    const key = customerKey(code, store);
    setBusyCustomerKey(key);
    setMessage(null);
    setError(null);
    try {
      await removeSellerCustomer(manageDataPortfolio.id, code, store);
      setMessage("Cliente removido da carteira.");
      reload();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro ao remover cliente.");
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
    if (!transferSourceId || !transferTargetId) {
      setError("Selecione carteira de origem e destino.");
      return;
    }
    if (transferSourceId === transferTargetId) {
      setError("Origem e destino devem ser carteiras diferentes.");
      return;
    }
    if (transferCustomerKeys.length === 0) {
      setError("Selecione ao menos um cliente para transferir.");
      return;
    }
    if (!transferReason.trim()) {
      setError("Informe o motivo da transferência.");
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
    setMessage(null);
    setError(null);
    try {
      const result = await transferSellerCustomers({
        source_portfolio_id: transferSourceId,
        target_portfolio_id: transferTargetId,
        customers,
        reason_note: transferReason.trim(),
      });
      setMessage(`Transferência concluída: ${result.transferred_count} cliente(s) movido(s).`);
      setTransferCustomerKeys([]);
      setTransferReason("");
      reload();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro ao transferir clientes.");
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
        render: (row) => row.user_id,
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
    [confirmingDeactivateId],
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

      {message ? (
        <StateBanner variant="success" classNames={cmStateBannerClassNames}>
          {message}
        </StateBanner>
      ) : null}
      {error ? (
        <StateBanner variant="error" classNames={cmStateBannerClassNames}>
          {error}
        </StateBanner>
      ) : null}

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
                onChange={setCreateUser}
                searchUsers={searchDirectoryUsers}
                maxSelected={1}
                labels={{
                  title: "Usuário (Minha Delpi)",
                  hint: CM_HELP.sellerPortfolios.directoryUser,
                  placeholder: "Buscar usuário…",
                }}
              />
            </div>
            <CommercialTextField
              label="Nome de exibição"
              hint={CM_HELP.sellerPortfolios.displayName}
              value={createDisplayName}
              onChange={setCreateDisplayName}
              placeholder="Ex.: João Silva"
              required
            />
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
        subtitle="Busque clientes ativos no TOTVS e vincule ou remova da carteira selecionada."
        hint={CM_HELP.sellerPortfolios.customers}
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        <div className="cm-portfolios-form">
          <div className="cm-portfolios-form__user">
            <CommercialSelectField
              label="Carteira"
              hint={CM_HELP.sellerPortfolios.managePortfolio}
              value={manageDataPortfolioId}
              onChange={setManageDataPortfolioId}
              options={portfolioOptions}
              allowEmpty
              emptyLabel="Selecione uma carteira"
              searchable
            />
          </div>
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
              <div>
                <h4>Clientes vinculados ({manageDataPortfolio.customers.length})</h4>
                {manageDataPortfolio.customers.length === 0 ? (
                  <EmptyState
                    classNames={cmEmptyCompactClassNames}
                    defaultTitle="Nenhum cliente vinculado"
                    defaultMessage="Use a busca ao lado para adicionar clientes."
                  />
                ) : (
                  <ul className="cm-customer-chip-list">
                    {manageDataPortfolio.customers.map((customer) => {
                      const key = customerKey(customer.customer_code, customer.customer_store);
                      return (
                        <li key={key}>
                          <span>
                            {customer.customer_code}/{customer.customer_store} ·{" "}
                            {customer.customer_name?.trim() || "—"}
                          </span>
                          <ActionButton
                            variant="ghost"
                            disabled={busyCustomerKey === key}
                            onClick={() =>
                              handleRemoveCustomer(customer.customer_code, customer.customer_store)
                            }
                            aria-label={`Remover ${customer.customer_name ?? customer.customer_code}`}
                          >
                            <Trash2 size={14} strokeWidth={1.75} aria-hidden="true" />
                          </ActionButton>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>

              <div>
                <h4>Buscar clientes ativos (TOTVS)</h4>
                <CommercialTextField
                  label="Buscar"
                  hint={CM_HELP.sellerPortfolios.searchCustomers}
                  value={customerQuery}
                  onChange={setCustomerQuery}
                  placeholder="Código ou nome do cliente"
                />
                {searchingCustomers ? <p className="cm-hint-text">Buscando…</p> : null}
                {customerHits.length > 0 ? (
                  <ul className="cm-customer-chip-list">
                    {customerHits.map((hit) => {
                      const key = customerKey(hit.code, hit.store);
                      const alreadyLinked = manageDataPortfolio.customers.some(
                        (customer) =>
                          customerKey(customer.customer_code, customer.customer_store) === key,
                      );
                      return (
                        <li key={key}>
                          <span>
                            {hit.code}/{hit.store} · {hit.name}
                          </span>
                          <ActionButton
                            variant="ghost"
                            disabled={alreadyLinked || busyCustomerKey === key}
                            onClick={() => handleAddCustomer(hit)}
                          >
                            {alreadyLinked ? "Já vinculado" : "Adicionar"}
                          </ActionButton>
                        </li>
                      );
                    })}
                  </ul>
                ) : null}
              </div>
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
