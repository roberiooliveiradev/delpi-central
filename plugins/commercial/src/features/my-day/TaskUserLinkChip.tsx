import { useEffect, useState, type ReactNode } from "react";

import {
  getUserProfile,
  userProfilePhotoAbsoluteUrl,
} from "../../api/userProfileApi";
import { httpGetBlob } from "../../api/httpClient";
import { CommercialAvatar } from "../../app/commercialUi";

type TaskUserLinkChipProps = {
  userId: string;
  /** Nome/fallback enquanto o perfil carrega (pode vir "Nome · e-mail mascarado"). */
  fallbackLabel: string;
  onOpen: () => void;
};

/** Extrai só o nome do rótulo do diretório (ignora e-mail mascarado). */
function displayNameFromFallback(label: string): string {
  const trimmed = label.trim();
  if (!trimmed) return "";
  for (const sep of [" · ", " - "]) {
    const idx = trimmed.indexOf(sep);
    if (idx > 0) return trimmed.slice(0, idx).trim();
  }
  return trimmed;
}

/**
 * Badge de usuário na tarefa: avatar + nome + e-mail; clique abre o perfil.
 */
export function TaskUserLinkChip({
  userId,
  fallbackLabel,
  onOpen,
}: TaskUserLinkChipProps): ReactNode {
  const [name, setName] = useState(() => displayNameFromFallback(fallbackLabel));
  const [email, setEmail] = useState<string | null>(null);
  const [photoUrl, setPhotoUrl] = useState<string | null>(null);

  useEffect(() => {
    setName(displayNameFromFallback(fallbackLabel));
  }, [fallbackLabel]);

  useEffect(() => {
    const uid = userId.trim();
    if (!uid) {
      setPhotoUrl(null);
      setEmail(null);
      return;
    }
    const controller = new AbortController();
    let created: string | null = null;
    void (async () => {
      try {
        const profile = await getUserProfile(uid, controller.signal);
        if (controller.signal.aborted) return;
        const resolvedName = (profile.name || "").trim();
        if (resolvedName) setName(resolvedName);
        const resolvedEmail = (profile.email || "").trim();
        setEmail(resolvedEmail || null);
        if (!profile.has_photo) {
          setPhotoUrl(null);
          return;
        }
        const blob = await httpGetBlob(userProfilePhotoAbsoluteUrl(uid), {
          signal: controller.signal,
        });
        if (controller.signal.aborted) return;
        created = URL.createObjectURL(blob);
        setPhotoUrl(created);
      } catch {
        if (!controller.signal.aborted) {
          setPhotoUrl(null);
        }
      }
    })();
    return () => {
      controller.abort();
      if (created) URL.revokeObjectURL(created);
    };
  }, [userId]);

  return (
    <button
      type="button"
      className="delpi-ui-tag-chip cm-task-link-chip"
      onClick={onOpen}
    >
      <span className="cm-task-link-chip__avatar" aria-hidden>
        <CommercialAvatar
          name={name}
          colorKey={userId}
          size="sm"
          src={photoUrl}
          previewable={false}
          portalScopeClassName="dashboard-commercial"
        />
      </span>
      <span className="cm-task-link-chip__text">
        <span className="cm-task-link-chip__name">{name}</span>
        {email ? (
          <span className="cm-task-link-chip__subtitle">{email}</span>
        ) : null}
      </span>
    </button>
  );
}
