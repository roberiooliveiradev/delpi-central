const PREVIEW_SAMPLES: Record<string, string> = {
  userName: "Usuária",
  userFullName: "Usuária Teste",
  userEmail: "usuario.teste@exemplo.com",
  eventName: "Confraternização DELPI",
  eventDate: "20/06/2026 às 19h",
  location: "Auditório principal",
  years: "3",
};

export function substituteNotificationVariables(html: string): string {
  if (!html.trim()) {
    return "";
  }

  return html.replace(/\{(\w+)\}/g, (match, key: string) => PREVIEW_SAMPLES[key] ?? match);
}
