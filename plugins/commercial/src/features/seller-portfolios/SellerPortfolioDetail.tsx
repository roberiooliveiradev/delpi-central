import { X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  NativeCheckboxControl,
  UserDirectoryPicker,
  type DirectoryUserOption,
} from "@delpi/plugin-ui/index";

import { searchDirectoryUsers } from "../../api/commercialPortfolioApi";
import {
  CommercialActionButton,
  CommercialDataListToolbar,
  CommercialDataTable,
  CommercialEmptyState,
  CommercialSectionCard,
  CommercialStateBanner,
  CommercialStatusBadge,
  CommercialTextField,
  CommercialViewTransition,
  type DataTableColumn,
} from "../../app/commercialUi";
import { CM_HELP } from "../../content/helpTooltips";
import { PORTFOLIO_COVERAGE_CONTENT } from "../../content/portfolioCoverageContent";
import { PORTFOLIO_MEMBERS_CONTENT } from "../../content/portfolioMembersContent";
import { customerKey } from "../../shared/format";
import type {
  SellerCustomer,
  SellerPortfolio,
  SellerPortfolioMember,
} from "../../types/portfolio";
import {
  customerAvatarKey,
  useCustomerAvatarPresence,
} from "../../hooks/useCustomerAvatarPresence";
import { CustomerAvatar } from "../customers/components/CustomerAvatar";
import {
  CustomerSearchPicker,
  type CustomerSearchSelection,
} from "../customers/components/CustomerSearchPicker";
import { TaskUserChipAvatar } from "../my-day/TaskUserChipAvatar";

type SellerPortfolioDetailProps = {
  portfolio: SellerPortfolio;
  userLabel: string;
  savingName: boolean;
  busyCustomerKey: string | null;
  linkingCustomers?: boolean;
  busyMemberUserId: string | null;
  addingMembers?: boolean;
  overlappingCustomerKeys?: ReadonlySet<string>;
  otherPortfolioLabelsFor?: (customerCode: string, customerStore: string) => string[];
  directoryLabelFor: (userId: string | null | undefined, fallback?: string | null) => string;
  onSaveName: (displayName: string) => void;
  onAddCustomers: (items: CustomerSearchSelection[]) => void;
  onRemoveCustomer: (code: string, store: string) => void;
  onRemoveCustomers: (items: Array<{ code: string; store: string }>) => void;
  unlinkingCustomers?: boolean;
  onAddMembers: (userIds: string[]) => void;
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
  const owner = (portfolio.owner_user_id ?? portfolio.user_id ?? "").trim();
  return owner ? [{ user_id: owner, role: "owner" }] : [];
}

