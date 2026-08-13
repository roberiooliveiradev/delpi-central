import { UserDirectoryPicker, type DirectoryUserOption } from "@delpi/plugin-ui/index";
import { Plus, RefreshCw, Trash2, UsersRound, X } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  addCommercialGroupMember,
  createCommercialGroup,
  deleteCommercialGroup,
  listCommercialGroups,
  removeCommercialGroupMember,
  type CommercialGroupDto,
} from "../../api/commercialGroupsApi";
import { searchDirectoryUsers } from "../../api/commercialPortfolioApi";
import {
  CommercialActionButton,
  CommercialEmptyState,
  CommercialLoadingCard,
  CommercialPageHero,
  CommercialPagePath,
  CommercialSectionCard,
  CommercialStateBanner,
  CommercialStatusBadge,
  CommercialTextField,
} from "../../app/commercialUi";
import { useCommercialConfirm } from "../../app/CommercialConfirmDialogProvider";
import { useCommercialFloatingNotice } from "../../app/CommercialFloatingNoticeProvider";
import { navigatePluginView } from "../../app/pluginNavigation";
import { useDirectoryUserLabels } from "../../app/useDirectoryUserLabels";
import { ADMINISTRATION_CONTENT } from "../../content/administration";
import { TaskUserChipAvatar } from "../my-day/TaskUserChipAvatar";
import { AdministrationSubNav } from "./AdministrationSubNav";

type AdministrationGroupsPageProps = {
  basePath: string;
};

