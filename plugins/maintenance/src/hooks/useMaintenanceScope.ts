import { useEffect, useMemo, useState } from "react";

import { MAINTENANCE_ROUTES } from "../constants/routes";
import { fetchMaintenanceOptions, type MaintenanceOptions, type MaintenanceSubmodule } from "../data/api/maintenanceApi";
import {
  getStoredFilial,
  resolveActiveFilial,
  setStoredFilial,
} from "../utils/maintenanceFilialSelection";
import { resolveMaintenanceHomePath } from "../utils/routeParser";

function filterSubmodulesForFilial(
  submodules: MaintenanceSubmodule[],
  filialId: string | undefined,
): MaintenanceSubmodule[] {
  if (!filialId) {
    return submodules;
  }
  return submodules.filter(
    (item) => !item.filiais?.length || item.filiais.includes(filialId),
  );
}

export function useMaintenanceOptions(getAccessToken?: () => string | undefined) {
  const [options, setOptions] = useState<MaintenanceOptions | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    fetchMaintenanceOptions(getAccessToken)
      .then((data) => {
        if (!active) return;
        setOptions(data);
        setError(null);
      })
      .catch((err: Error) => {
        if (!active) return;
        setOptions(null);
        setError(err.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [getAccessToken]);

  return { options, loading, error };
}

export function useMaintenanceModuleHomePath(
  getAccessToken?: () => string | undefined,
  filialScope?: string,
): string {
  const { options } = useMaintenanceOptions(getAccessToken);
  const filiais = options?.filiais ?? [];

  if (filialScope) {
    return resolveMaintenanceHomePath(filialScope);
  }

  const activeFilial = resolveActiveFilial(undefined, filiais, options?.default_filial ?? undefined);
  if (activeFilial && filiais.length === 1) {
    return MAINTENANCE_ROUTES.filialHome(activeFilial);
  }

  return MAINTENANCE_ROUTES.home;
}

export function useMaintenanceActiveFilial(
  getAccessToken?: () => string | undefined,
  filialScope?: string,
) {
  const { options, loading, error } = useMaintenanceOptions(getAccessToken);
  const filiais = options?.filiais ?? [];
  const [activeFilial, setActiveFilialState] = useState<string | undefined>();

  useEffect(() => {
    const resolved = resolveActiveFilial(
      filialScope,
      filiais,
      options?.default_filial ?? undefined,
    );
    setActiveFilialState(resolved);
    if (resolved) {
      setStoredFilial(resolved);
    }
  }, [filialScope, filiais, options?.default_filial]);

  const setActiveFilial = (filialId: string) => {
    setStoredFilial(filialId);
    setActiveFilialState(filialId);
  };

  const allSubmodules = options?.submodules ?? options?.modulos ?? [];
  const submodules = useMemo(
    () => filterSubmodulesForFilial(allSubmodules, activeFilial),
    [activeFilial, allSubmodules],
  );

  return {
    filiais,
    activeFilial,
    setActiveFilial,
    loading,
    error,
    submodules,
    canManageFiliais: options?.can_manage_filiais ?? false,
    canManageMiniApplicators:
      submodules.find((item) => item.id === "mini-applicadores")?.can_manage ?? false,
  };
}

export function useOperationalFilial(
  getAccessToken?: () => string | undefined,
  filialScope?: string,
): string | undefined {
  const { activeFilial, filiais, loading } = useMaintenanceActiveFilial(getAccessToken, filialScope);
  if (loading) return getStoredFilial() ?? undefined;
  return activeFilial ?? resolveActiveFilial(filialScope, filiais) ?? getStoredFilial() ?? undefined;
}
