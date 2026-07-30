import {
  EditorChromeNotice,
  EditorChromeNotices,
} from "@delpi/plugin-ui/index";

import type { CollaborationPresencePayload } from "../../data/api/transformometroCollaborationApi";
import { COLLABORATION_SECTION_LABELS } from "../../constants/collaborationSections";

type Props = {
  presence: CollaborationPresencePayload | null;
  lockError?: string | null;
  realtimeNotice?: string | null;
  onDismissRealtimeNotice?: () => void;
  /** Em páginas imersivas (ex.: editor BPMN), omitir «Visualizando» libera altura. */
  showViewers?: boolean;
  /**
   * `stack` — wrapper próprio (páginas de detalhe).
   * `items` — só os avisos, para encaixar em `EditorChrome.notices`.
   */
  layout?: "stack" | "items";
};

export function CollaborativePresenceBanner({
  presence,
  lockError,
  realtimeNotice,
  onDismissRealtimeNotice,
  showViewers = true,
  layout = "stack",
}: Props) {
  const editors = presence?.editors.filter((item) => item.lock_active) ?? [];
  const viewers = showViewers ? presence?.viewers ?? [] : [];

  if (!lockError && !realtimeNotice && !editors.length && !viewers.length) {
    return null;
  }

  const items = (
    <>
      {lockError ? (
        <EditorChromeNotice tone="danger">{lockError}</EditorChromeNotice>
      ) : null}
      {realtimeNotice ? (
        <EditorChromeNotice
          tone="info"
          actionLabel={onDismissRealtimeNotice ? "Ok" : undefined}
          onAction={onDismissRealtimeNotice}
        >
          {realtimeNotice}
        </EditorChromeNotice>
      ) : null}
      {editors.length ? (
        <EditorChromeNotice tone="info">
          Editando:{" "}
          {editors
            .map(
              (item) =>
                `${item.user_name || "Usuário"} (${COLLABORATION_SECTION_LABELS[item.section_key] || item.section_key})`,
            )
            .join(" · ")}
        </EditorChromeNotice>
      ) : null}
      {viewers.length ? (
        <EditorChromeNotice tone="neutral">
          Visualizando:{" "}
          {viewers
            .map((item) => item.user_name || item.user_email || "Usuário")
            .filter((value, index, list) => list.indexOf(value) === index)
            .join(", ")}
        </EditorChromeNotice>
      ) : null}
    </>
  );

  if (layout === "items") {
    return items;
  }

  return (
    <EditorChromeNotices aria-label="Presença colaborativa">{items}</EditorChromeNotices>
  );
}
