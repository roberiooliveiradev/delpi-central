const STORAGE_KEY = "maintenance.selectedFilial";

export function getStoredFilial(): string | null {
  if (typeof window === "undefined") return null;
  const value = window.sessionStorage.getItem(STORAGE_KEY);
  return value === "01" || value === "02" ? value : null;
}

export function setStoredFilial(filial: string): void {
  if (typeof window === "undefined") return;
  window.sessionStorage.setItem(STORAGE_KEY, filial);
}

export function resolveActiveFilial(
  filialScope: string | undefined,
  allowedFiliais: Array<{ id: string; label: string }>,
  defaultFilial?: string | null,
): string | undefined {
  if (filialScope === "01" || filialScope === "02") {
    if (allowedFiliais.some((item) => item.id === filialScope)) {
      return filialScope;
    }
  }

  if (defaultFilial && allowedFiliais.some((item) => item.id === defaultFilial)) {
    return defaultFilial;
  }

  if (allowedFiliais.length === 1) {
    return allowedFiliais[0].id;
  }

  const stored = getStoredFilial();
  if (stored && allowedFiliais.some((item) => item.id === stored)) {
    return stored;
  }

  return allowedFiliais[0]?.id;
}
