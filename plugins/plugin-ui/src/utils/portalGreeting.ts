export type PortalDayPeriodGreeting = "Bom dia" | "Boa tarde" | "Boa noite";

export type FormatPortalGreetingInput = {
  displayName?: string | null;
  firstName?: string | null;
  now?: Date;
  fallback?: string | null;
};

/** Primeiro token do nome de exibição. Não usa e-mail nem persiste PII. */
export function firstNameFromDisplay(name: string | null | undefined): string | null {
  const trimmed = (name ?? "").trim();
  if (!trimmed) return null;
  return trimmed.split(/\s+/)[0] || trimmed;
}

/** Saudação de período do dia. Clock injetável para teste. */
export function portalDayPeriodGreeting(date = new Date()): PortalDayPeriodGreeting {
  const hour = date.getHours();
  if (hour < 12) return "Bom dia";
  if (hour < 18) return "Boa tarde";
  return "Boa noite";
}

/**
 * Chrome de saudação dos portais: período + primeiro nome.
 * Sem nome, usa `fallback` ou só o período. Não calcula identidade.
 */
export function formatPortalGreeting(input: FormatPortalGreetingInput = {}): string {
  const period = portalDayPeriodGreeting(input.now);
  const firstName = (input.firstName ?? firstNameFromDisplay(input.displayName) ?? "").trim();
  if (firstName) return `${period}, ${firstName}`;
  const fallback = (input.fallback ?? "").trim();
  return fallback || period;
}
