export type ListSurfaceState = "loading" | "error" | "empty" | "ready";

export function resolveListSurfaceState(input: {
  loading: boolean;
  error: string | null;
  itemCount: number;
  hasLoaded: boolean;
}): ListSurfaceState {
  if (input.loading && !input.hasLoaded) return "loading";
  if (input.error) return "error";
  if (input.hasLoaded && input.itemCount === 0) return "empty";
  return "ready";
}

export type DetailSurfaceState = "idle" | "loading" | "error" | "ready";

export function resolveDetailSurfaceState(input: {
  open: boolean;
  loading: boolean;
  error: string | null;
  notFound: boolean;
  hasData: boolean;
}): DetailSurfaceState {
  if (!input.open) return "idle";
  if (input.loading) return "loading";
  if (input.notFound) return "error";
  if (input.error) return "error";
  if (input.hasData) return "ready";
  return "loading";
}

export function detailErrorMessage(error: string | null, notFound: boolean): string {
  if (notFound) return "Solicitação não encontrada ou indisponível.";
  return error || "Não foi possível carregar o detalhe.";
}
