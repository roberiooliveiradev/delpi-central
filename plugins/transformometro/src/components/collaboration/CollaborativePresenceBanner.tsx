import type { CollaborationPresencePayload } from "../../data/api/transformometroCollaborationApi";
import { COLLABORATION_SECTION_LABELS } from "../../constants/collaborationSections";

type Props = {
  presence: CollaborationPresencePayload | null;
  lockError?: string | null;
  realtimeNotice?: string | null;
  onDismissRealtimeNotice?: () => void;
};

export function CollaborativePresenceBanner({
  presence,
  lockError,
  realtimeNotice,
  onDismissRealtimeNotice,
}: Props) {
  if (!lockError && !realtimeNotice) {
    const editors = presence?.editors.filter((item) => item.lock_active) ?? [];
    const viewers = presence?.viewers ?? [];
    if (!editors.length && !viewers.length) {
      return null;
    }
  }

  const editors = presence?.editors.filter((item) => item.lock_active) ?? [];
  const viewers = presence?.viewers ?? [];

  return (
    <div className="tm-collab-banner" role="status">
      {lockError ? <p className="tm-collab-banner__alert">{lockError}</p> : null}
      {realtimeNotice ? (
        <p className="tm-collab-banner__line tm-collab-banner__line--info">
          {realtimeNotice}
          {onDismissRealtimeNotice ? (
            <button
              type="button"
              className="tm-collab-banner__dismiss"
              onClick={onDismissRealtimeNotice}
            >
              Ok
            </button>
          ) : null}
        </p>
      ) : null}
      {editors.length ? (
        <p className="tm-collab-banner__line">
          Editando:{" "}
          {editors
            .map(
              (item) =>
                `${item.user_name || "Usuário"} (${COLLABORATION_SECTION_LABELS[item.section_key] || item.section_key})`
            )
            .join(" · ")}
        </p>
      ) : null}
      {viewers.length ? (
        <p className="tm-collab-banner__line tm-collab-banner__line--muted">
          Visualizando:{" "}
          {viewers
            .map((item) => item.user_name || item.user_email || "Usuário")
            .filter((value, index, list) => list.indexOf(value) === index)
            .join(", ")}
        </p>
      ) : null}
    </div>
  );
}
