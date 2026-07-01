import {
  Activity,
  Bell,
  Cake,
  Calendar,
  ClipboardList,
  KeyRound,
  Megaphone,
  MessageCircle,
  Sparkles,
  type LucideIcon,
} from "lucide-react";

export type NotificationCatalogCategory = {
  id: string;
  label: string;
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
    { id: "system", label: "Sistema", icon: "bell", mutable: false, kind: "platform" },
    { id: "welcome", label: "Boas-vindas", icon: "sparkles", mutable: true, kind: "platform" },
    { id: "birthday", label: "Aniversário", icon: "cake", mutable: true, kind: "platform" },
    { id: "company_event", label: "Evento", icon: "calendar", mutable: true, kind: "platform" },
    { id: "announcement", label: "Comunicado", icon: "megaphone", mutable: true, kind: "platform" },
    { id: "access", label: "Acesso", icon: "key-round", mutable: true, kind: "platform" },
    { id: "custom", label: "Personalizada", icon: "bell", mutable: true, kind: "platform" },
    {
      id: "controle_mp",
      label: "Controle MP",
      icon: "message-circle",
      mutable: true,
      kind: "app",
      sourceApps: ["controle_mp"],
      pluginId: "controle-mp",
    },
    {
      id: "api_console",
      label: "Console API DELPI",
      icon: "activity",
      mutable: true,
      kind: "app",
      sourceApps: ["api-delpi-console"],
      pluginId: "api-delpi-console",
    },
    {
      id: "quality_action_plans",
      label: "Planos de ação (PAC)",
      icon: "clipboard-list",
      mutable: true,
      kind: "app",
      sourceApps: ["quality-action-plans"],
      pluginId: "quality-action-plans",
    },
  ],
  legacyCategoryAliases: {
    quality: "quality_action_plans",
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

export function getNotificationCategoryIcon(
  categoryId: string,
  catalog: NotificationCatalogResponse = FALLBACK_NOTIFICATION_CATALOG,
): LucideIcon {
  const iconName = getNotificationCategorySpec(categoryId, catalog)?.icon ?? "bell";
  return ICON_BY_NAME[iconName] ?? Bell;
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
