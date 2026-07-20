import { useCallback } from "react";

import { useTransformometroEntityWatch } from "../hooks/useTransformometroEntityWatch";

export type CatalogWatchId = "processo" | "filial" | "setor" | "recurso" | "dashboard";

type Options = {
  catalogId: CatalogWatchId;
  getAccessToken?: () => string | undefined;
  enabled?: boolean;
  onUpdated: () => void;
};

/** Assina a sala `catalog:<id>` para recarregar listagens / dashboard em tempo real. */
export function useTransformometroCatalogWatch({
  catalogId,
  getAccessToken,
  enabled = true,
  onUpdated,
}: Options) {
  const handleUpdated = useCallback(() => {
    onUpdated();
  }, [onUpdated]);

  useTransformometroEntityWatch({
    entities: [{ entityType: "catalog", entityId: catalogId }],
    getAccessToken,
    enabled,
    onEntityUpdated: handleUpdated,
  });
}
