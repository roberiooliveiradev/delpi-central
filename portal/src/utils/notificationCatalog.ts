import { resolveIcon } from "./iconResolver";
import {
  Activity,
  Bell,
  Briefcase,
  Cake,
  Calendar,
  ClipboardCheck,
  ClipboardList,
  FileText,
  KeyRound,
  Megaphone,
  MessageCircle,
  Sparkles,
  type LucideIcon,
} from "lucide-react";

export type NotificationCatalogCategory = {
  id: string;
  label: string;
  /** Nome da notificação no card de Preferências (obrigatório no catálogo). */
  notificationLabel: string;
  icon: string;
  mutable: boolean;
  kind: "platform" | "app" | string;
  sourceApps?: string[];
  pluginId?: string;
};

export type NotificationCatalogResponse = {
  version: number;
  categories: NotificationCatalogCategory[];
  legacyCategoryAliases?: Record<string, string>;
};

/** Espelho de `core-api/app/content/notification_catalog.json` — fallback offline. */
export const FALLBACK_NOTIFICATION_CATALOG: NotificationCatalogResponse = {
  version: 1,
  categories: [
    { id: "system", label: "Sistema", notificationLabel: "Avisos de sistema", icon: "bell", mutable: false, kind: "platform" },
    { id: "welcome", label: "Boas-vindas", notificationLabel: "Boas-vindas", icon: "sparkles", mutable: true, kind: "platform" },
    { id: "birthday", label: "Aniversário", notificationLabel: "Aniversário", icon: "cake", mutable: true, kind: "platform" },
    { id: "company_event", label: "Evento", notificationLabel: "Evento da empresa", icon: "calendar", mutable: true, kind: "platform" },
    { id: "announcement", label: "Comunicado", notificationLabel: "Comunicado", icon: "megaphone", mutable: true, kind: "platform" },
    { id: "access", label: "Acesso", notificationLabel: "Acesso a aplicações", icon: "key-round", mutable: true, kind: "platform" },
    { id: "custom", label: "Personalizada", notificationLabel: "Personalizada", icon: "bell", mutable: true, kind: "platform" },
    { id: "controle_mp", label: "Controle MP", notificationLabel: "Mensagens do Controle MP", icon: "message-circle", mutable: true, kind: "app", sourceApps: ["controle_mp"], pluginId: "controle-mp" },
    { id: "api_console", label: "Console API DELPI", notificationLabel: "Alertas do Console API", icon: "activity", mutable: true, kind: "app", sourceApps: ["api-delpi-console"], pluginId: "api-delpi-console" },
    { id: "quality_action_plans", label: "Planos de ação (PAC)", notificationLabel: "Atualizações de planos de ação", icon: "clipboard-list", mutable: true, kind: "app", sourceApps: ["quality-action-plans"], pluginId: "quality-action-plans" },
    { id: "auditoria_5s", label: "Auditoria 5S", notificationLabel: "Auditorias e não conformidades 5S", icon: "clipboard-check", mutable: true, kind: "app", sourceApps: ["auditoria-5s"], pluginId: "auditoria-5s" },
    { id: "central_agendamento", label: "Central de Agendamento", notificationLabel: "Agendamentos e lembretes", icon: "calendar", mutable: true, kind: "app", sourceApps: ["central-agendamento"], pluginId: "central-agendamento" },
    { id: "kaizometro", label: "Kaizômetro", notificationLabel: "Atualizações de kaizens", icon: "sparkles", mutable: true, kind: "app", sourceApps: ["kaizometro"], pluginId: "kaizometro" },
    { id: "lancamento_notas_fiscais", label: "Lançamento de Notas Fiscais", notificationLabel: "Pendências e menções de lançamento", icon: "file-text", mutable: true, kind: "app", sourceApps: ["lancamento-notas-fiscais"], pluginId: "lancamento-notas-fiscais" },
    { id: "invoice_issuance", label: "Emissão de Notas Fiscais", notificationLabel: "Solicitações de emissão de NF", icon: "file-text", mutable: true, kind: "app", sourceApps: ["invoice-issuance"], pluginId: "invoice-issuance" },
    { id: "comite_etica_conduta", label: "Comitê de Ética e Conduta", notificationLabel: "Atualizações do comitê", icon: "clipboard-check", mutable: true, kind: "app", sourceApps: ["comite-etica-conduta"], pluginId: "comite-etica-conduta" },
    { id: "tv_dashboard", label: "Painéis TV", notificationLabel: "Avisos dos painéis TV", icon: "tv", mutable: true, kind: "app", sourceApps: ["tv-dashboard"], pluginId: "tv-dashboard" },
    { id: "commercial", label: "Portal Comercial", notificationLabel: "Faturar notas fiscais", icon: "briefcase", mutable: true, kind: "app", sourceApps: ["commercial"], pluginId: "commercial" },
  ],
  legacyCategoryAliases: {
    quality: "quality_action_plans",
    cadastro_kaizen: "kaizometro",
  },
};

const ICON_BY_NAME: Record<string, LucideIcon> = {
  bell: Bell,
  sparkles: Sparkles,
  cake: Cake,
  calendar: Calendar,
  megaphone: Megaphone,
  "key-round": KeyRound,
  "message-circle": MessageCircle,
  activity: Activity,
  "clipboard-list": ClipboardList,
  "clipboard-check": ClipboardCheck,
  "file-text": FileText,
  "file-output": FileText,
  briefcase: Briefcase,
};

