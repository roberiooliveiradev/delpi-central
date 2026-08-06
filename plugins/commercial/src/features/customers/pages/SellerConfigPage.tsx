import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ArrowRightLeft,
  ImageOff,
  ImagePlus,
  Plus,
  Search,
  Trash2,
  UserPlus,
} from "lucide-react";

import { usePortfolioScope } from "../../../app/usePortfolioScope";
import { CommercialSelectField } from "../../../app/commercialUi";
import {
  addSellerCustomer,
  createSellerPortfolio,
  deactivateSellerPortfolio,
  listSellerPortfolios,
  removeSellerCustomer,
  searchActiveTotvsCustomers,
  searchDirectoryUsers,
  transferSellerCustomers,
  type DirectoryUser,
  type TotvsCustomerHit,
} from "../../../api/sellerPortfolioApi";
import {
  deleteCustomerAvatar,
  upsertCustomerAvatar,
} from "../../../api/customerEnrichmentApi";
import type { SellerPortfolio } from "../../../types/sellerPortfolio";
import { EmptyState } from "../../../ui/EmptyState";
import { navigatePluginView } from "../../../app/pluginNavigation";
import { CustomerAvatar } from "../components/CustomerAvatar";

type ConfigPageProps = {
  basePath: string;
};

function customerKey(code: string, store: string): string {
  return `${code.trim()}|${store.trim()}`;
}

