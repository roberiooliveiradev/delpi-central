// src/components/notifications/notificationVariables.ts

export type NotificationVariableScope = "recipient" | "admin";

export type NotificationVariableDefinition = {
  key: string;
  label: string;
  description: string;
  scope: NotificationVariableScope;
  example: string;
};

export const NOTIFICATION_VARIABLES: NotificationVariableDefinition[] = [
  {
    key: "userName",
    label: "Nome (primeiro)",
    description: "Preenchido automaticamente para cada destinatário",
    scope: "recipient",
    example: "Maria",
  },
  {
    key: "userFullName",
    label: "Nome completo",
    description: "Preenchido automaticamente para cada destinatário",
    scope: "recipient",
    example: "Maria Silva",
  },
  {
    key: "userEmail",
    label: "E-mail",
    description: "Preenchido automaticamente para cada destinatário",
    scope: "recipient",
    example: "maria@empresa.com",
  },
  {
    key: "eventName",
    label: "Nome do evento",
    description: "Informado no envio (mesmo valor para todos)",
    scope: "admin",
    example: "Confraternização",
  },
  {
    key: "eventDate",
    label: "Data do evento",
    description: "Opcional no envio",
    scope: "admin",
    example: "20/06/2026 às 19h",
  },
  {
    key: "location",
    label: "Local",
    description: "Opcional no envio",
    scope: "admin",
    example: "Auditório principal",
  },
];

export function formatVariablePlaceholder(key: string) {
  return `{${key}}`;
}

export function insertAtCursor(
  element: HTMLTextAreaElement | HTMLInputElement,
  text: string,
  currentValue: string,
  onChange: (next: string) => void,
) {
  const start = element.selectionStart ?? currentValue.length;
  const end = element.selectionEnd ?? currentValue.length;
  const next = `${currentValue.slice(0, start)}${text}${currentValue.slice(end)}`;
  onChange(next);

  requestAnimationFrame(() => {
    const position = start + text.length;
    element.focus();
    element.setSelectionRange(position, position);
  });
}
