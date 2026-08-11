import { useEffect, useMemo, useState } from "react";

import { searchActiveCustomers } from "../../api/commercialPortfolioApi";
import {
  CommercialActionButton,
  CommercialDataTable,
  CommercialEmptyState,
  CommercialFilterBarShell,
  CommercialLoadingCard,
  CommercialSectionCard,
  CommercialStateBanner,
  CommercialStatusBadge,
  CommercialTextField,
  CommercialViewTransition,
  type DataTableColumn,
} from "../../app/commercialUi";
import { CM_HELP } from "../../content/helpTooltips";
import { customerKey } from "../../shared/format";
import type { SellerCustomer, SellerPortfolio, TotvsCustomerHit } from "../../types/portfolio";

type SellerPortfolioDetailProps = {
  portfolio: SellerPortfolio | null;
  userLabel: string;
  savingName: boolean;
  busyCustomerKey: string | null;
  onSaveName: (displayName: string) => void;
  onAddCustomer: (hit: TotvsCustomerHit) => void;
  onRemoveCustomer: (code: string, store: string) => void;
  onDeactivate: () => void;
  onReactivate: () => void;
  onPurge: () => void;
  onTransfer: () => void;
};

export function SellerPortfolioDetail({
  portfolio,
  userLabel,
  savingName,
  busyCustomerKey,
  onSaveName,
  onAddCustomer,
  onRemoveCustomer,
  onDeactivate,
  onReactivate,
  onPurge,
  onTransfer,
}: SellerPortfolioDetailProps) {
  const [editName, setEditName] = useState(portfolio?.display_name ?? "");
  const [customerQuery, setCustomerQuery] = useState("");
  const [customerHits, setCustomerHits] = useState<TotvsCustomerHit[]>([]);
  const [searchingCustomers, setSearchingCustomers] = useState(false);
  const [customerSearchError, setCustomerSearchError] = useState<string | null>(null);

  useEffect(() => {
    setEditName(portfolio?.display_name ?? "");
    setCustomerQuery("");
    setCustomerHits([]);
    setCustomerSearchError(null);
  }, [portfolio?.id]);

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
          setCustomerSearchError(
            err instanceof Error && err.message.trim()
              ? err.message
              : "Não foi possível buscar clientes no cadastro.",
          );
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

  const linked = portfolio?.customers ?? [];
  const queryReady = customerQuery.trim().length >= 2;

  const hitColumns = useMemo<DataTableColumn<TotvsCustomerHit>[]>(
    () => [
      {
        key: "code",
        header: "Código/loja",
        render: (row) => `${row.code}/${row.store}`,
      },
      {
        key: "name",
        header: "Nome",
        render: (row) => row.name,
      },
      {
        key: "action",
        header: "Ação",
        render: (row) => {
          const key = customerKey(row.code, row.store);
          const alreadyLinked = linked.some(
            (customer) => customerKey(customer.customer_code, customer.customer_store) === key,
          );
          if (alreadyLinked) {
            return (
              <CommercialStatusBadge label="Já vinculado" variant="success" />
            );
          }
          return (
            <CommercialActionButton
              variant="primary"
              disabled={busyCustomerKey === key}
              onClick={() => onAddCustomer(row)}
            >
              {busyCustomerKey === key ? "Vinculando…" : "Vincular"}
            </CommercialActionButton>
          );
        },
      },
    ],
    [busyCustomerKey, linked, onAddCustomer],
  );

  const linkedColumns = useMemo<DataTableColumn<SellerCustomer>[]>(
    () => [
      {
        key: "code",
        header: "Código/loja",
        render: (row) => `${row.customer_code}/${row.customer_store}`,
      },
      {
        key: "name",
        header: "Nome",
        render: (row) => row.customer_name?.trim() || "—",
      },
      {
        key: "action",
        header: "Ação",
        render: (row) => {
          const key = customerKey(row.customer_code, row.customer_store);
          return (
            <CommercialActionButton
              variant="ghost"
              disabled={busyCustomerKey === key}
              onClick={() => onRemoveCustomer(row.customer_code, row.customer_store)}
              aria-label={`Remover ${row.customer_name ?? row.customer_code}`}
            >
              {busyCustomerKey === key ? "Removendo…" : "Remover"}
            </CommercialActionButton>
          );
        },
      },
    ],
    [busyCustomerKey, onRemoveCustomer],
  );

  if (!portfolio) {
    return (
      <CommercialSectionCard title="Conta da carteira" hint={CM_HELP.sellerPortfolios.edit}>
        <CommercialEmptyState
          title="Selecione uma carteira"
          message="Escolha uma carteira na lista para editar, vincular clientes ou transferir."
        />
      </CommercialSectionCard>
    );
  }

  return (
    <CommercialSectionCard
      title={portfolio.display_name}
      subtitle={`${userLabel} · ${portfolio.active ? "Ativa" : "Inativa"}`}
      hint={CM_HELP.sellerPortfolios.edit}
      actions={
        <CommercialStatusBadge
          label={portfolio.active ? "Ativa" : "Inativa"}
          variant={portfolio.active ? "success" : "neutral"}
        />
      }
    >
      <div className="cm-portfolios-detail-stack">
        <div className="cm-portfolios-form">
          <div className="cm-portfolios-form__display-name">
            <CommercialTextField
              label="Nome de exibição"
              hint={CM_HELP.sellerPortfolios.displayName}
              value={editName}
              onChange={setEditName}
              required
            />
          </div>
          <div className="cm-portfolios-form__actions">
            <CommercialActionButton
              variant="primary"
              onClick={() => onSaveName(editName.trim())}
              disabled={savingName || !editName.trim() || editName.trim() === portfolio.display_name}
            >
              {savingName ? "Salvando…" : "Salvar"}
            </CommercialActionButton>
          </div>
        </div>

        <section className="cm-portfolios-detail-block" aria-label="Buscar e vincular">
          <h3 className="cm-section-subtitle">Buscar e vincular</h3>
          <CommercialFilterBarShell embedded ariaLabel="Buscar no cadastro ativo">
            <CommercialTextField
              label="Buscar no cadastro"
              hint={CM_HELP.sellerPortfolios.searchCustomers}
              type="search"
              value={customerQuery}
              onChange={setCustomerQuery}
              placeholder="Código ou nome do cliente"
            />
          </CommercialFilterBarShell>
          <div aria-live="polite">
            {!queryReady ? (
              <CommercialEmptyState
                title="Digite para buscar"
                message="Informe código ou nome (ao menos 2 caracteres) para listar clientes ativos."
              />
            ) : searchingCustomers ? (
              <CommercialLoadingCard title="Buscando no cadastro…" variant="panel" />
            ) : customerSearchError ? (
              <CommercialStateBanner variant="error">{customerSearchError}</CommercialStateBanner>
            ) : customerHits.length === 0 ? (
              <CommercialEmptyState
                title="Nenhum cliente encontrado"
                message={`Nada para “${customerQuery.trim()}”. Tente outro código ou nome.`}
              />
            ) : (
              <CommercialDataTable
                rows={customerHits}
                columns={hitColumns}
                rowKey={(row, index) => customerKey(row.code, row.store) || `hit-${index}`}
                layout="embedded"
              />
            )}
          </div>
        </section>

        <section className="cm-portfolios-detail-block" aria-label="Clientes vinculados">
          <h3 className="cm-section-subtitle">
            Na carteira ({linked.length.toLocaleString("pt-BR")})
          </h3>
          <CommercialViewTransition transitionKey={`linked-${portfolio.id}-${linked.length}`} tone="panel">
            {linked.length === 0 ? (
              <CommercialEmptyState
                title="Carteira vazia"
                message="Use a busca acima para vincular o primeiro cliente."
              />
            ) : (
              <CommercialDataTable
                rows={linked}
                columns={linkedColumns}
                rowKey={(row, index) =>
                  customerKey(row.customer_code, row.customer_store) || `linked-${index}`
                }
                layout="embedded"
              />
            )}
          </CommercialViewTransition>
        </section>

        <div className="cm-row-actions">
          {portfolio.active ? (
            <CommercialActionButton variant="ghost" onClick={onDeactivate}>
              Inativar
            </CommercialActionButton>
          ) : (
            <CommercialActionButton variant="ghost" onClick={onReactivate}>
              Reativar
            </CommercialActionButton>
          )}
          <CommercialActionButton variant="ghost" onClick={onTransfer}>
            Transferir clientes
          </CommercialActionButton>
          <CommercialActionButton variant="ghost" onClick={onPurge}>
            Excluir
          </CommercialActionButton>
        </div>
      </div>
    </CommercialSectionCard>
  );
}
