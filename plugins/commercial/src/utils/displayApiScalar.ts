/** Exibe valor escalar da API sem assumir string (evita `.trim is not a function`). */
export function displayApiScalar(value: unknown, fallback = "—"): string {
  if (value == null || value === "") return fallback;
  if (typeof value === "string") {
    const trimmed = value.trim();
    return trimmed || fallback;
  }
  if (typeof value === "boolean") return value ? "Sim" : "Não";
  if (typeof value === "number" && Number.isFinite(value)) {
    return String(value);
  }
  return String(value);
}
