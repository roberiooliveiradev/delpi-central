// src/components/notifications/NotificationHtmlEditor.tsx

import { useMemo, useRef, useState } from "react";

import { NotificationVariableToolbar } from "./NotificationVariableToolbar";
import { substituteNotificationVariables } from "./notificationHtmlPreview";

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
  const [showPreview, setShowPreview] = useState(true);

  const previewHtml = useMemo(() => substituteNotificationVariables(value), [value]);

  return (
    <div className="notification-html-editor">
      <NotificationVariableToolbar
        targetRef={textareaRef}
        value={value}
        onChange={onChange}
        disabled={disabled}
      />

      <div className="notification-html-editor__toolbar">
        <span className="notification-html-editor__toolbar-label">Editor HTML</span>
        <label className="notification-html-editor__preview-toggle">
          <input
            type="checkbox"
            checked={showPreview}
            onChange={(event) => setShowPreview(event.target.checked)}
            disabled={disabled}
          />
          Mostrar pré-visualização
        </label>
      </div>

      <div
        className={
          showPreview
            ? "notification-html-editor__split"
            : "notification-html-editor__split notification-html-editor__split--editor-only"
        }
      >
        <textarea
          ref={textareaRef}
          className="notification-html-editor__area"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          rows={rows}
          disabled={disabled}
          placeholder="<p>Olá, <strong>{userName}</strong>!</p>"
          aria-label="Conteúdo HTML da notificação"
        />

        {showPreview ? (
          <section className="notification-html-editor__preview" aria-label="Pré-visualização">
            <p className="notification-html-editor__preview-title">Pré-visualização</p>
            {previewHtml.trim() ? (
              <div
                className="notification-html-editor__preview-body"
                dangerouslySetInnerHTML={{ __html: previewHtml }}
              />
            ) : (
              <p className="notification-html-editor__preview-empty">
                O preview aparece aqui conforme você digita o HTML.
              </p>
            )}
          </section>
        ) : null}
      </div>

      <p className="notification-html-editor__hint">
        Variáveis do destinatário ({`{userName}`}, {`{userFullName}`}, {`{userEmail}`}) são
        substituídas no envio. O HTML é sanitizado na Core API antes de ser gravado.
      </p>
    </div>
  );
}
