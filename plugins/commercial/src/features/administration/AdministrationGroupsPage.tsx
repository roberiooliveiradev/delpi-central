import { EmptyState, UserDirectoryPicker, type DirectoryUserOption } from "@delpi/plugin-ui/index";
import { RefreshCw, UsersRound, X } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  addCommercialGroupMember,
  listCommercialGroups,
  removeCommercialGroupMember,
  type CommercialGroupDto,
} from "../../api/commercialGroupsApi";
import { searchDirectoryUsers } from "../../api/commercialPortfolioApi";
import {
  cmEmptyStateClassNames,
  CommercialActionButton,
  CommercialLoadingCard,
  CommercialPageHero,
  CommercialPagePath,
  CommercialSectionCard,
  CommercialStateBanner,
  CommercialStatusBadge,
} from "../../app/commercialUi";
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
  const { notifyError, notifySuccess } = useCommercialFloatingNotice();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [groups, setGroups] = useState<CommercialGroupDto[]>([]);
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [pickerByGroup, setPickerByGroup] = useState<Record<string, DirectoryUserOption[]>>({});

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
    setGroups((prev) =>
      prev
        .map((item) => (item.id === next.id ? next : item))
        .sort(
          (a, b) =>
            a.sort_order - b.sort_order || a.name.localeCompare(b.name, "pt-BR"),
        ),
    );
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
          <CommercialActionButton
            variant="ghost"
            onClick={() => void load("refresh")}
            disabled={loading || refreshing}
          >
            <RefreshCw size={16} strokeWidth={1.75} aria-hidden="true" />
            {copy.refresh}
          </CommercialActionButton>
        }
      />

      {error ? (
        <CommercialStateBanner variant="error">{error}</CommercialStateBanner>
      ) : null}

      {loading ? <CommercialLoadingCard title={copy.loading} /> : null}

      {!loading && groups.length === 0 ? (
        <EmptyState
          classNames={{ ...cmEmptyStateClassNames, withTitle: true }}
          defaultTitle={copy.emptyTitle}
          defaultMessage={copy.emptyDescription}
        >
          <CommercialActionButton
            variant="primary"
            onClick={() => navigatePluginView("administration_team", { basePath })}
          >
            <UsersRound size={16} strokeWidth={1.75} aria-hidden="true" />
            {ADMINISTRATION_CONTENT.team.navLabel}
          </CommercialActionButton>
        </EmptyState>
      ) : null}

      {!loading
        ? groups.map((group) => {
            const memberIds = new Set(group.members.map((member) => member.user_id));
            const pickerValue = pickerByGroup[group.id] ?? [];
            return (
              <CommercialSectionCard
                key={group.id}
                title={group.name}
                subtitle={copy.memberCount.replace(
                  "{count}",
                  String(group.member_count ?? group.members.length),
                )}
                actions={
                  <CommercialStatusBadge
                    label={group.active ? "Ativo" : "Inativo"}
                    variant={group.active ? "success" : "neutral"}
                  />
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
