import { Plus, Search } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  createSequencingProfile,
  fetchMachineLoadWorkCenters,
  fetchSequencingBindings,
  fetchSequencingProfiles,
  setSequencingBinding,
  updateSequencingProfile,
} from "../api/ppcApi";
import { httpErrorStatus } from "../api/httpClient";
import { PpcWorkspaceHeader } from "../components/PpcWorkspaceHeader";
import { usePpcConfirm } from "../components/PpcConfirmDialogProvider";
import {
  SequencingBindingsPanel,
  type WorkCenterOption,
} from "../components/SequencingBindingsPanel";
import {
  SequencingProfileEditor,
  type ProfileDraft,
} from "../components/SequencingProfileEditor";
import { copy } from "../content/copy";
import { helpTooltips } from "../content/helpTooltips";
import type { PpcBranch, SequencingBinding, SequencingProfile } from "../types";
import {
  applyBindingResult,
  buildCriteriaPayload,
  canManageSequencingProfiles,
  statusLabel,
} from "../utils/sequencingProfiles";

type Props = {
  branch: PpcBranch;
  permissions?: string[];
  isSuperadmin?: boolean;
};

type LoadState = {
  profiles: SequencingProfile[];
  bindings: SequencingBinding[];
  workCenters: WorkCenterOption[];
};