export function SellerPortfolioDetail({
  portfolio,
  userLabel,
  savingName,
  busyCustomerKey,
  linkingCustomers = false,
  unlinkingCustomers = false,
  busyMemberUserId,
  addingMembers = false,
  overlappingCustomerKeys,
  otherPortfolioLabelsFor,
  directoryLabelFor,
  onSaveName,
  onAddCustomers,
  onRemoveCustomer,
  onRemoveCustomers,
  onAddMembers,
  onRemoveMember,
  onSetOwner,
  onDeactivate,
  onReactivate,
  onPurge,
  onTransfer,
}: SellerPortfolioDetailProps) {
  const [editName, setEditName] = useState(portfolio.display_name);
  const [memberPicker, setMemberPicker] = useState<DirectoryUserOption[]>([]);
  const [customerPicker, setCustomerPicker] = useState<CustomerSearchSelection[]>([]);
  const [selectedLinkedKeys, setSelectedLinkedKeys] = useState<Set<string>>(
    () => new Set(),
  );

  useEffect(() => {
    setEditName(portfolio.display_name);
    setMemberPicker([]);
    setCustomerPicker([]);
    setSelectedLinkedKeys(new Set());
  }, [portfolio.id, portfolio.display_name]);

  const linked = portfolio.customers ?? [];
  const linkedKeys = useMemo(
    () =>
      new Set(
        linked.map((customer) =>
          customerKey(customer.customer_code, customer.customer_store),
        ),
      ),
    [linked],
  );
  const avatarPairs = useMemo(
    () =>
      linked.map((customer) => ({
        customer_code: customer.customer_code,
        customer_store: customer.customer_store,
      })),
    [linked],
  );
  const avatarByKey = useCustomerAvatarPresence(avatarPairs);

  useEffect(() => {
    setCustomerPicker((prev) =>
      prev.filter((item) => !linkedKeys.has(customerKey(item.code, item.store))),
    );
  }, [linkedKeys]);

  useEffect(() => {
    setSelectedLinkedKeys((prev) => {
      const next = new Set([...prev].filter((key) => linkedKeys.has(key)));
      return next.size === prev.size ? prev : next;
    });
  }, [linkedKeys]);

  const members = resolveMembers(portfolio);
  const isOrphan = members.length === 0;
  const memberIds = useMemo(
    () => new Set(members.map((member) => member.user_id)),
    [members],
  );

  useEffect(() => {
    setMemberPicker((prev) => prev.filter((user) => !memberIds.has(user.id)));
  }, [memberIds]);

  const allLinkedSelected =
    linked.length > 0 &&
    linked.every((row) =>
      selectedLinkedKeys.has(customerKey(row.customer_code, row.customer_store)),
    );

  const linkedColumns = useMemo<DataTableColumn<SellerCustomer>[]>(
    () => [
      {
        key: "select",
        header: "Sel.",
        render: (row) => {
          const key = customerKey(row.customer_code, row.customer_store);
          return (
            <NativeCheckboxControl
              id={`portfolio-linked-${portfolio.id}-${key}`}
              checked={selectedLinkedKeys.has(key)}
              onChange={(checked) => {
                setSelectedLinkedKeys((prev) => {
                  const next = new Set(prev);
                  if (checked) next.add(key);
                  else next.delete(key);
                  return next;
                });
              }}
              aria-label={`Selecionar ${row.customer_name ?? key}`}
              disabled={unlinkingCustomers}
            />
          );
        },
      },
      {
        key: "code",
        header: "Código/loja",
        headerHint: CM_HELP.sellerPortfolios.colCustomerCode,
        render: (row) => `${row.customer_code}/${row.customer_store}`,
      },
      {
        key: "name",
        header: "Nome",
        headerHint: CM_HELP.sellerPortfolios.colCustomerName,
        render: (row) => {
          const name = row.customer_name?.trim() || row.customer_code;
          const hasAvatar =
            avatarByKey.get(
              customerAvatarKey(row.customer_code, row.customer_store),
            ) === true;
          return (
            <div className="cm-row-actions">
              <CustomerAvatar
                code={row.customer_code}
                store={row.customer_store}
                name={name}
                hasAvatar={hasAvatar}
                size="sm"
              />
              <span>{row.customer_name?.trim() || "—"}</span>
            </div>
          );
        },
      },
      {
        key: "coverage",
        header: "Cobertura",
        headerHint: CM_HELP.sellerPortfolios.overlappingCustomer,
        render: (row) => {
          const key = customerKey(row.customer_code, row.customer_store);
          if (!overlappingCustomerKeys?.has(key)) return "—";
          const others = otherPortfolioLabelsFor?.(row.customer_code, row.customer_store) ?? [];
          return (
            <span className="cm-row-actions">
              <CommercialStatusBadge
                label={PORTFOLIO_COVERAGE_CONTENT.overlappingBadge}
                variant="warning"
              />
              {others.length > 0 ? (
                <span>
                  {PORTFOLIO_COVERAGE_CONTENT.overlappingAlsoIn}: {others.join(", ")}
                </span>
              ) : null}
            </span>
          );
        },
      },
      {
        key: "action",
        header: "Ação",
        render: (row) => {
          const key = customerKey(row.customer_code, row.customer_store);
          return (
            <CommercialActionButton
              variant="ghost"
              disabled={
                busyCustomerKey === key || linkingCustomers || unlinkingCustomers
              }
              onClick={() => onRemoveCustomer(row.customer_code, row.customer_store)}
              aria-label={`Remover ${row.customer_name ?? row.customer_code}`}
            >
              {busyCustomerKey === key ? "Removendo…" : "Remover"}
            </CommercialActionButton>
          );
        },
      },
    ],
    [
      avatarByKey,
      busyCustomerKey,
      linkingCustomers,
      onRemoveCustomer,
      otherPortfolioLabelsFor,
      overlappingCustomerKeys,
      portfolio.id,
      selectedLinkedKeys,
      unlinkingCustomers,
    ],
  );

  const memberColumns = useMemo<DataTableColumn<SellerPortfolioMember>[]>(
    () => [
      {
        key: "user",
        header: "Usuário",
        headerHint: CM_HELP.sellerPortfolios.colMemberUser,
        render: (row) => {
          const name = directoryLabelFor(row.user_id);
          return (
            <div className="cm-row-actions">
              <TaskUserChipAvatar userId={row.user_id} name={name} />
              <span>{name}</span>
              {row.has_portal_access === false ? (
                <span title={PORTFOLIO_MEMBERS_CONTENT.noPortalAccessHint}>
                  <CommercialStatusBadge
                    label={PORTFOLIO_MEMBERS_CONTENT.noPortalAccessBadge}
                    variant="warning"
                  />
                </span>
              ) : null}
            </div>
          );
        },
      },
      {
        key: "role",
        header: "Papel",
        headerHint: CM_HELP.sellerPortfolios.colMemberRole,
        render: (row) => (
          <CommercialStatusBadge
            label={
              row.role === "owner"
                ? PORTFOLIO_MEMBERS_CONTENT.roleOwner
                : PORTFOLIO_MEMBERS_CONTENT.roleMember
            }
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
                  disabled={busy || addingMembers}
                  onClick={() => onSetOwner(row.user_id)}
                  aria-label={CM_HELP.sellerPortfolios.setOwner}
                >
                  {busy ? "Atualizando…" : "Tornar responsável"}
                </CommercialActionButton>
              ) : null}
              {row.role !== "owner" || members.length > 1 ? (
                <CommercialActionButton
                  variant="ghost"
                  disabled={
                    busy ||
                    addingMembers ||
                    (row.role === "owner" && members.length <= 1)
                  }
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
    [addingMembers, busyMemberUserId, directoryLabelFor, members.length, onRemoveMember, onSetOwner],
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

      {isOrphan ? (
        <CommercialStateBanner>{PORTFOLIO_MEMBERS_CONTENT.orphanBanner}</CommercialStateBanner>
      ) : null}

      <CommercialSectionCard
        title={`Usuários (${members.length.toLocaleString("pt-BR")})`}
        subtitle={
          isOrphan
            ? PORTFOLIO_MEMBERS_CONTENT.sectionSubtitleOrphan
            : PORTFOLIO_MEMBERS_CONTENT.sectionSubtitleWithOwner
        }
        hint={CM_HELP.sellerPortfolios.members}
      >
        <div className="cm-portfolios-detail-block">
          <UserDirectoryPicker
            value={memberPicker}
            onChange={(users) => {
              setMemberPicker(users.filter((user) => !memberIds.has(user.id)));
            }}
            searchUsers={async (query, limit, signal) => {
              const hits = await searchDirectoryUsers(query, limit, signal);
              return hits.filter((hit) => !memberIds.has(hit.id));
            }}
            maxSelected={10}
            disabled={addingMembers}
            labels={{
              title: isOrphan
                ? "Adicionar responsável"
                : "Usuário com acesso ao Portal Comercial",
              hint: CM_HELP.sellerPortfolios.membersAdd,
              placeholder: isOrphan
                ? "Buscar responsável…"
                : "Buscar para adicionar…",
            }}
            renderOptionLeading={(user) => (
              <TaskUserChipAvatar
                userId={user.id}
                name={(user.name || "").trim() || user.email}
              />
            )}
            renderSelectedChip={({ user, label, disabled, onRemove }) => (
              <span className="delpi-ui-tag-chip">
                <TaskUserChipAvatar
                  userId={user.id}
                  name={(user.name || "").trim() || user.email}
                />
                <span>{label}</span>
                <button
                  type="button"
                  className="delpi-ui-tag-chip__remove"
                  disabled={disabled || addingMembers}
                  aria-label={`Remover ${label}`}
                  onClick={onRemove}
                >
                  <X size={14} aria-hidden="true" />
                </button>
              </span>
            )}
          />
          <div className="cm-portfolios-form__actions">
            <CommercialActionButton
              variant="primary"
              disabled={addingMembers || memberPicker.length === 0}
              onClick={() => onAddMembers(memberPicker.map((user) => user.id))}
              title={CM_HELP.sellerPortfolios.addSelectedMembers}
            >
              {addingMembers
                ? "Adicionando…"
                : memberPicker.length <= 1
                  ? "Adicionar selecionado"
                  : `Adicionar selecionados (${memberPicker.length})`}
            </CommercialActionButton>
          </div>

          <CommercialViewTransition
            transitionKey={`members-${portfolio.id}-${members.length}`}
            tone="panel"
          >
            {isOrphan ? (
              <CommercialEmptyState
                title={PORTFOLIO_MEMBERS_CONTENT.emptyTitle}
                message={PORTFOLIO_MEMBERS_CONTENT.emptyMessage}
              >
                <p className="cm-muted">{PORTFOLIO_MEMBERS_CONTENT.emptyCta}</p>
              </CommercialEmptyState>
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
            <CustomerSearchPicker
              value={customerPicker}
              onChange={(next) => {
                setCustomerPicker(
                  next.filter(
                    (item) => !linkedKeys.has(customerKey(item.code, item.store)),
                  ),
                );
              }}
              maxSelected={20}
              disabled={linkingCustomers}
              labels={{
                title: "Buscar no cadastro",
                hint: CM_HELP.sellerPortfolios.searchCustomers,
                placeholder: "Código ou nome do cliente",
              }}
              renderOptionLeading={(hit) => (
                <CustomerAvatar
                  code={hit.code}
                  store={hit.store}
                  name={(hit.name || "").trim() || hit.code}
                  size="sm"
                />
              )}
              renderSelectedChip={({ item, label, disabled, onRemove }) => (
                <span className="delpi-ui-tag-chip">
                  <CustomerAvatar
                    code={item.code}
                    store={item.store}
                    name={(item.name || "").trim() || item.code}
                    size="sm"
                  />
                  <span>{label}</span>
                  <button
                    type="button"
                    className="delpi-ui-tag-chip__remove"
                    disabled={disabled || linkingCustomers}
                    aria-label={`Remover ${label}`}
                    onClick={onRemove}
                  >
                    <X size={14} aria-hidden="true" />
                  </button>
                </span>
              )}
            />
            <div className="cm-portfolios-form__actions">
              <CommercialActionButton
                variant="primary"
                disabled={linkingCustomers || customerPicker.length === 0}
                onClick={() => onAddCustomers(customerPicker)}
              >
                {linkingCustomers
                  ? "Vinculando…"
                  : customerPicker.length <= 1
                    ? "Vincular selecionado"
                    : `Vincular selecionados (${customerPicker.length})`}
              </CommercialActionButton>
            </div>
          </section>

          <section className="cm-portfolios-detail-block" aria-label="Clientes vinculados">
            <h3 className="cm-section-subtitle">
              Na carteira ({linked.length.toLocaleString("pt-BR")})
            </h3>
            {linked.length > 0 ? (
              <CommercialDataListToolbar
                leading={
                  <NativeCheckboxControl
                    id={`portfolio-linked-select-all-${portfolio.id}`}
                    checked={allLinkedSelected}
                    onChange={(checked) => {
                      if (checked) {
                        setSelectedLinkedKeys(
                          new Set(
                            linked.map((row) =>
                              customerKey(row.customer_code, row.customer_store),
                            ),
                          ),
                        );
                      } else {
                        setSelectedLinkedKeys(new Set());
                      }
                    }}
                    label="Selecionar todos"
                    disabled={unlinkingCustomers}
                  />
                }
                actions={
                  <div className="cm-row-actions">
                    {selectedLinkedKeys.size > 0 ? (
                      <span className="cm-muted">
                        {selectedLinkedKeys.size.toLocaleString("pt-BR")} selecionado(s)
                      </span>
                    ) : null}
                    <CommercialActionButton
                      variant="ghost"
                      disabled={unlinkingCustomers || selectedLinkedKeys.size === 0}
                      onClick={() => {
                        const items = linked
                          .filter((row) =>
                            selectedLinkedKeys.has(
                              customerKey(row.customer_code, row.customer_store),
                            ),
                          )
                          .map((row) => ({
                            code: row.customer_code,
                            store: row.customer_store,
                          }));
                        onRemoveCustomers(items);
                      }}
                    >
                      {unlinkingCustomers
                        ? "Desvinculando…"
                        : "Desvincular selecionados"}
                    </CommercialActionButton>
                  </div>
                }
              />
            ) : null}
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
