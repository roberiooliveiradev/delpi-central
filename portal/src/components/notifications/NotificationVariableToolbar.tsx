// src/components/notifications/NotificationVariableToolbar.tsx

import { useRef } from "react";

import {
  NOTIFICATION_VARIABLES,
  formatVariablePlaceholder,
  insertAtCursor,
  type NotificationVariableScope,
} from "./notificationVariables";

import "./NotificationVariableToolbar.css";

type NotificationVariableToolbarProps = {
  targetRef: React.RefObject<HTMLTextAreaElement | HTMLInputElement | null>;
  value: string;
  onChange: (value: string) => void;
  scopes?: NotificationVariableScope[];
  disabled?: boolean;
};

export function NotificationVariableToolbar({
  targetRef,
  value,
  onChange,
  scopes,
  disabled = false,
}: NotificationVariableToolbarProps) {
  const fallbackRef = useRef<HTMLTextAreaElement>(null);
  const variables = NOTIFICATION_VARIABLES.filter(
    (item) => !scopes || scopes.includes(item.scope),
  );

  function handleInsert(key: string) {
    const element = targetRef.current ?? fallbackRef.current;
    if (!element) {
      onChange(`${value}${formatVariablePlaceholder(key)}`);
      return;
    }
    insertAtCursor(element, formatVariablePlaceholder(key), value, onChange);
  }

  return (
    <div className="notification-var-toolbar">
      <span className="notification-var-toolbar__label">Inserir variável:</span>
      <div className="notification-var-toolbar__chips">
        {variables.map((item) => (
          <button
            key={item.key}
            type="button"
            className={`notification-var-toolbar__chip notification-var-toolbar__chip--${item.scope}`}
            disabled={disabled}
            title={`${item.description} — ex.: ${item.example}`}
            onClick={() => handleInsert(item.key)}
          >
            {item.label}
            <code>{formatVariablePlaceholder(item.key)}</code>
          </button>
        ))}
      </div>
    </div>
  );
}
