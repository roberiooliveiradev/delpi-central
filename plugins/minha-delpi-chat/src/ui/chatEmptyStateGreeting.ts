import { getFirstDisplayName } from "../utils/authDisplayName";

const GREETINGS_WITH_NAME = [
  (name: string) => `Olá, ${name}. Como posso ajudar você hoje?`,
  (name: string) => `Oi, ${name}. O que vamos resolver?`,
  (name: string) => `Ei, ${name}. Pode perguntar do seu jeito.`,
] as const;

const GREETINGS_ANONYMOUS = [
  "Olá. Como posso ajudar você hoje?",
  "O que vamos resolver hoje?",
  "Pode perguntar do seu jeito.",
] as const;

const HINT_WITH_NAME =
  "Pode escrever consultas, textos, análises ou documentos — do seu jeito.";
const HINT_ANONYMOUS =
  "Escreva consultas, textos, análises ou documentos — do seu jeito.";

function daySeedOffset(extra = 0) {
  const daySeed = new Date().toISOString().slice(0, 10);

  return (
    Math.abs(daySeed.split("").reduce((acc, ch) => acc + ch.charCodeAt(0), 0) + extra) %
    GREETINGS_WITH_NAME.length
  );
}

export function pickEmptyStateGreeting(displayName?: string | null): string {
  const firstName = getFirstDisplayName(displayName);

  if (firstName) {
    return GREETINGS_WITH_NAME[daySeedOffset()](firstName);
  }

  const index = daySeedOffset(7) % GREETINGS_ANONYMOUS.length;

  return GREETINGS_ANONYMOUS[index];
}

export function pickEmptyStateHint(displayName?: string | null): string {
  const firstName = getFirstDisplayName(displayName);

  return firstName ? HINT_WITH_NAME : HINT_ANONYMOUS;
}
