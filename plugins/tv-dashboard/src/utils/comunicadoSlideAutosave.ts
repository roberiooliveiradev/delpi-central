/**
 * Coordenação de autosave do slide custom_message (comunicado).
 * Versão monotônica por slide evita que uma resposta stale apague draft/pending mais novos.
 */

export type ComunicadoAutosavePending = {
  slideId: string;
  nativeConfig: Record<string, unknown>;
  version: number;
};

export function bumpComunicadoAutosaveVersion(
  versions: Map<string, number>,
  slideId: string,
): number {
  const next = (versions.get(slideId) ?? 0) + 1;
  versions.set(slideId, next);
  return next;
}

export function isStaleComunicadoAutosave(
  completedVersion: number | undefined,
  latestVersion: number,
): boolean {
  if (completedVersion == null) return false;
  return completedVersion < latestVersion;
}

/**
 * Após updateSlide: qual nativeConfig manter no estado local.
 * Resposta stale nunca sobrescreve pending/live mais novo do mesmo slide.
 */
export function resolveNativeConfigAfterAutosave(args: {
  slideId: string;
  serverNativeConfig: Record<string, unknown> | undefined;
  completedVersion: number | undefined;
  latestVersion: number;
  pending: ComunicadoAutosavePending | null;
  liveConfig: Record<string, unknown> | null;
  selectedSlideId: string | null;
}): Record<string, unknown> | undefined {
  const { slideId, serverNativeConfig, pending, liveConfig, selectedSlideId } = args;

  if (isStaleComunicadoAutosave(args.completedVersion, args.latestVersion)) {
    if (pending?.slideId === slideId) return pending.nativeConfig;
    if (selectedSlideId === slideId && liveConfig) return liveConfig;
    return serverNativeConfig;
  }

  if (pending?.slideId === slideId && pending.version > (args.completedVersion ?? 0)) {
    return pending.nativeConfig;
  }
  if (selectedSlideId === slideId && liveConfig) {
    return liveConfig;
  }
  return serverNativeConfig;
}

/** Deve limpar draft local após save bem-sucedido? */
export function shouldClearComunicadoDraftAfterSave(args: {
  completedVersion: number | undefined;
  latestVersion: number;
}): boolean {
  return !isStaleComunicadoAutosave(args.completedVersion, args.latestVersion);
}

/** Deve zerar o pending atual após save? */
export function shouldClearComunicadoPendingAfterSave(args: {
  pending: ComunicadoAutosavePending | null;
  slideId: string;
  completedVersion: number | undefined;
}): boolean {
  const { pending, slideId, completedVersion } = args;
  if (!pending || pending.slideId !== slideId) return false;
  if (completedVersion == null) return true;
  return pending.version <= completedVersion;
}
