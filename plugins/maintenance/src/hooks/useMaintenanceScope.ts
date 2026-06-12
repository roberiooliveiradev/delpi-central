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

function resolveOptionsFilialQuery(filialScope?: string): string | undefined {
  if (filialScope && /^[0-9]{2}$/.test(filialScope)) {
    return filialScope;
  }
  return getStoredFilial() ?? undefined;
}

export function resolveCanManageMiniApplicators(
  options: MaintenanceOptions | null,
  submodules: MaintenanceSubmodule[],
  activeFilial?: string,
): boolean {
  const submodule = submodules.find((item) => item.id === "mini-aplicadores");
  if (submodule?.can_manage) {
    return true;
  }

  const manageFiliais = options?.access_scope?.manage_filiais ?? [];
  if (activeFilial) {
    return manageFiliais.includes(activeFilial);
  }

  return manageFiliais.length > 0;
}

export function useMaintenanceOptions(
  getAccessToken?: () => string | undefined,
  filialQuery?: string,
) {
  const [options, setOptions] = useState<MaintenanceOptions | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    fetchMaintenanceOptions(getAccessToken, filialQuery)
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
  }, [getAccessToken, filialQuery]);

  return { options, loading, error };
}

export function useMaintenanceModuleHomePath(
  getAccessToken?: () => string | undefined,
  filialScope?: string,
): string {
  const { options } = useMaintenanceOptions(getAccessToken, resolveOptionsFilialQuery(filialScope));
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
  const [optionsFilialQuery, setOptionsFilialQuery] = useState<string | undefined>(
    () => resolveOptionsFilialQuery(filialScope),
  );
  const { options, loading, error } = useMaintenanceOptions(getAccessToken, optionsFilialQuery);
  const filiais = options?.filiais ?? [];
  const [activeFilial, setActiveFilialState] = useState<string | undefined>();

  useEffect(() => {
    setOptionsFilialQuery(resolveOptionsFilialQuery(filialScope));
  }, [filialScope]);

  useEffect(() => {
    const resolved = resolveActiveFilial(
      filialScope,
      filiais,
      options?.default_filial ?? undefined,
    );
    setActiveFilialState(resolved);
    if (resolved) {
      setStoredFilial(resolved);
      if (resolved !== optionsFilialQuery) {
        setOptionsFilialQuery(resolved);
      }
    }
  }, [filialScope, filiais, options?.default_filial, optionsFilialQuery]);

  const setActiveFilial = (filialId: string) => {
    setStoredFilial(filialId);
    setActiveFilialState(filialId);
    setOptionsFilialQuery(filialId);
  };

  const allSubmodules = options?.submodules ?? options?.modulos ?? [];
  const submodules = useMemo(
    () => filterSubmodulesForFilial(allSubmodules, activeFilial),
    [activeFilial, allSubmodules],
  );

  const canManageMiniApplicators = useMemo(
    () => resolveCanManageMiniApplicators(options, submodules, activeFilial),
    [activeFilial, options, submodules],
  );

  return {
    filiais,
    activeFilial,
    setActiveFilial,
    loading,
    error,
    submodules,
    canManageFiliais: options?.can_manage_filiais ?? false,
    canManageMiniApplicators,
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
