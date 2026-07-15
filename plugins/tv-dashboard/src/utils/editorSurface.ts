/**
 * Mantém o editor montado sob a prévia da mesma playlist para não piscar
 * «Carregando programação…» nem refetch ao Voltar.
 */
export function shouldKeepEditorUnderPreview(
  view: string,
  playlistId: string | undefined,
  editorSessionPlaylistId: string | null,
): boolean {
  if (view === "edit" && playlistId) return true;
  if (view === "preview" && playlistId && editorSessionPlaylistId === playlistId) return true;
  return false;
}

/** Atalhos do deck só na superfície de edição — não sob prévia keep-alive. */
export function isDeckEditorSurfaceActive(view: string): boolean {
  return view === "edit";
}
