export const COMUNICADO_BOX_SHADOW_PRESETS = [
  { key: "none", label: "Nenhuma", value: undefined },
  { key: "soft", label: "Suave", value: "0 4px 14px rgba(0, 0, 0, 0.28)" },
  { key: "medium", label: "Média", value: "0 8px 24px rgba(0, 0, 0, 0.35)" },
  { key: "hard", label: "Forte", value: "0 2px 10px rgba(0, 0, 0, 0.55)" },
] as const;

export function matchBoxShadowPreset(value?: string): string {
  if (!value) return "none";
  const preset = COMUNICADO_BOX_SHADOW_PRESETS.find((item) => item.value === value);
  return preset?.key ?? "none";
}
