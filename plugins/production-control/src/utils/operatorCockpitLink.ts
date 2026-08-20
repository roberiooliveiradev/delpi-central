/** Link público do cockpit do operador servido pelo public-hub (`/p/{app}/{page}/{token}`). */
export const OPERATOR_COCKPIT_TOKEN = "aberto";

export function buildOperatorCockpitUrl(branch: string, origin?: string): string {
  const base = (origin ?? window.location.origin).replace(/\/$/, "");
  const params = new URLSearchParams({ branch });
  return `${base}/p/production-control/cockpit/${OPERATOR_COCKPIT_TOKEN}?${params}`;
}

export async function copyText(value: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(value);
    return true;
  } catch {
    return legacyCopy(value);
  }
}

function legacyCopy(value: string): boolean {
  if (typeof document === "undefined") return false;
  const field = document.createElement("textarea");
  field.value = value;
  field.setAttribute("readonly", "");
  field.style.position = "fixed";
  field.style.opacity = "0";
  document.body.appendChild(field);
  field.select();
  let ok = false;
  try {
    ok = document.execCommand("copy");
  } catch {
    ok = false;
  }
  document.body.removeChild(field);
  return ok;
}
