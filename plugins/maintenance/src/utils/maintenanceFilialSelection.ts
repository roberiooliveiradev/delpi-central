const STORAGE_KEY = "maintenance.selectedFilial";

function isValidFilialCode(value: string | null | undefined): value is string {
  return typeof value === "string" && /^[0-9]{2}$/.test(value);
}

export function getStoredFilial(): string | null {
  if (typeof window === "undefined") return null;
  const value = window.sessionStorage.getItem(STORAGE_KEY);
  return isValidFilialCode(value) ? value : null;
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
  if (isValidFilialCode(filialScope)) {
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

export function resolveFilialDisplayName(
  filiais: Array<{ id: string; label: string }>,
  filialId: string | undefined,
): string {
  if (!filialId) {
    return "";
  }
  const match = filiais.find((item) => item.id === filialId);
  const name = match?.label?.trim();
  return name || filialId;
}
