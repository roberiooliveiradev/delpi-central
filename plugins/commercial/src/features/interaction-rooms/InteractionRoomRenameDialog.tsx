import { useEffect, useState } from "react";

import {
  CommercialActionButton,
  CommercialHostDialog,
  CommercialTextField,
} from "../../app/commercialUi";
import { INTERACTION_ROOMS_CONTENT } from "../../content/interactionRoomsContent";

type Props = {
  open: boolean;
  busy?: boolean;
  initialTitle: string;
  onClose: () => void;
  onSave: (title: string) => void;
};

export function InteractionRoomRenameDialog({
  open,
  busy = false,
  initialTitle,
  onClose,
  onSave,
}: Props) {
  const content = INTERACTION_ROOMS_CONTENT;
  const [draft, setDraft] = useState(initialTitle);

  useEffect(() => {
    if (!open) return;
    setDraft(initialTitle);
  }, [open, initialTitle]);

  const trimmed = draft.trim();
  const canSave = trimmed.length > 0 && trimmed !== initialTitle.trim() && !busy;

  return (
    <CommercialHostDialog
      open={open}
      title={content.renameRoomDialogTitle}
      onClose={() => {
        if (busy) return;
        onClose();
      }}
      footer={
        <div className="cm-room-rename-dialog__actions">
          <CommercialActionButton
            variant="ghost"
            disabled={busy}
            onClick={onClose}
          >
            {content.renameRoomCancelLabel}
          </CommercialActionButton>
          <CommercialActionButton
            variant="primary"
            disabled={!canSave}
            onClick={() => onSave(trimmed)}
          >
            {content.renameRoomConfirmLabel}
          </CommercialActionButton>
        </div>
      }
    >
      <CommercialTextField
        label={content.renameRoomFieldLabel}
        value={draft}
        onChange={setDraft}
        disabled={busy}
      />
    </CommercialHostDialog>
  );
}
