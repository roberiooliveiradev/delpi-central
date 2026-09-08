/** Helpers for RequestType.branch_scope (required | optional | none). */

export type BranchScope = "required" | "optional" | "none" | string;

export function normalizeBranchScope(scope: string | null | undefined): BranchScope {
  const value = (scope || "optional").trim().toLowerCase();
  if (value === "required" || value === "optional" || value === "none") return value;
  return "optional";
}

export function showsBranchField(scope: string | null | undefined): boolean {
  return normalizeBranchScope(scope) !== "none";
}

export function requiresBranchField(scope: string | null | undefined): boolean {
  return normalizeBranchScope(scope) === "required";
}

/** Branch to send on create — omit when scope is none. */
export function branchCodeForCreate(
  scope: string | null | undefined,
  branchCode: string | null | undefined,
): string | undefined {
  if (!showsBranchField(scope)) return undefined;
  const trimmed = (branchCode || "").trim();
  return trimmed || undefined;
}