export function resolveNotificationCategoryId(
  categoryId: string,
  catalog: NotificationCatalogResponse = FALLBACK_NOTIFICATION_CATALOG,
): string {
  const normalized = categoryId.trim().toLowerCase();
  return catalog.legacyCategoryAliases?.[normalized] ?? normalized;
}

export function getNotificationCategorySpec(
  categoryId: string,
  catalog: NotificationCatalogResponse = FALLBACK_NOTIFICATION_CATALOG,
): NotificationCatalogCategory | undefined {
  const resolved = resolveNotificationCategoryId(categoryId, catalog);
  return catalog.categories.find((item) => item.id === resolved);
}

export function getNotificationCategoryLabel(
  categoryId: string,
  catalog: NotificationCatalogResponse = FALLBACK_NOTIFICATION_CATALOG,
): string {
  return getNotificationCategorySpec(categoryId, catalog)?.label ?? categoryId;
}

export function getNotificationCategoryKindLabel(
  kind: string | null | undefined,
): string {
  const normalized = (kind || "").trim().toLowerCase();
  if (normalized === "app") return "Aplicação";
  if (normalized === "platform") return "Plataforma";
  return normalized ? normalized : "Notificação";
}

export type NotificationPreferenceDisplay = {
  /** Nome da notificação (título do card). */
  notificationName: string;
  /** Nome da aplicação de origem. */
  applicationName: string;
  /** Ícone Lucide (app.icon do manifesto ou catálogo). */
  iconName: string;
};

type AppRef = { id: string; name: string; icon?: string | null };

/**
 * Preferências / cards: nome da notificação → app → status.
 * Ícone de `kind=app` vem do manifesto publicado (`apps.icon`), não do JSON do catálogo.
 */
export function resolveNotificationPreferenceDisplay(
  categoryId: string,
  catalog: NotificationCatalogResponse = FALLBACK_NOTIFICATION_CATALOG,
  apps: AppRef[] = [],
): NotificationPreferenceDisplay {
  const spec = getNotificationCategorySpec(categoryId, catalog);
  const catalogLabel = spec?.label ?? categoryId;
  const notificationName =
    (spec?.notificationLabel || "").trim() || catalogLabel;
  const kind = (spec?.kind || "platform").toLowerCase();
  const catalogIcon = (spec?.icon || "bell").trim() || "bell";

  if (kind === "app") {
    const pluginId = (spec?.pluginId || "").trim();
    const pluginKey = pluginId.toLowerCase();
    const sourceKeys = new Set(
      (spec?.sourceApps ?? []).map((item) => item.trim().toLowerCase()).filter(Boolean),
    );
    if (pluginKey) sourceKeys.add(pluginKey);

    const matched = apps.find((app) => {
      const id = app.id.trim().toLowerCase();
      return id === pluginKey || sourceKeys.has(id);
    });

    const publishedIcon = (matched?.icon || "").trim();
    // Catálogo só como último recurso (API já enriquece com apps.icon do manifesto).
    const iconName = publishedIcon || catalogIcon || "bell";
    return {
      notificationName,
      applicationName: matched?.name?.trim() || catalogLabel,
      iconName,
    };
  }

  return {
    notificationName,
    applicationName: "Minha Delpi",
    iconName: catalogIcon,
  };
}

/** Ícone Lucide para categoria — prioriza manifesto via `apps`. */
export function resolveNotificationCategoryIcon(
  categoryId: string,
  catalog: NotificationCatalogResponse = FALLBACK_NOTIFICATION_CATALOG,
  apps: AppRef[] = [],
): LucideIcon {
  const { iconName } = resolveNotificationPreferenceDisplay(categoryId, catalog, apps);
  return resolveNotificationCategoryIconComponent(iconName);
}

export function resolveNotificationCategoryIconComponent(
  iconName: string | null | undefined,
): LucideIcon {
  const key = (iconName || "bell").trim();
  return resolveIcon(key) ?? ICON_BY_NAME[key.toLowerCase()] ?? Bell;
}

/** @deprecated Preferir `resolveNotificationCategoryIcon` com lista de apps publicados. */
export function getNotificationCategoryIcon(
  categoryId: string,
  catalog: NotificationCatalogResponse = FALLBACK_NOTIFICATION_CATALOG,
): LucideIcon {
  return resolveNotificationCategoryIcon(categoryId, catalog, []);
}

export function buildNotificationCategoryOptions(
  catalog: NotificationCatalogResponse = FALLBACK_NOTIFICATION_CATALOG,
  options?: { includeAll?: boolean; onlyMutable?: boolean },
): { value: string; label: string }[] {
  const items = catalog.categories.filter((item) =>
    options?.onlyMutable ? item.mutable : true,
  );

  const mapped = items.map((item) => ({ value: item.id, label: item.label }));

  if (options?.includeAll) {
    return [{ value: "", label: "Todas as categorias" }, ...mapped];
  }

  return mapped;
}

export function normalizeNotificationCatalogResponse(
  data: Partial<NotificationCatalogResponse> | null | undefined,
): NotificationCatalogResponse {
  if (!data?.categories?.length) {
    return FALLBACK_NOTIFICATION_CATALOG;
  }

  return {
    version: data.version ?? FALLBACK_NOTIFICATION_CATALOG.version,
    categories: data.categories,
    legacyCategoryAliases:
      data.legacyCategoryAliases ?? FALLBACK_NOTIFICATION_CATALOG.legacyCategoryAliases,
  };
}
