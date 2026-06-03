/** Erros típicos quando o SSE cai (restart do backend, proxy, rede). */
export function isIncompleteChatStreamError(error: unknown): boolean {
  const message =
    error instanceof Error
      ? error.message
      : typeof error === "string"
        ? error
        : "";

  const normalized = message.toLowerCase();

  return (
    normalized.includes("streaming foi encerrada") ||
    normalized.includes("failed to fetch") ||
    normalized.includes("networkerror") ||
    normalized.includes("network request failed") ||
    normalized.includes("load failed")
  );
}
