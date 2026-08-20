/**
 * Rótulos de tempo da thread (criação + indicação de edição).
 */

export function formatInteractionMessageTime(
  iso: string | null | undefined,
): string {
  if (!iso) return "";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return String(iso);
  return date.toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/**
 * Ex.: `20/08, 09:41 · editado às 20/08, 10:15`
 * Sem `editedAt`, só o horário de criação.
 */
export function formatInteractionMessageCreatedAtLabel(
  createdAt: string | null | undefined,
  editedAt: string | null | undefined,
  editedAtTemplate: string,
): string {
  const created = formatInteractionMessageTime(createdAt);
  const edited = formatInteractionMessageTime(editedAt);
  if (!edited) return created;
  const editedPart = editedAtTemplate.replace(/\{time\}/g, edited);
  if (!created) return editedPart;
  return `${created} · ${editedPart}`;
}