export function SequencingProfilesPage({ branch, permissions, isSuperadmin }: Props) {
  const confirm = usePpcConfirm();
  const texts = copy.sequencingProfiles;
  const [state, setState] = useState<LoadState>({
    profiles: [],
    bindings: [],
    workCenters: [],
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  // Permissão efetiva: o backend continua sendo a autoridade, mas a tela já
  // nasce somente leitura para quem não tem o grant — sem depender do 403.
  const canManage = canManageSequencingProfiles(permissions, isSuperadmin);
  const [forbidden, setForbidden] = useState(false);
  const readOnly = !canManage || forbidden;
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [selectedId, setSelectedId] = useState<string | "new" | null>(null);
  const [editorDirty, setEditorDirty] = useState(false);
  const [reloadToken, setReloadToken] = useState(0);
  const selectedIdRef = useRef(selectedId);

  useEffect(() => {
    selectedIdRef.current = selectedId;
  }, [selectedId]);

  const reload = useCallback(() => setReloadToken((v) => v + 1), []);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    Promise.all([
      fetchSequencingProfiles({ branch, signal: controller.signal }),
      fetchSequencingBindings({ branch, signal: controller.signal }),
      fetchMachineLoadWorkCenters({ branch, signal: controller.signal }).catch(() => null),
    ])
      .then(([profiles, bindings, machineLoad]) => {
        if (controller.signal.aborted) return;
        setState({
          profiles: (profiles.items ?? []).filter(
            (profile) =>
              profile.origin_branch == null || profile.origin_branch === branch,
          ),
          bindings: bindings.items ?? [],
          workCenters:
            machineLoad?.items.map((center) => ({
              work_center: center.work_center,
              work_center_name: center.work_center_name,
            })) ?? [],
        });
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : texts.loadError);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [branch, reloadToken, texts.loadError]);

  const handleError = useCallback(
    (err: unknown, fallback: string) => {
      const status = httpErrorStatus(err);
      if (status === 403) {
        setForbidden(true);
        setError(texts.forbidden);
        return;
      }
      if (status === 409) {
        setError(texts.conflict);
        return;
      }
      if (status === 404) {
        setError(texts.notFound);
        reload();
        return;
      }
      setError(err instanceof Error ? err.message : fallback);
    },
    [reload, texts],
  );

  const filtered = useMemo(() => {
    const text = query.trim().toLowerCase();
    return state.profiles.filter((profile) => {
      if (statusFilter !== "all" && profile.status !== statusFilter) return false;
      if (!text) return true;
      return (
        profile.name.toLowerCase().includes(text) ||
        (profile.description ?? "").toLowerCase().includes(text)
      );
    });
  }, [state.profiles, query, statusFilter]);

  const selected: SequencingProfile | null = useMemo(() => {
    if (!selectedId || selectedId === "new") return null;
    return state.profiles.find((profile) => profile.id === selectedId) ?? null;
  }, [state.profiles, selectedId]);

  const boundCenters = useMemo(() => {
    if (!selected) return [];
    return state.bindings
      .filter((binding) => binding.profile_id === selected.id)
      .map((binding) => binding.work_center);
  }, [state.bindings, selected]);

  const selectProfile = useCallback(
    async (id: string | "new" | null) => {
      if (id === selectedIdRef.current) return;
      if (editorDirty) {
        const okLeave = await confirm({
          title: texts.unsavedTitle,
          message: texts.unsavedMessage,
          confirmLabel: texts.unsavedDiscard,
          variant: "danger",
        });
        if (!okLeave) return;
      }
      setSelectedId(id);
      setEditorDirty(false);
      setError(null);
      setNotice(null);
    },
    [confirm, editorDirty, texts],
  );

  const saveProfile = useCallback(
    async (draft: ProfileDraft) => {
      setSaving(true);
      setError(null);
      setNotice(null);
      try {
        const criteria = buildCriteriaPayload(draft.criteria);
        if (!selected) {
          const created = await createSequencingProfile({
            branch,
            name: draft.name,
            description: draft.description || null,
            criteria,
          });
          setSelectedId(created.id);
          setNotice(texts.created);
        } else {
          await updateSequencingProfile({
            branch,
            profileId: selected.id,
            expectedRevision: selected.revision,
            name: draft.name,
            description: draft.description || null,
            status: selected.status,
            criteria,
          });
          setNotice(texts.saved);
        }
        setEditorDirty(false);
        reload();
      } catch (err) {
        handleError(err, texts.saveError);
      } finally {
        setSaving(false);
      }
    },
    [branch, handleError, reload, selected, texts],
  );

  const changeStatus = useCallback(
    async (status: "draft" | "active" | "archived") => {
      if (!selected) return;
      if (status === "archived") {
        const okArchive = await confirm({
          title: texts.archiveTitle,
          message: texts.archiveMessage(selected.name, boundCenters),
          confirmLabel: texts.archiveConfirm,
          variant: "danger",
        });
        if (!okArchive) return;
      }
      setSaving(true);
      setError(null);
      setNotice(null);
      try {
        await updateSequencingProfile({
          branch,
          profileId: selected.id,
          expectedRevision: selected.revision,
          name: selected.name,
          description: selected.description,
          status,
          criteria: selected.criteria,
        });
        setNotice(
          status === "active"
            ? texts.activated
            : status === "archived"
              ? texts.archived
              : texts.backToDraft,
        );
        reload();
      } catch (err) {
        handleError(err, texts.saveError);
      } finally {
        setSaving(false);
      }
    },
    [boundCenters, branch, confirm, handleError, reload, selected, texts],
  );

  const bind = useCallback(
    async (workCenter: string, profileId: string | null) => {
      if (profileId) {
        const previous = state.bindings.find(
          (binding) => binding.work_center === workCenter,
        );
        if (previous && previous.profile_id !== profileId) {
          const okReplace = await confirm({
            title: texts.replaceTitle,
            message: texts.replaceMessage(workCenter),
            confirmLabel: texts.replaceConfirm,
          });
          if (!okReplace) return;
        }
      } else {
        const okUnbind = await confirm({
          title: texts.unbindTitle,
          message: texts.unbindMessage(workCenter),
          confirmLabel: texts.unbindConfirm,
          variant: "danger",
        });
        if (!okUnbind) return;
      }
      setSaving(true);
      setError(null);
      setNotice(null);
      try {
        const result = await setSequencingBinding({ branch, workCenter, profileId });
        // Atualização local do vínculo — sem recarregar perfis, para não
        // descartar um rascunho não salvo aberto no editor.
        setState((current) => ({
          ...current,
          bindings: applyBindingResult(current.bindings, result),
          workCenters: current.workCenters.some(
            (center) => center.work_center === workCenter,
          )
            ? current.workCenters
            : [
                ...current.workCenters,
                { work_center: workCenter, work_center_name: workCenter },
              ],
        }));
        setNotice(profileId ? texts.bound : texts.unbound);
      } catch (err) {
        handleError(err, texts.bindError);
      } finally {
        setSaving(false);
      }
    },
    [branch, confirm, handleError, state.bindings, texts],
  );

  return (
    <div className="ppc-page-stack seq-page">
      <PpcWorkspaceHeader
        title={texts.title}
        subtitle={texts.subtitle}
        titleHint={helpTooltips.sequencingProfiles}
        branch={branch}
        subpluginId="sequencing-profiles"
      />

      {error ? (
        <div className="ppc-state ppc-state--error" role="alert">
          {error}
          {error === texts.conflict ? (
            <button type="button" className="seq-btn" onClick={reload}>
              {texts.reload}
            </button>
          ) : null}
        </div>
      ) : null}
      {notice ? (
        <div className="ppc-state seq-state--ok" role="status">
          {notice}
        </div>
      ) : null}

      {loading ? (
        <div className="ppc-state">{texts.loading}</div>
      ) : (
        <div className="seq-page__grid">
          <aside className="seq-card seq-list" aria-label={texts.listTitle}>
            <header className="seq-card__head">
              <h3>{texts.listTitle}</h3>
              <button
                type="button"
                className="seq-btn seq-btn--primary"
                disabled={readOnly || saving}
                onClick={() => void selectProfile("new")}
              >
                <Plus size={15} aria-hidden /> {texts.newProfile}
              </button>
            </header>
            <div className="seq-list__filters">
              <label className="seq-list__search">
                <Search size={15} aria-hidden />
                <input
                  type="search"
                  className="seq-input"
                  placeholder={texts.searchPlaceholder}
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                />
              </label>
              <select
                className="seq-input seq-list__status"
                value={statusFilter}
                aria-label={texts.statusFilterAria}
                onChange={(event) => setStatusFilter(event.target.value)}
              >
                <option value="all">{texts.filterAll}</option>
                <option value="active">{statusLabel("active")}</option>
                <option value="draft">{statusLabel("draft")}</option>
                <option value="archived">{statusLabel("archived")}</option>
              </select>
            </div>
            {filtered.length === 0 ? (
              <p className="ppc-state">{texts.empty}</p>
            ) : (
              <ul className="seq-list__items">
                {filtered.map((profile) => {
                  const inUse = state.bindings.some(
                    (binding) => binding.profile_id === profile.id,
                  );
                  const foreign =
                    profile.origin_branch && profile.origin_branch !== branch;
                  return (
                    <li key={profile.id}>
                      <button
                        type="button"
                        className={`seq-list__item${
                          selectedId === profile.id ? " seq-list__item--active" : ""
                        }`}
                        onClick={() => void selectProfile(profile.id)}
                      >
                        <span className="seq-list__name">{profile.name}</span>
                        <span className="seq-list__meta">
                          <span className={`seq-status seq-status--${profile.status}`}>
                            {statusLabel(profile.status)}
                          </span>
                          {inUse ? (
                            <span className="seq-list__inuse">{texts.inUse}</span>
                          ) : null}
                          {foreign ? (
                            <span className="seq-list__foreign">
                              {texts.otherBranch(profile.origin_branch ?? "")}
                            </span>
                          ) : null}
                        </span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </aside>

          <div className="seq-page__main">
            {selectedId === null ? (
              <section className="seq-card seq-card--empty">
                <p className="ppc-state">{texts.selectHint}</p>
              </section>
            ) : (
              <SequencingProfileEditor
                key={selected ? selected.id : "new"}
                profile={selected}
                boundCenters={boundCenters}
                readOnly={readOnly || Boolean(
                  selected?.origin_branch && selected.origin_branch !== branch,
                )}
                saving={saving}
                onSaveDraft={(draft) => void saveProfile(draft)}
                onChangeStatus={(status) => void changeStatus(status)}
                onDirtyChange={setEditorDirty}
              />
            )}

            <SequencingBindingsPanel
              workCenters={state.workCenters}
              bindings={state.bindings}
              profiles={state.profiles}
              branch={branch}
              readOnly={readOnly}
              saving={saving}
              onBind={(center, profileId) => void bind(center, profileId)}
            />
          </div>
        </div>
      )}
      <p className="seq-page__footer">{texts.footerNote}</p>
    </div>
  );
}
