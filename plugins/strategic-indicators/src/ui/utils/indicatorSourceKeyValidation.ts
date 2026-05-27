const SOURCE_KEY_PATTERN = /^[a-z][a-z0-9_]{0,127}$/;

export function normalizeIndicatorSourceKey(sourceKey: string | null | undefined): string {
  return (sourceKey ?? "").trim();
}

export function validateIndicatorSourceKey(
  sourceKey: string | null | undefined,
  isActive: boolean,
): string | null {
  const normalized = normalizeIndicatorSourceKey(sourceKey);

  if (isActive && !normalized) {
    return (
      "A chave da fonte é obrigatória para indicadores ativos " +
      "(medições automáticas e metas nos dashboards departamentais)."
    );
  }

  if (!normalized) {
    return null;
  }

  if (!SOURCE_KEY_PATTERN.test(normalized)) {
    return (
      "Chave inválida: use letras minúsculas, números e underscore " +
      "(ex.: commercial_rol, production_otd)."
    );
  }

  return null;
}
