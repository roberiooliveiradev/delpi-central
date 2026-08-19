/** Autor da bolha = usuário da sessão (carteira). */
export function isOwnInteractionAuthor(
  authorUserId: string | null | undefined,
  currentUserId: string | null | undefined,
): boolean {
  const author = (authorUserId ?? "").trim();
  const me = (currentUserId ?? "").trim();
  return Boolean(author && me && author === me);
}
