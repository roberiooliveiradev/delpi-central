import { useEffect, useState, type FormEvent } from "react";
import {
  ActionButton,
  EmptyState,
  SectionCard,
  StateBanner,
} from "@delpi/plugin-ui/index";

import {
  createSellerPortfolio,
  listSellerPortfolios,
  transferSellerCustomers,
} from "../../api/commercialPortfolioApi";
import {
  CommercialLoadingCard,
  cmEmptyStateClassNames,
  cmSectionCardClassNames,
  cmSectionLabels,
  cmStateBannerClassNames,
} from "../../app/commercialUi";
import type { SellerCustomerInput, SellerPortfolio } from "../../types/portfolio";

export function SellerPortfoliosPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [items, setItems] = useState<SellerPortfolio[]>([]);
  const [message, setMessage] = useState<string | null>(null);

  const [createUserId, setCreateUserId] = useState("");
  const [createDisplayName, setCreateDisplayName] = useState("");
  const [creating, setCreating] = useState(false);

  const [transferSourceId, setTransferSourceId] = useState("");
  const [transferTargetId, setTransferTargetId] = useState("");
  const [transferCode, setTransferCode] = useState("");
  const [transferStore, setTransferStore] = useState("");
  const [transferring, setTransferring] = useState(false);

  const reload = () => {
    setLoading(true);
    setError(null);
    listSellerPortfolios({ activeOnly: true })
      .then((response) => setItems(response))
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Erro ao listar carteiras.");
        setItems([]);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    reload();
  }, []);

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    setCreating(true);
    setMessage(null);
    setError(null);
    try {
      await createSellerPortfolio({
        user_id: createUserId.trim(),
        display_name: createDisplayName.trim(),
      });
      setCreateUserId("");
      setCreateDisplayName("");
      setMessage("Carteira criada com sucesso.");
      reload();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro ao criar carteira.");
    } finally {
      setCreating(false);
    }
  }

  async function handleTransfer(event: FormEvent) {
    event.preventDefault();
    const customers: SellerCustomerInput[] = [
      {
        customer_code: transferCode.trim(),
        customer_store: transferStore.trim(),
      },
    ];
    if (!transferSourceId.trim() || !transferTargetId.trim() || !customers[0]?.customer_code) {
      setError("Informe origem, destino, código e loja do cliente.");
      return;
    }

    setTransferring(true);
    setMessage(null);
    setError(null);
    try {
      const result = await transferSellerCustomers(transferSourceId.trim(), {
        target_seller_id: transferTargetId.trim(),
        customers,
      });
      setMessage(
        `Transferência concluída: ${result.transferred_count} cliente(s) movido(s).`,
      );
      setTransferCode("");
      setTransferStore("");
      reload();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro ao transferir clientes.");
    } finally {
      setTransferring(false);
    }
  }

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
        ) : items.length === 0 ? (
          <EmptyState
            title="Nenhuma carteira ativa"
            message="Cadastre a primeira carteira abaixo."
            defaultMessage="Nenhuma carteira cadastrada."
            classNames={cmEmptyStateClassNames}
          />
        ) : (
          <ul>
            {items.map((item) => (
              <li key={item.id}>
                <strong>{item.display_name}</strong> — {item.customer_count} cliente(s) · user{" "}
                {item.user_id}
              </li>
            ))}
          </ul>
        )}
      </SectionCard>

      <SectionCard
        title="Nova carteira"
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        <form className="cm-form-grid" onSubmit={handleCreate}>
          <label>
            ID do usuário (Keycloak)
            <input
              value={createUserId}
              onChange={(event) => setCreateUserId(event.target.value)}
              required
            />
          </label>
          <label>
            Nome de exibição
            <input
              value={createDisplayName}
              onChange={(event) => setCreateDisplayName(event.target.value)}
              required
            />
          </label>
          <ActionButton variant="primary" type="submit" disabled={creating}>
            {creating ? "Salvando…" : "Criar carteira"}
          </ActionButton>
        </form>
      </SectionCard>

      <SectionCard
        title="Transferir clientes (stub)"
        subtitle="Informe origem, destino e par código + loja."
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        <form className="cm-form-grid" onSubmit={handleTransfer}>
          <label>
            Carteira origem (seller_id)
            <select value={transferSourceId} onChange={(event) => setTransferSourceId(event.target.value)}>
              <option value="">Selecione…</option>
              {items.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.display_name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Carteira destino (seller_id)
            <select value={transferTargetId} onChange={(event) => setTransferTargetId(event.target.value)}>
              <option value="">Selecione…</option>
              {items.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.display_name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Código cliente
            <input value={transferCode} onChange={(event) => setTransferCode(event.target.value)} />
          </label>
          <label>
            Loja
            <input value={transferStore} onChange={(event) => setTransferStore(event.target.value)} />
          </label>
          <ActionButton variant="primary" type="submit" disabled={transferring}>
            {transferring ? "Transferindo…" : "Transferir cliente"}
          </ActionButton>
        </form>
      </SectionCard>
    </section>
  );
}
