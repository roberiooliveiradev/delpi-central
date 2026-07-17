import { useEffect, useId, useState } from "react";

import { ActionButton } from "../actions/ActionButton";
import { ModalShell, type ModalShellClassNames } from "../feedback/ModalShell";
import { NativeTextControl } from "../forms/NativeTextControl";
import { FieldLabel } from "../help/FieldLabel";
import { RICH_TEXT_LABELS } from "./richTextLabels";

/** Classes canônicas do kit — CSS em `styles/modal-shell.css`. */
const LINK_MODAL_CLASSES: ModalShellClassNames = {
  overlay: "delpi-ui-modal-overlay",
  dialog: "delpi-ui-modal delpi-ui-modal--sm",
  header: "delpi-ui-modal__header",
  title: "delpi-ui-modal__title",
  closeButton: "delpi-ui-modal__close",
  body: "delpi-ui-modal__body",
  footer: "delpi-ui-modal__footer",
};

export type RichTextLinkDialogProps = {
  open: boolean;
  /** URL pré-preenchida (edição de link existente). */
  initialUrl?: string;
  editing?: boolean;
  portalScopeClassName?: string;
  onSubmit: (url: string) => void;
  onClose: () => void;
};

/** Diálogo de inserção/edição de link do RichTextEditor (sem prompt do navegador). */
export function RichTextLinkDialog({
  open,
  initialUrl = "",
  editing = false,
  portalScopeClassName,
  onSubmit,
  onClose,
}: RichTextLinkDialogProps) {
  const [url, setUrl] = useState(initialUrl);
  const inputId = useId();

  useEffect(() => {
    if (open) setUrl(initialUrl);
  }, [open, initialUrl]);

  const trimmed = url.trim();

  function submit() {
    if (!trimmed) return;
    onSubmit(trimmed);
  }

  return (
    <ModalShell
      open={open}
      title={editing ? RICH_TEXT_LABELS.linkDialogEditTitle : RICH_TEXT_LABELS.linkDialogTitle}
      onClose={onClose}
      classNames={LINK_MODAL_CLASSES}
      portalScopeClassName={portalScopeClassName}
      initialFocusSelector="input"
      footer={
        <>
          <ActionButton onClick={onClose}>{RICH_TEXT_LABELS.linkCancel}</ActionButton>
          <ActionButton variant="primary" disabled={!trimmed} onClick={submit}>
            {RICH_TEXT_LABELS.linkApply}
          </ActionButton>
        </>
      }
    >
      <FieldLabel label={RICH_TEXT_LABELS.linkUrlLabel} htmlFor={inputId} />
      <NativeTextControl
        id={inputId}
        type="url"
        value={url}
        onChange={setUrl}
        placeholder={RICH_TEXT_LABELS.linkUrlPlaceholder}
        onKeyDown={(event) => {
          if (event.key === "Enter") {
            event.preventDefault();
            submit();
          }
        }}
      />
    </ModalShell>
  );
}
