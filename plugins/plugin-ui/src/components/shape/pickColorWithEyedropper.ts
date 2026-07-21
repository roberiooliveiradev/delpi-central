/**
 * Conta-gotas do sistema (EyeDropper API) — cor sRGB em hex (#rrggbb).
 * Indisponível em browsers sem suporte ou em contextos sem gesto do usuário.
 */

type EyeDropperResult = { sRGBHex: string };

type EyeDropperConstructor = new () => {
  open: (options?: { signal?: AbortSignal }) => Promise<EyeDropperResult>;
};

function getEyeDropperCtor(): EyeDropperConstructor | null {
  if (typeof window === "undefined") return null;
  const ctor = (window as Window & { EyeDropper?: EyeDropperConstructor }).EyeDropper;
  return typeof ctor === "function" ? ctor : null;
}

export function isEyedropperSupported(): boolean {
  return getEyeDropperCtor() != null;
}

/**
 * Abre o conta-gotas nativo. Retorna hex ou `null` se cancelado / sem suporte.
 */
export async function pickColorWithEyedropper(
  options?: { signal?: AbortSignal },
): Promise<string | null> {
  const Ctor = getEyeDropperCtor();
  if (!Ctor) return null;
  try {
    const result = await new Ctor().open(options?.signal ? { signal: options.signal } : undefined);
    const hex = String(result?.sRGBHex ?? "").trim();
    return hex || null;
  } catch {
    return null;
  }
}
