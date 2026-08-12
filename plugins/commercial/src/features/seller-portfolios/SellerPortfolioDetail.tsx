import { useEffect, useMemo, useState } from "react";
import { UserDirectoryPicker, type DirectoryUserOption } from "@delpi/plugin-ui/index";

import {
  searchActiveCustomers,
  searchDirectoryUsers,
} from "../../api/commercialPortfolioApi";
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
import type {
  SellerCustomer,
  SellerPortfolio,
  SellerPortfolioMember,
  TotvsCustomerHit,
} from "../../types/portfolio";

type SellerPortfolioDetailProps = {
  portfolio: SellerPortfolio;
  userLabel: string;
  savingName: boolean;
  busyCustomerKey: string | null;
  busyMemberUserId: string | null;
  directoryLabelFor: (userId: string, fallback?: string | null) => string;
  onSaveName: (displayName: string) => void;
  onAddCustomer: (hit: TotvsCustomerHit) => void;
  onRemoveCustomer: (code: string, store: string) => void;
  onAddMember: (userId: string) => void;
  onRemoveMember: (userId: string) => void;
  onSetOwner: (userId: string) => void;
  onDeactivate: () => void;
  onReactivate: () => void;
  onPurge: () => void;
  onTransfer: () => void;
};

function resolveMembers(portfolio: SellerPortfolio): SellerPortfolioMember[] {
  const members = portfolio.members ?? [];
  if (members.length > 0) return members;
  const owner = (portfolio.owner_user_id ?? portfolio.user_id).trim();
  return owner ? [{ user_id: owner, role: "owner" }] : [];
}

export function SellerPortfolioDetail({
  portfolio,
  userLabel,
  savingName,
  busyCustomerKey,
  busyMemberUserId,
  directoryLabelFor,
  onSaveName,
  onAddCustomer,
  onRemoveCustomer,
  onAddMember,
  onRemoveMember,
  onSetOwner,
  onDeactivate,
  onReactivate,
  onPurge,
  onTransfer,
}: SellerPortfolioDetailProps) {
  const [editName, setEditName] = useState(portfolio.display_name);
  const [customerQuery, setCustomerQuery] = useState("");
  const [customerHits, setCustomerHits] = useState<TotvsCustomerHit[]>([]);
  const [searchingCustomers, setSearchingCustomers] = useState(false);
  const [customerSearchError, setCustomerSearchError] = useState<string | null>(null);
  const [memberPicker, setMemberPicker] = useState<DirectoryUserOption[]>([]);

  useEffect(() => {
    setEditName(portfolio.display_name);
    setCustomerQuery("");
    setCustomerHits([]);
    setCustomerSearchError(null);
    setMemberPicker([]);
  }, [portfolio.id, portfolio.display_name]);

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

  const linked = portfolio.customers ?? [];
  const members = resolveMembers(portfolio);
  const memberIds = useMemo(
    () => new Set(members.map((member) => member.user_id)),
    [members],
  );
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
            return <CommercialStatusBadge label="Já vinculado" variant="success" />;
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

  const memberColumns = useMemo<DataTableColumn<SellerPortfolioMember>[]>(
    () => [
      {
        key: "user",
        header: "Usuário",
        render: (row) => directoryLabelFor(row.user_id),
      },
      {
        key: "role",
        header: "Papel",
        render: (row) => (
          <CommercialStatusBadge
            label={row.role === "owner" ? "Responsável" : "Membro"}
            variant={row.role === "owner" ? "info" : "neutral"}
          />
        ),
      },
      {
        key: "action",
        header: "Ação",
        render: (row) => {
          const busy = busyMemberUserId === row.user_id;
          return (
            <div className="cm-row-actions">
              {row.role !== "owner" ? (
                <CommercialActionButton
                  variant="ghost"
                  disabled={busy}
                  onClick={() => onSetOwner(row.user_id)}
                  aria-label={CM_HELP.sellerPortfolios.setOwner}
                >
                  {busy ? "Atualizando…" : "Tornar responsável"}
                </CommercialActionButton>
              ) : null}
              {row.role !== "owner" || members.length > 1 ? (
                <CommercialActionButton
                  variant="ghost"
                  disabled={busy || (row.role === "owner" && members.length <= 1)}
                  onClick={() => onRemoveMember(row.user_id)}
                  aria-label={CM_HELP.sellerPortfolios.removeMember}
                >
                  {busy ? "Removendo…" : "Remover"}
                </CommercialActionButton>
              ) : null}
            </div>
          );
        },
      },
    ],
    [busyMemberUserId, directoryLabelFor, members.length, onRemoveMember, onSetOwner],
  );

  return (
    <div className="cm-portfolios-detail-stack">
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
      </CommercialSectionCard>

      <CommercialSectionCard
        title={`Usuários (${members.length.toLocaleString("pt-BR")})`}
        subtitle="Usuário com acesso ao Portal Comercial"
        hint={CM_HELP.sellerPortfolios.members}
      >
        <div className="cm-portfolios-detail-block">
          <UserDirectoryPicker
            value={memberPicker}
            onChange={(users) => {
              const next = users.filter((user) => !memberIds.has(user.id));
              setMemberPicker(next);
              const candidate = next[0];
              if (candidate) {
                onAddMember(candidate.id);
                setMemberPicker([]);
              }
            }}
            searchUsers={async (query, limit, signal) => {
              const hits = await searchDirectoryUsers(query, limit, signal);
              return hits.filter((hit) => !memberIds.has(hit.id));
            }}
            maxSelected={1}
            labels={{
              title: "Usuário com acesso ao Portal Comercial",
              hint: CM_HELP.sellerPortfolios.membersAdd,
              placeholder: "Buscar para adicionar…",
            }}
          />

          <CommercialViewTransition
            transitionKey={`members-${portfolio.id}-${members.length}`}
            tone="panel"
          >
            {members.length === 0 ? (
              <CommercialEmptyState
                title="Sem usuários"
                message="Adicione ao menos um usuário com acesso ao Portal Comercial."
              />
            ) : (
              <CommercialDataTable
                rows={members}
                columns={memberColumns}
                rowKey={(row) => row.user_id}
                layout="embedded"
              />
            )}
          </CommercialViewTransition>
        </div>
      </CommercialSectionCard>

      <CommercialSectionCard
        title="Clientes"
        subtitle="Vincule contas TOTVS a esta carteira"
        hint={CM_HELP.sellerPortfolios.customers}
      >
        <div className="cm-portfolios-detail-stack">
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
            <CommercialViewTransition
              transitionKey={`linked-${portfolio.id}-${linked.length}`}
              tone="panel"
            >
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
        </div>
      </CommercialSectionCard>

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
  );
}
