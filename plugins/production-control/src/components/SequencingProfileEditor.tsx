import { useEffect, useMemo, useState } from "react";

import { copy } from "../content/copy";
import type { SequencingProfile } from "../types";
import {
  criteriaFromProfile,
  statusLabel,
  validateCriteria,
  type CriteriaEditorItem,
} from "../utils/sequencingProfiles";
import { SequencingCriteriaEditor } from "./SequencingCriteriaEditor";

export type ProfileDraft = {
  name: string;
  description: string;
  criteria: CriteriaEditorItem[];
};

type Props = {
  /** Perfil selecionado; `null` = novo perfil em rascunho. */
  profile: SequencingProfile | null;
  boundCenters: string[];
  readOnly: boolean;
  saving: boolean;
  onSaveDraft: (draft: ProfileDraft) => void;
  onChangeStatus: (status: "draft" | "active" | "archived") => void;
  onDirtyChange?: (dirty: boolean) => void;
};

export function SequencingProfileEditor({
  profile,
  boundCenters,
  readOnly,
  saving,
  onSaveDraft,
  onChangeStatus,
  onDirtyChange,
}: Props) {
  const texts = copy.sequencingProfiles.editor;
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [criteria, setCriteria] = useState<CriteriaEditorItem[]>(() =>
    criteriaFromProfile(null),
  );
  const [baseline, setBaseline] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const nextName = profile?.name ?? "";
    const nextDescription = profile?.description ?? "";
    const nextCriteria = criteriaFromProfile(profile);
    setName(nextName);
    setDescription(nextDescription);
    setCriteria(nextCriteria);
    setError(null);
    setBaseline(JSON.stringify([nextName, nextDescription, nextCriteria]));
  }, [profile]);

  const dirty = useMemo(
    () => JSON.stringify([name, description, criteria]) !== baseline,
    [name, description, criteria, baseline],
  );

  useEffect(() => {
    onDirtyChange?.(dirty);
  }, [dirty, onDirtyChange]);

  const archived = profile?.status === "archived";
  const disabled = readOnly || saving || archived;

  const handleSave = () => {
    if (!name.trim()) {
      setError(texts.nameRequired);
      return;
    }
    const criteriaError = validateCriteria(criteria);
    if (criteriaError) {
      setError(criteriaError);
      return;
    }
    setError(null);
    onSaveDraft({ name: name.trim(), description: description.trim(), criteria });
  };

  return (
    <section className="seq-card" aria-label={texts.title}>
      <header className="seq-card__head">
        <h3>{profile ? texts.titleEdit : texts.titleNew}</h3>
        {profile ? (
          <span className={`seq-status seq-status--${profile.status}`}>
            {statusLabel(profile.status)} · rev. {profile.revision}
          </span>
        ) : (
          <span className="seq-status seq-status--draft">{texts.newDraft}</span>
        )}
      </header>

      {boundCenters.length > 0 ? (
        <p className="seq-card__bound" role="note">
          {texts.boundTo(boundCenters.join(", "))}
        </p>
      ) : null}

      <div className="seq-card__fields">
        <label className="seq-field">
          <span>{texts.nameLabel}</span>
          <input
            className="seq-input"
            type="text"
            value={name}
            maxLength={120}
            disabled={disabled}
            placeholder={texts.namePlaceholder}
            onChange={(event) => setName(event.target.value)}
          />
        </label>
        <label className="seq-field">
          <span>{texts.descriptionLabel}</span>
          <textarea
            className="seq-input"
            rows={2}
            value={description}
            maxLength={500}
            disabled={disabled}
            placeholder={texts.descriptionPlaceholder}
            onChange={(event) => setDescription(event.target.value)}
          />
        </label>
      </div>

      <SequencingCriteriaEditor
        items={criteria}
        disabled={disabled}
        onChange={setCriteria}
      />

      {error ? (
        <p className="seq-card__error" role="alert">
          {error}
        </p>
      ) : null}
      {archived ? (
        <p className="seq-card__hint">{texts.archivedHint}</p>
      ) : null}
      {readOnly && !archived ? (
        <p className="seq-card__hint">{texts.readOnlyHint}</p>
      ) : null}

      <footer className="seq-card__actions">
        <button
          type="button"
          className="seq-btn"
          disabled={disabled || !dirty}
          onClick={handleSave}
        >
          {saving ? texts.saving : profile ? texts.save : texts.create}
        </button>
        {profile?.status === "draft" ? (
          <button
            type="button"
            className="seq-btn seq-btn--primary"
            disabled={disabled || dirty}
            title={dirty ? texts.activateBlockedDirty : undefined}
            onClick={() => onChangeStatus("active")}
          >
            {texts.activate}
          </button>
        ) : null}
        {profile?.status === "active" ? (
          <button
            type="button"
            className="seq-btn seq-btn--ghost"
            disabled={disabled || dirty}
            onClick={() => onChangeStatus("draft")}
          >
            {texts.toDraft}
          </button>
        ) : null}
        {profile && profile.status !== "archived" ? (
          <button
            type="button"
            className="seq-btn seq-btn--danger"
            disabled={disabled || dirty}
            onClick={() => onChangeStatus("archived")}
          >
            {texts.archive}
          </button>
        ) : null}
      </footer>
    </section>
  );
}
