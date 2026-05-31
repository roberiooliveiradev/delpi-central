/** Quebra título longo de onboarding em duas linhas equilibradas (evita “análises.” isolado gigante). */
export function splitWelcomeHeadline(title: string): { lead: string; accent?: string } {
  const trimmed = title.trim();

  if (!trimmed) {
    return { lead: trimmed };
  }

  const match = trimmed.match(/^(.+?)\s+e\s+(.+)$/iu);

  if (match && trimmed.length >= 42) {
    const lead = match[1].trim().replace(/[.,;:!?]+$/, "");
    const accent = match[2].trim();

    return {
      lead: lead.endsWith("!") || lead.endsWith("?") ? lead : `${lead}.`,
      accent,
    };
  }

  return { lead: trimmed };
}
