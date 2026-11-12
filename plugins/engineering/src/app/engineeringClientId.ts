/** client_id por aba — suprime toast da própria origem quando o
 * envelope trouxer `actorClientId`. */

const KEY = "delpi-engineering-client-id";

export function getEngineeringClientId(): string {
  try {
    const existing = window.sessionStorage.getItem(KEY);
    if (existing) return existing;
    const id = crypto.randomUUID();
    window.sessionStorage.setItem(KEY, id);
    return id;
  } catch {
    return `eng-${Math.random().toString(36).slice(2)}`;
  }
}
