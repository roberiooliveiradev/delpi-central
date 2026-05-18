// src/components/notifications/useNotificationTemplates.ts

import { useCallback, useEffect, useState } from "react";

import type { CoreApi, NotificationTemplateDefinition } from "../../data/coreApi";
import { NOTIFICATION_TEMPLATE_DEFINITIONS } from "./notificationTemplates";

function mapApiTemplate(item: NotificationTemplateDefinition): NotificationTemplateDefinition {
  return {
    ...item,
    fields: item.fields ?? [],
    recipientAutoVars: item.recipientAutoVars ?? item.recipientVars ?? [],
    isSystem: item.isSystem ?? item.id.startsWith("custom_") === false,
  };
}

export function useNotificationTemplates(coreApi: CoreApi | null) {
  const [templates, setTemplates] = useState<NotificationTemplateDefinition[]>(
    NOTIFICATION_TEMPLATE_DEFINITIONS,
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    if (!coreApi) {
      setTemplates(NOTIFICATION_TEMPLATE_DEFINITIONS);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const remote = await coreApi.listNotificationTemplates();
      const mapped = remote.map(mapApiTemplate);
      setTemplates(mapped.length > 0 ? mapped : NOTIFICATION_TEMPLATE_DEFINITIONS);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar templates");
      setTemplates(NOTIFICATION_TEMPLATE_DEFINITIONS);
    } finally {
      setLoading(false);
    }
  }, [coreApi]);

  useEffect(() => {
    void reload();
  }, [reload]);

  return {
    templates,
    loading,
    error,
    reload,
  };
}
