import {
  stripContentRunStylesOverriddenByContainer,
  typographyKeysFromContainerPatch,
  type ComunicadoBlockStyle,
  type ComunicadoContentRun,
  type ContainerTypographyStyleKey,
} from "@delpi/tv-dashboard-presentation";

/**
 * Reconcilia contentRuns de um draft de edição contra a tipografia atual do
 * container antes de um flush/upsert.
 *
 * Propriedades tipográficas presentes em `containerStyle` e NÃO marcadas como
 * edição explícita de trecho nesta sessão são removidas dos runs — evita que
 * um draftRef iniciado antes de `updateSelectedStyle` reintroduza overrides
 * stale (ex.: color branco) via `upsert_block` (replace wholesale de runs).
 *
 * Chaves em `explicitRunStyleKeys` (partial formatting) são preservadas.
 */
export function reconcileDraftContentRunsForCommit(args: {
  draftRuns: ComunicadoContentRun[] | undefined;
  containerStyle: ComunicadoBlockStyle | null | undefined;
  explicitRunStyleKeys?: ReadonlySet<ContainerTypographyStyleKey> | null;
}): ComunicadoContentRun[] | undefined {
  const { draftRuns, containerStyle, explicitRunStyleKeys } = args;
  if (!draftRuns?.length || !containerStyle) return draftRuns;

  const containerKeys = typographyKeysFromContainerPatch(
    containerStyle as Record<string, unknown>,
  );
  if (containerKeys.length === 0) return draftRuns;

  const keysToStrip = containerKeys.filter((key) => !explicitRunStyleKeys?.has(key));
  if (keysToStrip.length === 0) return draftRuns;

  return stripContentRunStylesOverriddenByContainer(draftRuns, keysToStrip);
}

/** Mapeia um patch de estilo de run para as chaves de tipografia de container. */
export function containerTypographyKeysFromRunPatch(
  patch: Record<string, unknown>,
): ContainerTypographyStyleKey[] {
  return typographyKeysFromContainerPatch(patch);
}
