import { useEffect, useId, useRef, useState } from "react";

import { HostContainedDialog } from "./ui/Modal";

type Props = {
  open: boolean;
  initialName: string;
  busy?: boolean;
  onClose: () => void;
  onConfirm: (name: string) => void | Promise<void>;
};

const MAX_NAME = 200;

/** Diálogo para renomear programação (home, ribbon e top bar). */
export function PlaylistRenameDialog({
  open,
  initialName,
  busy = false,
  onClose,
  onConfirm,
}: Props) {
  const inputId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const [draft, setDraft] = useState(initialName);

  useEffect(() => {
    if (!open) return;
    setDraft(initialName);
    const timer = window.setTimeout(() => {
      const el = inputRef.current;
      if (!el) return;
      el.focus();
      el.select();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [open, initialName]);

  const trimmed = draft.trim();
  const canSave = trimmed.length > 0 && trimmed !== initialName.trim() && !busy;

  async function submit() {
    if (!canSave) return;
    await onConfirm(trimmed.slice(0, MAX_NAME));
  }

  return (
    <HostContainedDialog
      open={open}
      title="Renomear programação"
      onClose={onClose}
      className="td-modal--confirm"
      footer={
        <div className="td-modal-actions td-modal-actions--end">
          <button type="button" className="td-btn td-btn--ghost" disabled={busy} onClick={onClose}>
            Cancelar
          </button>
          <button
            type="button"
            className="td-btn td-btn--primary"
            disabled={!canSave}
            onClick={() => void submit()}
          >
            {busy ? "Salvando…" : "Salvar"}
          </button>
        </div>
      }
    >
      <label className="td-playlist-rename" htmlFor={inputId}>
        <span className="td-playlist-rename__label">Nome</span>
        <input
          ref={inputRef}
          id={inputId}
          type="text"
          maxLength={MAX_NAME}
          value={draft}
          disabled={busy}
          autoComplete="off"
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              void submit();
            }
            if (event.key === "Escape") {
              event.preventDefault();
              onClose();
            }
          }}
        />
      </label>
    </HostContainedDialog>
  );
}
