/**
 * Autorização de rota do host: permissão única ou ANY-OF.
 * Espelha o contrato Core (`permission` + `anyOfPermissions`).
 */

export function normalizeRequiredPermissions(
  permission?: string | string[] | null,
  anyOfPermissions?: string[] | null,
): string[] {
  if (Array.isArray(anyOfPermissions) && anyOfPermissions.length > 0) {
    const seen = new Set<string>();
    const ordered: string[] = [];
    for (const item of anyOfPermissions) {
      const code = String(item || "").trim();
      if (!code || seen.has(code)) continue;
      seen.add(code);
      ordered.push(code);
    }
    if (ordered.length > 0) return ordered;
  }

  if (Array.isArray(permission)) {
    const seen = new Set<string>();
    const ordered: string[] = [];
    for (const item of permission) {
      const code = String(item || "").trim();
      if (!code || seen.has(code)) continue;
      seen.add(code);
      ordered.push(code);
    }
    return ordered;
  }

  const single = String(permission || "").trim();
  return single ? [single] : [];
}

export function userHasAnyPermission(
  userPermissions: readonly string[] | undefined,
  required: readonly string[],
): boolean {
  if (required.length === 0) return true;
  const held = new Set(userPermissions ?? []);
  return required.some((code) => held.has(code));
}
