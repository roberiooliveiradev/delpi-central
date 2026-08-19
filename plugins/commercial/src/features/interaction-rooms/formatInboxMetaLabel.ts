export type FormatInboxMetaLabelOptions = {
  now?: Date;
  yesterdayLabel?: string;
};

function startOfLocalDay(date: Date): number {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
}

export function formatInboxMetaLabel(
  iso: string | null | undefined,
  options: FormatInboxMetaLabelOptions = {},
): string {
  if (!iso) return "";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  const now = options.now ?? new Date();
  const yesterdayLabel = options.yesterdayLabel ?? "Ontem";
  const day = startOfLocalDay(date);
  const today = startOfLocalDay(now);
  const dayMs = 24 * 60 * 60 * 1000;
  if (day === today) {
    return new Intl.DateTimeFormat("pt-BR", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }).format(date);
  }
  if (day === today - dayMs) return yesterdayLabel;
  if (date.getFullYear() === now.getFullYear()) {
    return new Intl.DateTimeFormat("pt-BR", {
      day: "2-digit",
      month: "2-digit",
    }).format(date);
  }
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(date);
}
