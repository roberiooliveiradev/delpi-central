export type ResolvedInviteText = { subject: string; body: string; link_url: string };

/**
 * Quando o backend não tem `PUBLIC_BASE_URL`, o link vem relativo (`/p/commercial/form/…`).
 * Um convite colado fora do Portal precisa de URL absoluta: usa a origem atual e reescreve o
 * mesmo link dentro do corpo. Links já absolutos passam intactos.
 */
export function absolutizeInvite<T extends ResolvedInviteText>(invite: T, origin: string): T {
  const link = invite.link_url;
  if (!link.startsWith("/") || link.startsWith("//") || !origin) return invite;
  const absolute = `${origin.replace(/\/+$/, "")}${link}`;
  return { ...invite, link_url: absolute, body: invite.body.split(link).join(absolute) };
}
