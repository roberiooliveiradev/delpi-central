const DATE_TIME = new Intl.DateTimeFormat("pt-BR", {
  dateStyle: "short",
  timeStyle: "short",
  timeZone: "America/Sao_Paulo",
});
const DATE_ONLY = new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeZone: "UTC" });

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : DATE_TIME.format(date);
}

/** Datas de negócio (`YYYY-MM-DD`) sem deslocamento de fuso. */
export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(`${value}T00:00:00Z`);
  return Number.isNaN(date.getTime()) ? "—" : DATE_ONLY.format(date);
}

export function formatCount(value: number): string {
  return value.toLocaleString("pt-BR");
}

export function orDash(value: string | null | undefined): string {
  return value && value.trim() ? value : "—";
}
