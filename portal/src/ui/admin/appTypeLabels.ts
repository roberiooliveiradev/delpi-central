import type { ManifestType } from "./manifest/manifestTypes";

export const APP_TYPE_OPTIONS: { value: ManifestType; label: string }[] = [
  { value: "microfrontend", label: "Microfrontend" },
  { value: "iframe", label: "Iframe" },
  { value: "backend-only", label: "Backend-only" },
];

export function formatAppType(type?: string | null) {
  if (!type) return "Não informado";

  const match = APP_TYPE_OPTIONS.find((option) => option.value === type);
  return match?.label ?? type;
}
