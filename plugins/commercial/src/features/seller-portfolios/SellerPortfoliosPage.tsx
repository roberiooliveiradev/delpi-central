import { useEffect, useMemo, useState } from "react";
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
import {
  CommercialLoadingCard,
  CommercialMultiSelectField,
  CommercialSelectField,
  CommercialTextAreaField,
  CommercialTextField,
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

export function SellerPortfoliosPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [portfolios, setPortfolios] = useState<SellerPortfolio[]>([]);

  const [createUser, setCreateUser] = useState<DirectoryUserOption[]>([]);
  const [createDisplayName, setCreateDisplayName] = useState("");
  const [creating, setCreating] = useState(false);

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

  const columns = useMemo<DataTableColumn<SellerPortfolio>[]>(
    () => [
      { key: "display_name", header: "Carteira", render: (row) => row.display_name },
      { key: "user_id", header: "Usuário", render: (row) => row.user_id },
      {
        key: "customer_count",
        header: "Clientes",
        align: "right",
        render: (row) => row.customer_count.toLocaleString("pt-BR"),
      },
      {
        key: "status",
        header: "Status",
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
        render: (row) => (
          <div className="cm-row-actions">
            <ActionButton variant="ghost" onClick={() => startEdit(row)}>
              Editar
            </ActionButton>
            <ActionButton variant="ghost" onClick={() => setManageDataPortfolioId(row.id)}>
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
        title="Carteiras de vendedores"
        subtitle="Administração de carteiras via commercial-api"
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        {loading ? (
          <CommercialLoadingCard title="Carregando carteiras" variant="panel" />
        ) : portfolios.length === 0 ? (
          <EmptyState
            title="Nenhuma carteira cadastrada"
            message="Cadastre a primeira carteira abaixo."
            defaultMessage="Nenhuma carteira cadastrada."
            classNames={cmEmptyStateClassNames}
          />
        ) : (
          <DataTable
            rows={portfolios}
            columns={columns}
            rowKey={(row: SellerPortfolio) => row.id}
            classNames={cmDataTableClassNames}
            labels={cmDataTableLabels}
            layout="section"
          />
        )}
      </SectionCard>

      <SectionCard
        title="Nova carteira"
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        <div className="cm-form-grid">
          <UserDirectoryPicker
            value={createUser}
            onChange={setCreateUser}
            searchUsers={searchDirectoryUsers}
            maxSelected={1}
            labels={{
              title: "Usuário (Keycloak)",
              hint: "Busque por nome ou e-mail.",
              placeholder: "Buscar usuário…",
            }}
          />
          <CommercialTextField
            label="Nome de exibição"
            value={createDisplayName}
            onChange={setCreateDisplayName}
            placeholder="Ex.: João Silva"
            required
          />
          <ActionButton variant="primary" onClick={handleCreate} disabled={creating}>
            <Plus size={16} strokeWidth={1.75} aria-hidden="true" />
            {creating ? "Salvando…" : "Criar carteira"}
          </ActionButton>
        </div>
      </SectionCard>

      {editingPortfolioId ? (
        <SectionCard
          title="Editar carteira"
          classNames={cmSectionCardClassNames}
          labels={cmSectionLabels}
        >
          <div className="cm-form-grid">
            <CommercialTextField
              label="Nome de exibição"
              value={editDisplayName}
              onChange={setEditDisplayName}
              required
            />
            <div className="cm-row-actions">
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

      <SectionCard
        title="Gerenciar clientes da carteira"
        subtitle="Busque clientes ativos no TOTVS e vincule ou remova da carteira selecionada."
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        <div className="cm-form-grid">
          <CommercialSelectField
            label="Carteira"
            value={manageDataPortfolioId}
            onChange={setManageDataPortfolioId}
            options={portfolioOptions}
            allowEmpty
            emptyLabel="Selecione uma carteira"
            searchable
          />
        </div>

        {manageDataPortfolio ? (
          <div className="cm-manage-customers-grid">
            <div>
              <h4>Clientes vinculados ({manageDataPortfolio.customers.length})</h4>
              {manageDataPortfolio.customers.length === 0 ? (
                <EmptyState
                  title="Nenhum cliente vinculado"
                  message="Use a busca ao lado para adicionar clientes."
                  defaultMessage="Nenhum cliente vinculado."
                  classNames={cmEmptyStateClassNames}
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
        ) : null}
      </SectionCard>

      <SectionCard
        title="Transferir clientes"
        subtitle="Selecione origem, destino, clientes e o motivo da transferência."
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        <div className="cm-form-grid">
          <CommercialSelectField
            label="Carteira origem"
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
            value={transferTargetId}
            onChange={setTransferTargetId}
            options={portfolioOptions}
            allowEmpty
            emptyLabel="Selecione…"
            searchable
          />
          <CommercialMultiSelectField
            label="Clientes a transferir"
            options={transferCustomerOptions}
            selectedValues={transferCustomerKeys}
            onChange={setTransferCustomerKeys}
            searchable
            showSelectedTags
          />
          <CommercialTextAreaField
            label="Motivo da transferência"
            value={transferReason}
            onChange={setTransferReason}
            placeholder="Ex.: Reorganização de carteira regional"
            required
          />
          <ActionButton variant="primary" onClick={handleTransfer} disabled={transferring}>
            {transferring ? "Transferindo…" : "Transferir clientes"}
          </ActionButton>
        </div>
      </SectionCard>
    </section>
  );
}
