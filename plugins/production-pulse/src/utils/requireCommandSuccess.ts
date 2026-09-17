/**
 * Admin/detail commands return HTTP 200 even when the chip rejects the action.
 * Callers must treat `success: false` as failure (same rule as operator pad).
 */
export function requireCommandSuccess(
  result: { success: boolean; errorMessage?: string | null },
  fallback: string,
): void {
  if (result.success) return;
  const message = typeof result.errorMessage === "string" ? result.errorMessage.trim() : "";
  throw new Error(message || fallback);
}