export function AdministrationGroupsPage({ basePath }: AdministrationGroupsPageProps) {
  const copy = ADMINISTRATION_CONTENT.groups;
  const confirm = useCommercialConfirm();
  const { notifyError, notifySuccess } = useCommercialFloatingNotice();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [groups, setGroups] = useState<CommercialGroupDto[]>([]);
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [pickerByGroup, setPickerByGroup] = useState<Record<string, DirectoryUserOption[]>>({});
  const [newGroupName, setNewGroupName] = useState("");
  const [creating, setCreating] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);

  const memberUserIds = useMemo(
    () =>
      [...new Set(groups.flatMap((group) => group.members.map((member) => member.user_id)))],
    [groups],
  );
  const { byId, labelFor } = useDirectoryUserLabels(memberUserIds);

  const load = useCallback(
    async (mode: "initial" | "refresh" = "initial", signal?: AbortSignal) => {
      if (mode === "refresh") setRefreshing(true);
      else setLoading(true);
      setError(null);
      try {
        const items = await listCommercialGroups({ signal });
        if (signal?.aborted) return;
        setGroups(
          [...items].sort(
            (a, b) =>
              a.sort_order - b.sort_order || a.name.localeCompare(b.name, "pt-BR"),
          ),
        );
      } catch (err: unknown) {
        if (signal?.aborted) return;
        setError(err instanceof Error ? err.message : copy.loadError);
        setGroups([]);
      } finally {
        if (!signal?.aborted) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    },
    [copy.loadError],
  );

  useEffect(() => {
    const controller = new AbortController();
    void load("initial", controller.signal);
    return () => controller.abort();
  }, [load]);

  const upsertGroup = (next: CommercialGroupDto) => {
    setGroups((prev) => {
      const exists = prev.some((item) => item.id === next.id);
      const list = exists
        ? prev.map((item) => (item.id === next.id ? next : item))
        : [...prev, next];
      return list.sort(
        (a, b) =>
          a.sort_order - b.sort_order || a.name.localeCompare(b.name, "pt-BR"),
      );
    });
  };

  const openCreateForm = () => {
    setShowCreateForm(true);
  };

  const closeCreateForm = () => {
    setShowCreateForm(false);
    setNewGroupName("");
  };

  const onCreateGroup = async () => {
    const name = newGroupName.trim();
    if (!name) {
      notifyError(copy.createNameRequired);
      return;
    }
    setCreating(true);
    try {
      const created = await createCommercialGroup(name);
      upsertGroup(created);
      setNewGroupName("");
      setShowCreateForm(false);
      notifySuccess(copy.createSuccess);
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Falha ao criar grupo.");
    } finally {
      setCreating(false);
    }
  };

  const onDeleteGroup = async (group: CommercialGroupDto) => {
    const ok = await confirm({
      title: copy.deleteConfirmTitle,
      message: copy.deleteConfirmMessage.replace("{name}", group.name),
      confirmLabel: copy.deleteGroup,
      cancelLabel: "Cancelar",
      variant: "danger",
    });
    if (!ok) return;
    const key = `${group.id}:delete`;
    setBusyKey(key);
    try {
      await deleteCommercialGroup(group.id);
      setGroups((prev) => prev.filter((item) => item.id !== group.id));
      setPickerByGroup((prev) => {
        const next = { ...prev };
        delete next[group.id];
        return next;
      });
      notifySuccess(copy.deleteSuccess);
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Falha ao excluir grupo.");
    } finally {
      setBusyKey(null);
    }
  };

  const onAddMember = async (groupId: string, userId: string) => {
    const key = `${groupId}:add:${userId}`;
    setBusyKey(key);
    try {
      const updated = await addCommercialGroupMember(groupId, userId);
      upsertGroup(updated);
      setPickerByGroup((prev) => ({ ...prev, [groupId]: [] }));
      notifySuccess("Membro adicionado ao grupo.");
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Falha ao adicionar membro.");
    } finally {
      setBusyKey(null);
    }
  };

  const onRemoveMember = async (groupId: string, userId: string) => {
    const key = `${groupId}:remove:${userId}`;
    setBusyKey(key);
    try {
      const updated = await removeCommercialGroupMember(groupId, userId);
      upsertGroup(updated);
      notifySuccess("Membro removido do grupo.");
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Falha ao remover membro.");
    } finally {
      setBusyKey(null);
    }
  };

  const createFormCard = showCreateForm ? (
    <CommercialSectionCard
      title={copy.createFormTitle}
      actions={
        <CommercialActionButton
          variant="ghost"
          disabled={creating}
          onClick={closeCreateForm}
        >
          {copy.closeCreate}
        </CommercialActionButton>
      }
    >
      <div className="cm-row-actions cm-administration-groups__create">
        <CommercialTextField
          label={copy.createPlaceholder}
          value={newGroupName}
          onChange={setNewGroupName}
          disabled={creating}
        />
        <CommercialActionButton
          variant="primary"
          disabled={creating || !newGroupName.trim()}
          onClick={() => void onCreateGroup()}
        >
          <Plus size={16} strokeWidth={1.75} aria-hidden="true" />
          {creating ? copy.creating : copy.create}
        </CommercialActionButton>
      </div>
    </CommercialSectionCard>
  ) : null;

  return (
    <section className="cm-page-stack cm-administration-groups">
      <CommercialPagePath
        back={{
          label: "Portal Comercial",
          href: basePath,
          onNavigate: (event) => {
            event.preventDefault();
            navigatePluginView("home", { basePath });
          },
        }}
        items={[
          {
            id: "admin",
            label: ADMINISTRATION_CONTENT.breadcrumbRoot,
            href: `${basePath}/administration`,
            onNavigate: (event) => {
              event.preventDefault();
              navigatePluginView("administration", { basePath });
            },
          },
        ]}
        current={copy.navLabel}
      />

      <AdministrationSubNav basePath={basePath} active="groups" />

      <CommercialPageHero
        aria-label={copy.title}
        eyebrow={copy.eyebrow}
        title={copy.title}
        description={loading ? copy.loading : copy.description}
        actions={
          <>
            {!loading && groups.length > 0 && !showCreateForm ? (
              <CommercialActionButton variant="primary" onClick={openCreateForm}>
                <Plus size={16} strokeWidth={1.75} aria-hidden="true" />
                {copy.create}
              </CommercialActionButton>
            ) : null}
            <CommercialActionButton
              variant="ghost"
              onClick={() => void load("refresh")}
              disabled={loading || refreshing}
            >
              <RefreshCw size={16} strokeWidth={1.75} aria-hidden="true" />
              {copy.refresh}
            </CommercialActionButton>
          </>
        }
      />

      {error ? (
        <CommercialStateBanner variant="error">{error}</CommercialStateBanner>
      ) : null}

      {loading ? <CommercialLoadingCard title={copy.loading} /> : null}

      {!loading ? createFormCard : null}

      {!loading && groups.length === 0 && !showCreateForm ? (
        <CommercialEmptyState
          defaultTitle={copy.emptyTitle}
          defaultMessage={copy.emptyDescription}
        >
          <CommercialActionButton variant="primary" onClick={openCreateForm}>
            <UsersRound size={16} strokeWidth={1.75} aria-hidden="true" />
            {copy.create}
          </CommercialActionButton>
        </CommercialEmptyState>
      ) : null}

      {!loading
        ? groups.map((group) => {
            const memberIds = new Set(group.members.map((member) => member.user_id));
            const pickerValue = pickerByGroup[group.id] ?? [];
            const deleting = busyKey === `${group.id}:delete`;
            return (
              <CommercialSectionCard
                key={group.id}
                title={group.name}
                subtitle={copy.memberCount.replace(
                  "{count}",
                  String(group.member_count ?? group.members.length),
                )}
                actions={
                  <>
                    <CommercialStatusBadge
                      label={group.active ? "Ativo" : "Inativo"}
                      variant={group.active ? "success" : "neutral"}
                    />
                    <CommercialActionButton
                      variant="ghost"
                      disabled={Boolean(busyKey)}
                      onClick={() => void onDeleteGroup(group)}
                    >
                      <Trash2 size={16} strokeWidth={1.75} aria-hidden="true" />
                      {deleting ? copy.deleting : copy.deleteGroup}
                    </CommercialActionButton>
                  </>
                }
              >
                <div className="cm-portfolios-detail-block">
                  <UserDirectoryPicker
                    value={pickerValue}
                    onChange={(users) => {
                      const next = users.filter((user) => !memberIds.has(user.id));
                      setPickerByGroup((prev) => ({ ...prev, [group.id]: next }));
                      const candidate = next[0];
                      if (candidate) {
                        void onAddMember(group.id, candidate.id);
                      }
                    }}
                    searchUsers={async (query, limit, signal) => {
                      const hits = await searchDirectoryUsers(query, limit, signal);
                      return hits.filter((hit) => !memberIds.has(hit.id));
                    }}
                    maxSelected={1}
                    labels={{
                      title: copy.addMember,
                      placeholder: copy.addMemberPlaceholder,
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
                          disabled={disabled}
                          aria-label={`Remover ${label}`}
                          onClick={onRemove}
                        >
                          <X size={14} aria-hidden="true" />
                        </button>
                      </span>
                    )}
                  />

                  {group.members.length === 0 ? (
                    <p className="cm-muted">{copy.noMembers}</p>
                  ) : (
                    <ul className="cm-user-profile__permission-list">
                      {group.members.map((member) => {
                        const name = labelFor(
                          member.user_id,
                          byId[member.user_id]?.name ?? null,
                        );
                        const busy = busyKey === `${group.id}:remove:${member.user_id}`;
                        return (
                          <li key={member.user_id} className="cm-row-actions">
                            <TaskUserChipAvatar userId={member.user_id} name={name} />
                            <strong>{name}</strong>
                            <CommercialActionButton
                              variant="ghost"
                              disabled={busy || busyKey?.startsWith(`${group.id}:add:`)}
                              onClick={() => void onRemoveMember(group.id, member.user_id)}
                            >
                              {busy ? copy.removing : copy.removeMember}
                            </CommercialActionButton>
                          </li>
                        );
                      })}
                    </ul>
                  )}
                </div>
              </CommercialSectionCard>
            );
          })
        : null}
    </section>
  );
}
