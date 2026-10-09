import type { SaveState } from "../state/saveMachine";
import { BpmnmStatusBadge } from "../ui/kit";

const LABELS: Record<SaveState, string> = {
  LOADING: "Carregando…",
  CLEAN: "Salvo",
  DIRTY: "Alterações aguardando salvamento",
  SAVING: "Salvando…",
  SAVE_FAILED: "Falha ao salvar",
  OFFLINE: "Sem conexão",
  SESSION_EXPIRED: "Sessão expirada",
  CONFLICT: "Conflito de edição",
  READ_ONLY: "Somente leitura",
};

const VARIANTS: Record<SaveState, "neutral" | "success" | "warning" | "danger" | "info"> = {
  LOADING: "neutral",
  CLEAN: "success",
  DIRTY: "warning",
  SAVING: "info",
  SAVE_FAILED: "danger",
  OFFLINE: "warning",
  SESSION_EXPIRED: "danger",
  CONFLICT: "danger",
  READ_ONLY: "neutral",
};

export function SaveStatus({ state }: { state: SaveState }) {
  return (
    <span
      className={`bpmnm-save-status bpmnm-save-status--${state.toLowerCase()}`}
      role="status"
      aria-live="polite"
    >
      <BpmnmStatusBadge label={LABELS[state]} variant={VARIANTS[state]} />
    </span>
  );
}
