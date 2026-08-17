/** Saudação por horário — alinhada à home do portal. */
export function timeOfDayGreeting(now: Date = new Date()): string {
  const hour = now.getHours();
  if (hour < 12) return "Bom dia";
  if (hour < 18) return "Boa tarde";
  return "Boa noite";
}

/** Primeiro nome para saudação; null se não houver. */
export function firstNameFromDisplayName(name?: string | null): string | null {
  const trimmed = (name ?? "").trim();
  if (!trimmed) return null;
  const first = trimmed.split(/\s+/).find(Boolean);
  return first ?? null;
}

export function formatHomeGreeting(name?: string | null, now: Date = new Date()): string {
  const greeting = timeOfDayGreeting(now);
  const first = firstNameFromDisplayName(name);
  return first ? `${greeting}, ${first}` : `${greeting}!`;
}
