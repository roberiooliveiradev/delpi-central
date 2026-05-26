// src/components/notifications/notificationTemplates.ts

import type {
  NotificationTemplateDefinition,
  NotificationTemplateFieldSpec,
} from "../../data/coreApi";

export type { NotificationTemplateDefinition, NotificationTemplateFieldSpec };

export const NOTIFICATION_TEMPLATE_DEFINITIONS: NotificationTemplateDefinition[] = [
  {
    id: "welcome_v1",
    label: "Boas-vindas",
    category: "welcome",
    defaultType: "success",
    defaultTitle: "Bem-vindo à Minha DELPI",
    defaultMessage: "Olá, {userName}! Sua conta está pronta para explorar os aplicativos.",
    recipientAutoVars: ["userName"],
    recipientVars: ["userName"],
    isSystem: true,
    hint: "Explore os aplicativos no menu lateral e personalize seus favoritos.",
    fields: [],
  },
  {
    id: "birthday_v1",
    label: "Aniversário",
    category: "birthday",
    defaultType: "success",
    defaultTitle: "Feliz aniversário!",
    defaultMessage: "A equipe DELPI deseja um excelente dia, {userName}!",
    recipientAutoVars: ["userName"],
    recipientVars: ["userName"],
    isSystem: true,
    hint: "🎂 Um ótimo ano novo de conquistas!",
    fields: [],
  },
  {
    id: "company_event_v1",
    label: "Evento da empresa",
    category: "company_event",
    defaultType: "info",
    defaultTitle: "Evento da empresa",
    defaultMessage: "Você está convidado(a) para {eventName}.",
    isSystem: true,
    fields: [
      { key: "eventName", label: "Nome do evento", placeholder: "Confraternização", required: true },
      { key: "eventDate", label: "Data (opcional)", placeholder: "20/06/2026 às 19h" },
      { key: "location", label: "Local (opcional)", placeholder: "Auditório principal" },
    ],
  },
  {
    id: "app_access_granted_v1",
    label: "Acesso a aplicação concedido",
    category: "access",
    defaultType: "info",
    defaultTitle: "Novo acesso liberado",
    defaultMessage: "Olá, {userName}! Você recebeu acesso a: {appNames}.",
    recipientAutoVars: ["userName"],
    recipientVars: ["userName"],
    isSystem: true,
    hint: "Acesse pelo menu lateral ou pela página de aplicativos.",
    fields: [
      { key: "appNames", label: "Aplicações", placeholder: "App1, App2, App3", required: true },
    ],
  },
];

export function getTemplateDefinition(
  templates: NotificationTemplateDefinition[],
  templateId: string | undefined | null,
) {
  return templates.find((item) => item.id === templateId) ?? null;
}

export function renderTemplateText(template: string, vars: Record<string, string>) {
  return template.replace(/\{(\w+)\}/g, (_, key: string) => vars[key] ?? `{${key}}`);
}

export function buildTemplatePreview(
  definition: NotificationTemplateDefinition,
  vars: Record<string, string>,
  previewRecipientVars?: Record<string, string>,
) {
  const merged = { ...(previewRecipientVars ?? {}), ...vars };
  return {
    title: renderTemplateText(definition.defaultTitle, merged),
    message: renderTemplateText(definition.defaultMessage, merged),
  };
}

export function resolvePreviewRecipientName(displayName?: string | null) {
  const trimmed = displayName?.trim();
  if (!trimmed) {
    return "Fulano";
  }
  return trimmed.split(/\s+/)[0] ?? trimmed;
}

export function getTemplateVarsFromMetadata(metadata: Record<string, unknown> | null | undefined) {
  const raw = metadata?.vars;
  if (!raw || typeof raw !== "object") {
    return {};
  }

  const result: Record<string, string> = {};
  for (const [key, value] of Object.entries(raw as Record<string, unknown>)) {
    if (value != null && String(value).trim()) {
      result[key] = String(value).trim();
    }
  }
  return result;
}

export function getTemplateIdFromMetadata(metadata: Record<string, unknown> | null | undefined) {
  const id = metadata?.templateId;
  return typeof id === "string" ? id : null;
}

export function isSystemTemplate(definition: NotificationTemplateDefinition | null) {
  return Boolean(definition?.isSystem);
}
