import type { SaveState } from "../state/saveMachine";

const LABELS: Record<SaveState, string> = {
  LOADING: "Carregando…",
  CLEAN: "Salvo",
  DIRTY: "Alterações não salvas",
  SAVING: "Salvando…",
  SAVE_FAILED: "Falha ao salvar",
  CONFLICT: "Conflito de versão",
  READ_ONLY: "Somente leitura",
};

export function SaveStatus({ state }: { state: SaveState }) {
  return (
    <span
      className={`bpmnm-save-status bpmnm-save-status--${state.toLowerCase()}`}
      role="status"
      aria-live="polite"
    >
      {LABELS[state]}
    </span>
  );
}
