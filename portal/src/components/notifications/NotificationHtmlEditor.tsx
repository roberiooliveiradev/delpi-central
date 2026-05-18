// src/components/notifications/NotificationHtmlEditor.tsx

import { useRef } from "react";

import { NotificationVariableToolbar } from "./NotificationVariableToolbar";

import "./NotificationHtmlEditor.css";

type NotificationHtmlEditorProps = {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  rows?: number;
};

export function NotificationHtmlEditor({
  value,
  onChange,
  disabled = false,
  rows = 8,
}: NotificationHtmlEditorProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  return (
    <div className="notification-html-editor">
      <NotificationVariableToolbar
        targetRef={textareaRef}
        value={value}
        onChange={onChange}
        disabled={disabled}
      />
      <textarea
        ref={textareaRef}
        className="notification-html-editor__area"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        rows={rows}
        disabled={disabled}
        placeholder="<p>Olá, <strong>{userName}</strong>!</p>"
      />
      <p className="notification-html-editor__hint">
        Variáveis do destinatário ({`{userName}`}, {`{userFullName}`}, {`{userEmail}`}) são
        substituídas automaticamente para cada pessoa no envio.
      </p>
    </div>
  );
}