export function SellerConfigPage({ basePath }: ConfigPageProps) {
  const { isAdmin, loading: scopeLoading, reloadScope } = usePortfolioScope();
  const [sellers, setSellers] = useState<SellerPortfolio[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [userQuery, setUserQuery] = useState("");
  const [userHits, setUserHits] = useState<DirectoryUser[]>([]);
  const [creating, setCreating] = useState(false);
  const [customerQuery, setCustomerQuery] = useState("");
  const [customerHits, setCustomerHits] = useState<TotvsCustomerHit[]>([]);
  const [customerSearchLoading, setCustomerSearchLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [transferMode, setTransferMode] = useState(false);
  const [transferTargetId, setTransferTargetId] = useState("");
  const [transferSelected, setTransferSelected] = useState<Set<string>>(new Set());
  /** Presença de logo conhecida nesta sessão (upload/remoção); bump força refresh do blob. */
  const [logoPresence, setLogoPresence] = useState<Record<string, number>>({});

  const selected = useMemo(
    () => sellers.find((item) => item.id === selectedId) ?? null,
    [sellers, selectedId],
  );

  const transferTargets = useMemo(
    () =>
      sellers.filter(
        (item) => item.active && item.id !== selectedId,
      ),
    [sellers, selectedId],
  );

  const linkedKeys = useMemo(() => {
    const keys = new Set<string>();
    for (const customer of selected?.customers ?? []) {
      keys.add(customerKey(customer.customer_code, customer.customer_store));
    }
    return keys;
  }, [selected]);

  const availableHits = useMemo(
    () =>
      customerHits.filter(
        (hit) => hit.code && hit.store && !linkedKeys.has(customerKey(hit.code, hit.store)),
      ),
    [customerHits, linkedKeys],
  );

  function resetTransferUi() {
    setTransferMode(false);
    setTransferTargetId("");
    setTransferSelected(new Set());
  }

  function selectSeller(sellerId: string) {
    setSelectedId(sellerId);
    setCustomerQuery("");
    setCustomerHits([]);
    resetTransferUi();
  }

  useEffect(() => {
    if (!isAdmin || scopeLoading) return;
    const controller = new AbortController();
    // Carrega lista admin quando a permissão estiver disponível.
    // eslint-disable-next-line react-hooks/set-state-in-effect -- fetch inicial sincronizado com isAdmin
    setLoading(true);
    setError(null);
    void listSellerPortfolios({ signal: controller.signal })
      .then((items) => {
        if (controller.signal.aborted) return;
        setSellers(items);
        setSelectedId((current) => {
          if (current && items.some((item) => item.id === current)) return current;
          return items[0]?.id ?? null;
        });
      })
      .catch((err) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Falha ao carregar vendedores.");
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [isAdmin, scopeLoading]);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const items = await listSellerPortfolios();
      setSellers(items);
      setSelectedId((current) => {
        if (current && items.some((item) => item.id === current)) return current;
        return items[0]?.id ?? null;
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar vendedores.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    const handle = window.setTimeout(() => {
      void searchDirectoryUsers(userQuery, 8, controller.signal)
        .then((items) => {
          if (!controller.signal.aborted) setUserHits(items);
        })
        .catch(() => {
          if (!controller.signal.aborted) setUserHits([]);
        });
    }, 250);
    return () => {
      controller.abort();
      window.clearTimeout(handle);
    };
  }, [userQuery]);

  useEffect(() => {
    if (!selected) {
      setCustomerHits([]);
      setCustomerSearchLoading(false);
      return;
    }
    const term = customerQuery.trim();
    if (term.length < 2) {
      setCustomerHits([]);
      setCustomerSearchLoading(false);
      return;
    }
    const controller = new AbortController();
    const handle = window.setTimeout(() => {
      setCustomerSearchLoading(true);
      void searchActiveTotvsCustomers(term, {
        pageSize: 12,
        signal: controller.signal,
      })
        .then((result) => {
          if (!controller.signal.aborted) setCustomerHits(result.items);
        })
        .catch((err) => {
          if (controller.signal.aborted) return;
          setCustomerHits([]);
          setError(err instanceof Error ? err.message : "Falha ao buscar clientes no TOTVS.");
        })
        .finally(() => {
          if (!controller.signal.aborted) setCustomerSearchLoading(false);
        });
    }, 250);
    return () => {
      controller.abort();
      window.clearTimeout(handle);
    };
  }, [customerQuery, selected?.id]);

  if (scopeLoading) {
    return (
      <div className="pva-internal-page" role="status">
        Carregando permissões…
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="pva-internal-page">
        <EmptyState
          title="Acesso restrito"
          description="A configuração de carteiras é exclusiva para gerentes com permissão de administração."
          action={
            <button
              type="button"
              className="pva-btn pva-btn--secondary"
              onClick={() => navigatePluginView("customers", { basePath })}
            >
              Ir para Minha carteira
            </button>
          }
        />
      </div>
    );
  }

  async function handleCreate(user: DirectoryUser) {
    setCreating(true);
    setError(null);
    try {
      const created = await createSellerPortfolio({
        user_id: user.id,
        display_name: user.name || user.email || user.id,
        customers: [],
      });
      setUserQuery("");
      setUserHits([]);
      await reload();
      setSelectedId(created.id);
      reloadScope();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao cadastrar vendedor.");
    } finally {
      setCreating(false);
    }
  }

  async function handleAddCustomer(hit: TotvsCustomerHit) {
    if (!selected) return;
    setBusy(true);
    setError(null);
    try {
      const updated = await addSellerCustomer(selected.id, {
        customer_code: hit.code,
        customer_store: hit.store,
        customer_name: hit.name || null,
      });
      setSellers((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      );
      reloadScope();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao adicionar cliente.");
    } finally {
      setBusy(false);
    }
  }

  async function handleRemoveCustomer(code: string, store: string) {
    if (!selected) return;
    setBusy(true);
    setError(null);
    try {
      const updated = await removeSellerCustomer(selected.id, code, store);
      setSellers((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      );
      reloadScope();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao remover cliente.");
    } finally {
      setBusy(false);
    }
  }

  async function handleDeactivate() {
    if (!selected) return;
    if (!window.confirm(`Desativar o vendedor ${selected.display_name}?`)) return;
    setBusy(true);
    setError(null);
    try {
      await deactivateSellerPortfolio(selected.id);
      await reload();
      resetTransferUi();
      reloadScope();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao desativar vendedor.");
    } finally {
      setBusy(false);
    }
  }

  function toggleTransferCustomer(key: string) {
    setTransferSelected((current) => {
      const next = new Set(current);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  function selectAllLinkedForTransfer() {
    if (!selected) return;
    setTransferSelected(
      new Set(
        selected.customers.map((item) =>
          customerKey(item.customer_code, item.customer_store),
        ),
      ),
    );
  }

  async function handleTransfer() {
    if (!selected) return;
    if (!transferTargetId) {
      setError("Selecione o vendedor de destino.");
      return;
    }
    if (transferSelected.size === 0) {
      setError("Selecione ao menos um cliente para transferir.");
      return;
    }
    const customers = selected.customers.filter((item) =>
      transferSelected.has(customerKey(item.customer_code, item.customer_store)),
    );
    const target = sellers.find((item) => item.id === transferTargetId);
    if (
      !window.confirm(
        `Transferir ${customers.length} cliente(s) de ${selected.display_name} para ${target?.display_name ?? "destino"}?`,
      )
    ) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const result = await transferSellerCustomers(selected.id, {
        target_seller_id: transferTargetId,
        customers: customers.map((item) => ({
          customer_code: item.customer_code,
          customer_store: item.customer_store,
          customer_name: item.customer_name,
        })),
      });
      setSellers((current) =>
        current.map((item) => {
          if (item.id === result.source.id) return result.source;
          if (item.id === result.target.id) return result.target;
          return item;
        }),
      );
      resetTransferUi();
      reloadScope();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao transferir clientes.");
    } finally {
      setBusy(false);
    }
  }

  async function handleUploadLogo(code: string, store: string, file: File) {
    const key = customerKey(code, store);
    setBusy(true);
    setError(null);
    try {
      await upsertCustomerAvatar(code, store, file);
      setLogoPresence((current) => ({
        ...current,
        [key]: (current[key] ?? 0) + 1,
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao salvar logo.");
    } finally {
      setBusy(false);
    }
  }

  async function handleRemoveLogo(code: string, store: string) {
    const key = customerKey(code, store);
    setBusy(true);
    setError(null);
    try {
      await deleteCustomerAvatar(code, store);
      setLogoPresence((current) => ({
        ...current,
        [key]: (current[key] ?? 0) + 1,
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao remover logo.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="pva-internal-page pva-config-page">
      <header className="pva-customers-page__header">
        <div className="pva-customers-page__titles">
          <h2 className="pva-internal-page__title">Configuração de carteiras</h2>
          <p className="pva-internal-page__text">
            Cadastre vendedores (usuários Minha DELPI) e vincule clientes ativos do TOTVS à
            carteira de cada um.
          </p>
        </div>
      </header>

      {error ? (
        <div className="pva-alert pva-alert--error" role="alert">
          <p>{error}</p>
        </div>
      ) : null}

      <section className="pva-checkup-panel" aria-label="Cadastrar vendedor">
        <h3 className="pva-checkup-panel__title">Novo vendedor</h3>
        <div className="pva-search">
          <Search size={18} className="pva-search__icon" aria-hidden="true" />
          <label className="visually-hidden" htmlFor="pva-config-user-search">
            Buscar usuário Minha DELPI
          </label>
          <input
            id="pva-config-user-search"
            className="pva-search__input"
            type="search"
            value={userQuery}
            onChange={(event) => setUserQuery(event.target.value)}
            placeholder="Buscar usuário por nome ou e-mail"
            autoComplete="off"
            disabled={creating}
          />
        </div>
        {userHits.length > 0 ? (
          <ul className="pva-config-user-hits">
            {userHits.map((user) => (
              <li key={user.id}>
                <button
                  type="button"
                  className="pva-btn pva-btn--secondary"
                  disabled={creating}
                  onClick={() => void handleCreate(user)}
                >
                  <UserPlus size={16} aria-hidden="true" />
                  {user.name || "Sem nome"} · {user.email}
                </button>
              </li>
            ))}
          </ul>
        ) : null}
      </section>

      <div className="pva-config-layout">
        <section className="pva-checkup-panel" aria-label="Vendedores">
          <h3 className="pva-checkup-panel__title">Vendedores</h3>
          {loading ? <p role="status">Carregando…</p> : null}
          {!loading && sellers.length === 0 ? (
            <EmptyState
              title="Nenhum vendedor"
              description="Busque um usuário Minha DELPI acima para cadastrar o primeiro vendedor."
            />
          ) : null}
          <ul className="pva-config-seller-list">
            {sellers.map((seller) => (
              <li key={seller.id}>
                <button
                  type="button"
                  className={
                    seller.id === selectedId
                      ? "pva-config-seller pva-config-seller--active"
                      : "pva-config-seller"
                  }
                  onClick={() => selectSeller(seller.id)}
                >
                  <strong>{seller.display_name}</strong>
                  <span>
                    {seller.customer_count} cliente(s)
                    {!seller.active ? " · inativo" : ""}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </section>

        <section className="pva-checkup-panel pva-config-portfolio-panel" aria-label="Clientes da carteira">
          {selected ? (
            <>
              <div className="pva-section__header">
                <div>
                  <h3 className="pva-checkup-panel__title">{selected.display_name}</h3>
                  <p className="pva-section__hint">
                    {selected.customer_count} cliente(s) na carteira
                  </p>
                </div>
                <div className="pva-config-header-actions">
                  {selected.customers.length > 0 ? (
                    <button
                      type="button"
                      className={
                        transferMode
                          ? "pva-btn pva-btn--primary"
                          : "pva-btn pva-btn--secondary"
                      }
                      disabled={busy || (!transferMode && transferTargets.length === 0)}
                      title={
                        transferTargets.length === 0
                          ? "Cadastre outro vendedor ativo para transferir a carteira."
                          : "Transferir clientes selecionados para outro vendedor"
                      }
                      onClick={() => {
                        if (transferMode) {
                          resetTransferUi();
                          return;
                        }
                        if (transferTargets.length === 0) return;
                        setTransferMode(true);
                        setTransferSelected(new Set());
                        setTransferTargetId(transferTargets[0]?.id ?? "");
                      }}
                    >
                      <ArrowRightLeft size={16} aria-hidden="true" />
                      {transferMode ? "Cancelar transferência" : "Transferir"}
                    </button>
                  ) : null}
                  {selected.active ? (
                    <button
                      type="button"
                      className="pva-btn pva-btn--secondary"
                      disabled={busy}
                      onClick={() => void handleDeactivate()}
                    >
                      Desativar
                    </button>
                  ) : null}
                </div>
              </div>

              {selected.customers.length > 0 && transferTargets.length === 0 ? (
                <p className="pva-section__hint">
                  Para transferir, cadastre pelo menos outro vendedor ativo em «Novo vendedor».
                </p>
              ) : null}

              {transferMode ? (
                <div className="pva-config-transfer" aria-label="Transferir carteira">
                  <h4 className="pva-config-subtitle">Transferir clientes</h4>
                  <p className="pva-section__hint">
                    Selecione os clientes e o vendedor de destino. Os escolhidos saem desta
                    carteira e entram na do destino.
                  </p>
                  <CommercialSelectField
                    label="Vendedor destino"
                    options={transferTargets.map((seller) => ({
                      value: seller.id,
                      label: `${seller.display_name} (${seller.customer_count})`,
                    }))}
                    value={transferTargetId}
                    onChange={setTransferTargetId}
                    allowEmpty={false}
                    disabled={busy}
                  />
                  <div className="pva-config-transfer__toolbar">
                    <button
                      type="button"
                      className="pva-btn pva-btn--secondary pva-btn--sm"
                      disabled={busy}
                      onClick={selectAllLinkedForTransfer}
                    >
                      Selecionar todos
                    </button>
                    <button
                      type="button"
                      className="pva-btn pva-btn--secondary pva-btn--sm"
                      disabled={busy || transferSelected.size === 0}
                      onClick={() => setTransferSelected(new Set())}
                    >
                      Limpar seleção
                    </button>
                    <span className="pva-section__hint">
                      {transferSelected.size} selecionado(s)
                    </span>
                  </div>
                  <button
                    type="button"
                    className="pva-btn pva-btn--primary"
                    disabled={busy || transferSelected.size === 0 || !transferTargetId}
                    onClick={() => void handleTransfer()}
                  >
                    <ArrowRightLeft size={16} aria-hidden="true" />
                    Confirmar transferência
                  </button>
                </div>
              ) : null}

              {!transferMode ? (
              <div className="pva-config-customer-form">
                <h4 className="pva-config-subtitle">Adicionar do TOTVS</h4>
                <div className="pva-search pva-config-customer-form__search">
                  <Search size={18} className="pva-search__icon" aria-hidden="true" />
                  <label className="visually-hidden" htmlFor="pva-config-customer-search">
                    Buscar cliente ativo no TOTVS
                  </label>
                  <input
                    id="pva-config-customer-search"
                    className="pva-search__input"
                    type="search"
                    value={customerQuery}
                    onChange={(event) => setCustomerQuery(event.target.value)}
                    placeholder="Digite ao menos 2 caracteres (código, loja ou nome)"
                    autoComplete="off"
                    disabled={busy}
                  />
                </div>
                {customerSearchLoading ? (
                  <p className="pva-section__hint" role="status">
                    Buscando no TOTVS…
                  </p>
                ) : null}
                {!customerSearchLoading && customerQuery.trim().length < 2 ? (
                  <p className="pva-section__hint">
                    Busque pelo código, loja ou nome para listar clientes ativos.
                  </p>
                ) : null}
                {!customerSearchLoading &&
                customerQuery.trim().length >= 2 &&
                availableHits.length === 0 ? (
                  <p className="pva-section__hint">
                    {customerHits.length > 0
                      ? "Os clientes encontrados já estão nesta carteira."
                      : "Nenhum cliente ativo encontrado para esta busca."}
                  </p>
                ) : null}
                {availableHits.length > 0 ? (
                  <ul className="pva-config-customer-hits" aria-label="Resultados da busca TOTVS">
                    {availableHits.map((hit) => (
                      <li key={customerKey(hit.code, hit.store)}>
                        <div>
                          <strong>{hit.name || `${hit.code} · Loja ${hit.store}`}</strong>
                          <span>
                            {hit.code} · Loja {hit.store}
                          </span>
                        </div>
                        <button
                          type="button"
                          className="pva-btn pva-btn--primary pva-btn--sm"
                          disabled={busy}
                          onClick={() => void handleAddCustomer(hit)}
                        >
                          <Plus size={14} aria-hidden="true" />
                          Adicionar
                        </button>
                      </li>
                    ))}
                  </ul>
                ) : null}
              </div>
              ) : null}

              <div className="pva-config-linked">
                <h4 className="pva-config-subtitle">
                  Vinculados
                  {selected.customers.length > 0 ? ` (${selected.customers.length})` : ""}
                </h4>
                {selected.customers.length === 0 ? (
                  <p className="pva-section__hint">Nenhum cliente vinculado ainda.</p>
                ) : (
                  <ul className="pva-config-customer-list" aria-label="Clientes vinculados à carteira">
                    {selected.customers.map((customer) => {
                      const key = customerKey(
                        customer.customer_code,
                        customer.customer_store,
                      );
                      const checked = transferSelected.has(key);
                      const logoRev = logoPresence[key] ?? 0;
                      const displayName =
                        customer.customer_name ||
                        `${customer.customer_code} · Loja ${customer.customer_store}`;
                      return (
                        <li key={key} className="pva-config-linked-item">
                          {transferMode ? (
                            <label className="pva-config-transfer-check">
                              <input
                                type="checkbox"
                                checked={checked}
                                disabled={busy}
                                onChange={() => toggleTransferCustomer(key)}
                              />
                              <span className="visually-hidden">
                                Selecionar {customer.customer_code}
                              </span>
                            </label>
                          ) : null}
                          <CustomerAvatar
                            key={`avatar-${key}-${logoRev}`}
                            code={customer.customer_code}
                            store={customer.customer_store}
                            name={displayName}
                            hasAvatar
                            size="sm"
                          />
                          <div className="pva-config-linked-item__text">
                            <strong>{displayName}</strong>
                            <span>
                              {customer.customer_code} · Loja {customer.customer_store}
                            </span>
                          </div>
                          {!transferMode ? (
                            <div className="pva-config-linked__actions">
                              <label
                                className="pva-config-icon-btn"
                                title="Alterar logo"
                              >
                                <ImagePlus size={14} aria-hidden="true" />
                                <span className="visually-hidden">
                                  Alterar logo de {displayName}
                                </span>
                                <input
                                  type="file"
                                  accept="image/png,image/jpeg,image/webp,image/gif"
                                  className="visually-hidden"
                                  disabled={busy}
                                  onChange={(event) => {
                                    const file = event.target.files?.[0];
                                    event.target.value = "";
                                    if (file) {
                                      void handleUploadLogo(
                                        customer.customer_code,
                                        customer.customer_store,
                                        file,
                                      );
                                    }
                                  }}
                                />
                              </label>
                              <button
                                type="button"
                                className="pva-config-icon-btn"
                                disabled={busy}
                                title="Remover logo"
                                aria-label={`Remover logo de ${displayName}`}
                                onClick={() =>
                                  void handleRemoveLogo(
                                    customer.customer_code,
                                    customer.customer_store,
                                  )
                                }
                              >
                                <ImageOff size={14} aria-hidden="true" />
                              </button>
                              <button
                                type="button"
                                className="pva-config-icon-btn pva-config-icon-btn--danger"
                                disabled={busy}
                                title="Desvincular cliente"
                                aria-label={`Remover ${displayName} da carteira`}
                                onClick={() =>
                                  void handleRemoveCustomer(
                                    customer.customer_code,
                                    customer.customer_store,
                                  )
                                }
                              >
                                <Trash2 size={14} aria-hidden="true" />
                              </button>
                            </div>
                          ) : null}
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
            </>
          ) : (
            <EmptyState
              title="Selecione um vendedor"
              description="Escolha um vendedor à esquerda para gerenciar a carteira de clientes."
            />
          )}
        </section>
      </div>
    </div>
  );
}
