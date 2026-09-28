/**
 * Seleção corrente do Process Workspace publicada para o TÉO context
 * bridge. Não é domain state: reflete apenas o que a UI está exibindo
 * (ex.: "Melhoria analisada"/"Cenário proposto" de Resultados).
 *
 * Guardada em módulo (não React state) para que o execute WebMCP leia o
 * valor vivo no momento da chamada — sem closure obsoleta.
 */

export type TeoWorkspaceSelection = {
  process_id: string;
  instance_id: string | null;
  revision_id: string | null;
};

let currentSelection: TeoWorkspaceSelection | null = null;
const listeners = new Set<() => void>();

export function publishTeoWorkspaceSelection(
  selection: TeoWorkspaceSelection | null,
): void {
  if (
    currentSelection?.process_id === selection?.process_id &&
    currentSelection?.instance_id === selection?.instance_id &&
    currentSelection?.revision_id === selection?.revision_id
  ) {
    return;
  }
  currentSelection = selection;
  for (const listener of listeners) listener();
}

export function readTeoWorkspaceSelection(): TeoWorkspaceSelection | null {
  return currentSelection;
}

export function subscribeTeoWorkspaceSelection(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}
